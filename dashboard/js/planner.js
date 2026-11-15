// Planificador "què passaria si": recalcula el millor pla de 24 h al navegador amb programació dinàmica.
(function () {
  const MODE = window.MODE;
  // nivells de càrrega: 10 kWh al Mode estàndard; amb la bateria gran, 30 kWh perquè vagi igual de ràpid
  const CAP = MODE.cap_kwh, ETA = Math.sqrt(0.9), STEP = Math.max(10, CAP / 200);
  const LEVELS = CAP / STEP + 1;
  const f = (x, d = 0) => x.toLocaleString("ca-ES", { minimumFractionDigits: d, maximumFractionDigits: d });
  const $ = id => document.getElementById(id);
  const DEFAULTS = { price: 0, co2: 0, reserve: 0, power: MODE.power_kw, weight: 70 };
  let state = { ...DEFAULTS }, ctx = null;

  // millor pla: mínim de sum(w_t * p_t) recorrent els nivells de càrrega possibles
  // endLevel: el pla ha d'acabar amb almenys aquesta energia, perquè buidar la bateria al final no surt gratis
  // net: consum − solar de cada hora; si és negatiu, carregar amb l'excedent no compra res a la xarxa
  function solve(w, net, soc0, power, reserve, endKwh = 0) {
    const H = w.length, minLevel = Math.ceil(reserve * CAP / STEP);
    const reach = Math.ceil(power / ETA / STEP) + 1;   // nivells que es poden moure en una hora
    const start = Math.round(soc0 / STEP);
    const endLevel = Math.min(LEVELS - 1, Math.floor(endKwh / STEP));
    let value = new Float64Array(LEVELS).map((_, s) => (s >= endLevel ? 0 : Infinity));
    const choice = [];
    for (let t = H - 1; t >= 0; t--) {
      const next = new Float64Array(LEVELS).fill(Infinity), best = new Int16Array(LEVELS);
      for (let s = 0; s < LEVELS; s++) {
        for (let s2 = Math.max(0, s - reach); s2 <= Math.min(LEVELS - 1, s + reach); s2++) {
          if (s2 < minLevel && s2 < s) continue;           // no baixem per sota de la reserva
          const de = (s2 - s) * STEP;
          const p = de >= 0 ? de / ETA : de * ETA;           // potència vista des de la xarxa
          if (p > power || -p > Math.min(power, Math.max(0, net[t]))) continue;
          const c = w[t] * (Math.max(0, net[t] + p) - Math.max(0, net[t])) + value[s2];
          if (c < next[s]) { next[s] = c; best[s] = s2; }
        }
      }
      value = next;
      choice[t] = best;
    }
    if (!isFinite(value[start]) && endKwh > 0) return solve(w, net, soc0, power, reserve, 0);   // escenari massa estret
    const plan = [], socs = [];
    let s = start;
    for (let t = 0; t < H; t++) {
      const s2 = choice[t][s], de = (s2 - s) * STEP;
      plan.push(de >= 0 ? de / ETA : de * ETA);
      socs.push(s2 * STEP / CAP);
      s = s2;
    }
    return { plan, socs };
  }

  function evaluate(idx, plan, co2, price, H) {
    let kg = 0, eur = 0;
    idx.forEach((i, j) => {
      const grid = Math.max(0, H.load[i] - H.pv[i] + plan[j]);
      kg += (H.base[i] - grid) * co2[j];
      eur += (H.base[i] - grid) * price[j];
    });
    return { kg, eur };
  }

  function render() {
    if (!ctx) return;
    const { H, k, co2Color } = ctx;
    const idx = d3.range(k, Math.min(k + 24, H.t.length));
    const price = idx.map(i => H.price[i] * (1 + state.price / 100));
    const co2 = idx.map(i => H.co2[i] * (1 + state.co2 / 100));
    const a = state.weight / 100;
    const w = idx.map((_, j) => a * co2[j] / MODE.co2_ref + (1 - a) * price[j] / MODE.price_ref);
    const net = idx.map(i => H.load[i] - H.pv[i]);
    const soc0 = k > 0 ? H.soc[k - 1] * CAP : CAP / 2;
    const agentPlan = idx.map(i => H.bat[i]);
    const agentSocs = idx.map(i => H.soc[i]);
    let res = solve(w, net, soc0, state.power, state.reserve / 100, H.soc[idx[idx.length - 1]] * CAP);
    // si el pla de l'agent també compleix l'escenari i és igual o millor, és el que proposem
    // (el càlcul del navegador va en salts de 10 kWh i l'agent és exacte)
    const cost = plan => plan.reduce((s, p, j) => s + w[j] * (Math.max(0, net[j] + p) - Math.max(0, net[j])), 0);
    const agentOk = agentPlan.every(p => Math.abs(p) <= state.power + 1e-6) &&
                    agentSocs.every((s, j) => s * 100 >= state.reserve - 1e-6 || agentPlan[j] >= 0);
    if (agentOk && cost(agentPlan) <= cost(res.plan)) res = { plan: agentPlan, socs: agentSocs };
    const mine = evaluate(idx, res.plan, co2, price, H), agent = evaluate(idx, agentPlan, co2, price, H);

    const d = mine.kg - agent.kg;
    $("pl-kpis").innerHTML =
      `<div><b class="good">${f(mine.kg)} kg</b>CO₂ evitat amb l'escenari</div>` +
      `<div><b>${f(agent.kg)} kg</b>amb el pla actual</div>` +
      `<div><b class="good">${f(mine.eur)} €</b>estalviats amb l'escenari</div>` +
      `<div><b>${d >= 0 ? "+" : "−"}${f(Math.abs(d))} kg</b>diferència amb el pla actual</div>` +
      `<div><b>${f(Math.max(...res.socs.map(s => s * 100)) - Math.min(...res.socs.map(s => s * 100)))} %</b>de bateria fet servir</div>`;

    // gràfic: pla nou (color) i pla de l'agent (contorn), i càrrega de la bateria
    const el = $("c-planner"), W = el.clientWidth, Ht = 300, m = { t: 14, r: 44, b: 26, l: 44 };
    const iw = W - m.l - m.r, ih = Ht - m.t - m.b;
    el.innerHTML = "";
    const svg = d3.select(el).append("svg").attr("viewBox", `0 0 ${W} ${Ht}`).attr("width", "100%");
    const g = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);
    const x = d3.scaleBand().domain(d3.range(idx.length)).range([0, iw]).padding(0.2);
    const y = d3.scaleLinear().domain([-MODE.power_kw, MODE.power_kw]).range([ih * 0.62, 0]);
    const ys = d3.scaleLinear().domain([0, 100]).range([ih, ih * 0.7]);
    g.selectAll("rect.c").data(idx).join("rect").attr("x", (_, j) => x(j)).attr("y", -10).attr("width", x.bandwidth())
      .attr("height", 6).attr("rx", 3).attr("fill", (_, j) => co2Color(co2[j]));
    g.selectAll("rect.p").data(res.plan).join("rect").attr("x", (_, j) => x(j)).attr("width", x.bandwidth()).attr("rx", 3)
      .attr("y", p => y(Math.max(0, p))).attr("height", p => Math.abs(y(p) - y(0)))
      .attr("fill", p => (p > 0 ? "#0072B2" : "#D55E00"));
    g.selectAll("rect.a").data(agentPlan).join("rect").attr("x", (_, j) => x(j) + 1).attr("width", x.bandwidth() - 2).attr("rx", 3)
      .attr("y", p => y(Math.max(0, p))).attr("height", p => Math.abs(y(p) - y(0)))
      .attr("fill", "none").attr("stroke", "#1F2326").attr("stroke-width", 1.2).attr("stroke-dasharray", "3 2");
    g.append("line").attr("x1", 0).attr("x2", iw).attr("y1", y(0)).attr("y2", y(0)).attr("stroke", "#E6E2DA");
    if (state.reserve > 0) g.append("line").attr("x1", 0).attr("x2", iw).attr("y1", ys(state.reserve)).attr("y2", ys(state.reserve))
      .attr("stroke", "#D55E00").attr("stroke-dasharray", "4 3");
    const line = arr => d3.line().x((_, j) => x(j) + x.bandwidth() / 2).y(v => ys(v * 100)).curve(d3.curveMonotoneX)(arr);
    g.append("path").attr("d", line(agentPlan.map((_, j) => H.soc[idx[j]]))).attr("fill", "none").attr("stroke", "#A19C93").attr("stroke-width", 2).attr("stroke-dasharray", "4 3");
    g.append("path").attr("d", line(res.socs)).attr("fill", "none").attr("stroke", "#47908B").attr("stroke-width", 2.5);
    g.append("g").attr("class", "axis").call(d3.axisLeft(y).ticks(4).tickSize(0).tickPadding(6)).call(s => s.select(".domain").remove());
    g.append("g").attr("class", "axis").call(d3.axisLeft(ys).ticks(2).tickFormat(v => v + " %").tickSize(0).tickPadding(6)).call(s => s.select(".domain").remove());
    g.append("g").attr("class", "axis").attr("transform", `translate(0,${ih})`)
      .call(d3.axisBottom(x).tickValues(d3.range(0, idx.length, 3)).tickFormat(j => H.t[idx[j]].slice(11, 13) + " h").tickSize(0).tickPadding(6))
      .call(s => s.select(".domain").remove());
    g.append("text").attr("x", iw + 6).attr("y", y(MODE.power_kw / 2)).style("font-size", "10px").text("kW");
    g.append("text").attr("x", iw + 6).attr("y", ys(60)).style("font-size", "10px").text("càrrega");
  }

  function bind() {
    const set = (id, key, fmt) => {
      const el = $(id);
      el.value = state[key];
      const out = () => { $(id + "-v").textContent = fmt(state[key]); };
      el.oninput = () => { state[key] = +el.value; out(); render(); };
      out();
    };
    const sign = v => (v > 0 ? "+" : "") + v + " %";
    set("pl-price", "price", sign);
    set("pl-co2", "co2", sign);
    set("pl-reserve", "reserve", v => v + " %");
    // el límit de l'inversor depèn del mode (500 o 1.500 kW)
    $("pl-power").max = MODE.power_kw;
    $("pl-step").textContent = STEP;
    $("pl-power").step = MODE.power_kw / 10;
    set("pl-power", "power", v => v + " kW");
    set("pl-weight", "weight", v => `${v} % CO₂, ${100 - v} % preu`);
    $("pl-reset").onclick = () => { state = { ...DEFAULTS }; bind(); render(); };
  }

  window.Planner = {
    init() { bind(); },
    update(c) { ctx = c; if (document.getElementById("v-planner").classList.contains("on")) render(); },
    render,
    solve,
  };
})();
