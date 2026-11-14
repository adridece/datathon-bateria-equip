// Gràfics del tauler (D3). Tots fan servir els mateixos colors i s'animen en entrar.
(function () {
  const C = { text: "#1F2326", muted: "#6E6A63", dim: "#A19C93", line: "#E6E2DA", soft: "#F0EDE7",
              accent: "#0F7A62", ref: "#CFC9BD", charge: "#0072B2", discharge: "#D55E00", price: "#7A5195", co2: "#A9824F" };
  const f = (x, d = 0) => x.toLocaleString("ca-ES", { minimumFractionDigits: d, maximumFractionDigits: d });
  const eur = x => (Math.abs(x) >= 10000 ? f(x / 1000) + " k€" : f(x) + " €");
  const $ = id => document.getElementById(id);
  const T = 700, ease = d3.easeCubicOut;
  let D;

  function frame(id, h, m = { t: 12, r: 16, b: 28, l: 44 }) {
    const el = $(id), w = el.clientWidth;
    el.innerHTML = "";
    const s = d3.select(el).append("svg").attr("viewBox", `0 0 ${w} ${h}`).attr("width", "100%");
    return { s, w, iw: w - m.l - m.r, ih: h - m.t - m.b, g: s.append("g").attr("transform", `translate(${m.l},${m.t})`) };
  }
  const gridY = (g, y, iw, ticks = 4, fmt = null) => {
    g.append("g").attr("class", "grid").call(d3.axisLeft(y).ticks(ticks).tickSize(-iw).tickFormat("")).call(a => a.select(".domain").remove());
    g.append("g").attr("class", "axis").call(d3.axisLeft(y).ticks(ticks).tickSize(0).tickPadding(8).tickFormat(fmt))
      .call(a => a.select(".domain").remove());
  };
  const axisX = (g, x, ih, a) => g.append("g").attr("class", "axis").attr("transform", `translate(0,${ih})`)
    .call(a(x)).call(s => s.select(".domain").attr("stroke", C.line)).call(s => s.selectAll("line").remove());
  let counted = false;
  function count(el, to, fmt) {
    el.textContent = fmt(to);   // el valor real sempre hi és, encara que l'animació s'interrompi
    if (counted || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    d3.select(el).transition().duration(900).ease(ease)
      .tween("text", () => { const i = d3.interpolateNumber(0, to); return t => { el.textContent = fmt(i(t)); }; })
      .on("interrupt end", () => { el.textContent = fmt(to); });
    // si el navegador frena l'animació (pestanya en segon pla), la xifra queda igualment bé
    setTimeout(() => { el.textContent = fmt(to); }, 1200);
  }

  // ---------------------------------------------------------------- KPI
  function kpis() {
    const y = D.yearly, o = D.official, st = D.strategies;
    const cards = [
      { cls: "hero", label: "CO₂ evitat per any (estimació)", v: y.co2_t_year, fmt: v => f(v) + " t", delta: `−${f(y.co2_pct, 1)} % d'emissions` },
      { cls: "", label: "Estalvi a la factura per any (estimació)", v: y.eur_year, fmt: v => eur(v), delta: `−${f(y.cost_pct, 1)} % de cost` },
      { cls: "", label: "Puntuació oficial (test ocult)", v: o.score, fmt: v => f(v, 2), delta: `al màxim teòric (validació: ${f(st[2].score, 2)} de ${f(st[3].score, 2)})`, n: true },
      { cls: "", label: "Infraccions físiques", v: o.violations, fmt: v => f(v), delta: "en 2.016 h de test", n: true },
    ];
    $("kpis").innerHTML = cards.map((c, i) => `<div class="card kpi s3 ${c.cls}"><div class="label">${c.label}</div>` +
      `<div class="value" id="kv${i}">0</div><span class="delta ${c.n ? "neutral" : ""}">${c.delta}</span>${i < 2 ? `<svg id="ks${i}" width="96" height="34"></svg>` : ""}</div>`).join("");
    cards.forEach((c, i) => count($("kv" + i), c.v, c.fmt));
    counted = true;
    // sparkline: estalvi per setmana (CO2 i €)
    const m = D.monthly;
    [["co2_pct"], ["cost_pct"]].forEach(([key], i) => {
      const svg = d3.select("#ks" + i), x = d3.scaleLinear().domain([0, m.length - 1]).range([2, 94]);
      const yy = d3.scaleLinear().domain([0, d3.max(m, d => d[key])]).range([32, 4]);
      const p = svg.append("path").datum(m).attr("fill", "none").attr("stroke", i ? C.dim : C.accent).attr("stroke-width", 2)
        .attr("stroke-linecap", "round").attr("d", d3.line().x((_, j) => x(j)).y(d => yy(d[key])).curve(d3.curveMonotoneX));
      const L = p.node().getTotalLength();
      p.attr("stroke-dasharray", L).attr("stroke-dashoffset", L).transition().duration(1100).ease(ease).attr("stroke-dashoffset", 0);
    });
  }

  // ---------------------------------------------------------------- estratègies
  function strategyBars(id, h) {
    const st = D.strategies, rows = st.slice(0, 3);
    const { g, iw, ih } = frame(id, h, { t: 22, r: 50, b: 26, l: 170 });
    const x = d3.scaleLinear().domain([0, 7]).range([0, iw]);
    const y = d3.scaleBand().domain(rows.map(r => r.strategy)).range([0, ih]).padding(0.35);
    axisX(g, x, ih, s => d3.axisBottom(s).ticks(7));
    g.selectAll("text.n").data(rows).join("text").attr("x", -12).attr("y", r => y(r.strategy) + y.bandwidth() / 2 + 4)
      .attr("text-anchor", "end").style("font-size", "12.5px").style("fill", r => (r.strategy.startsWith("MPC") ? C.text : C.muted)).text(r => r.strategy);
    g.selectAll("rect").data(rows).join("rect").attr("y", r => y(r.strategy)).attr("height", y.bandwidth()).attr("rx", y.bandwidth() / 2)
      .attr("fill", r => (r.strategy.startsWith("MPC") ? C.accent : C.ref)).attr("width", 0)
      .transition().duration(T).ease(ease).delay((_, i) => i * 90).attr("width", r => (r.score < 0.01 ? 0 : Math.max(y.bandwidth(), x(r.score))));
    g.selectAll("text.v").data(rows).join("text").attr("class", "lab").attr("x", r => Math.max(y.bandwidth(), x(r.score)) + 8)
      .attr("y", r => y(r.strategy) + y.bandwidth() / 2 + 4).text(r => f(r.score, 2)).style("opacity", 0)
      .transition().delay(T).style("opacity", 1);
    const ox = x(st[3].score);
    g.append("line").attr("x1", ox).attr("x2", ox).attr("y1", -10).attr("y2", ih).attr("stroke", C.text).attr("stroke-dasharray", "3 4");
    g.append("text").attr("x", ox).attr("y", -12).attr("text-anchor", "middle").text("òptim teòric " + f(st[3].score, 2));
  }

  // ---------------------------------------------------------------- perfil horari
  function profile(id, compact) {
    const p = D.profile;
    const panels = compact
      ? [{ key: "battery_kw", title: "Bateria (kW)", h: 130, bars: true }, { key: "co2_g", title: "CO₂ (g/kWh)", h: 60, color: C.co2 }]
      : [{ key: "battery_kw", title: "Bateria (kW)", h: 140, bars: true }, { key: "co2_g", title: "CO₂ xarxa (g/kWh)", h: 70, color: C.co2 },
         { key: "price_eur_mwh", title: "Preu (€/MWh)", h: 70, color: C.price }];
    const total = d3.sum(panels, p => p.h + 22) + 28;
    const { g, iw } = frame(id, total, { t: 8, r: 90, b: 0, l: 44 });
    const x = d3.scaleBand().domain(d3.range(24)).range([0, iw]).padding(0.22);
    let y0 = 0;
    panels.forEach(pn => {
      const gg = g.append("g").attr("transform", `translate(0,${y0})`);
      const ext = d3.extent(p, r => r[pn.key]);
      const y = pn.bars ? d3.scaleLinear().domain([-500, 500]).range([pn.h, 0]) : d3.scaleLinear().domain([ext[0] * 0.92, ext[1] * 1.05]).range([pn.h, 0]);
      gridY(gg, y, iw, pn.bars ? 4 : 2);
      gg.append("text").attr("x", iw + 10).attr("y", 12).text(pn.title);
      if (pn.bars) {
        gg.selectAll("rect").data(p).join("rect").attr("x", r => x(r.hour)).attr("width", x.bandwidth()).attr("rx", 3)
          .attr("fill", r => (r.battery_kw > 0 ? C.charge : C.discharge)).attr("y", y(0)).attr("height", 0)
          .transition().duration(T).ease(ease).delay((_, i) => i * 18)
          .attr("y", r => y(Math.max(0, r.battery_kw))).attr("height", r => Math.abs(y(r.battery_kw) - y(0)));
      } else {
        const path = gg.append("path").datum(p).attr("fill", "none").attr("stroke", pn.color).attr("stroke-width", 2.2).attr("stroke-linecap", "round")
          .attr("d", d3.line().x(r => x(r.hour) + x.bandwidth() / 2).y(r => y(r[pn.key])).curve(d3.curveMonotoneX));
        const L = path.node().getTotalLength();
        path.attr("stroke-dasharray", L).attr("stroke-dashoffset", L).transition().duration(1000).ease(ease).attr("stroke-dashoffset", 0);
      }
      y0 += pn.h + 22;
    });
    axisX(g, x, y0 - 18, s => d3.axisBottom(s).tickValues(d3.range(0, 24, 3)).tickFormat(h => h + " h"));
  }

  // ---------------------------------------------------------------- mapa de calor
  function heat() {
    const H = D.hours, n = H.t.length, days = d3.range(0, n, 24);
    const { g, iw, ih } = frame("c-heat", 250, { t: 4, r: 12, b: 26, l: 48 });
    // un dia per columna, una hora per fila: així cap a l'amplada
    const x = d3.scaleBand().domain(days).range([0, iw]).paddingInner(0.08);
    const y = d3.scaleBand().domain(d3.range(24)).range([0, ih]).paddingInner(0.08);
    const col = d3.scaleLinear().domain([-500, 0, 500]).range([C.discharge, "#F3F0EA", C.charge]);
    const cells = [];
    days.forEach(d0 => { for (let h = 0; h < 24 && d0 + h < n; h++) cells.push([d0, h, H.bat[d0 + h]]); });
    g.selectAll("rect").data(cells).join("rect").attr("x", c => x(c[0])).attr("y", c => y(c[1])).attr("rx", 2)
      .attr("width", x.bandwidth()).attr("height", y.bandwidth()).attr("fill", "#F3F0EA")
      .transition().duration(500).delay(c => c[0] / 24 * 8).attr("fill", c => col(c[2]));
    g.append("g").attr("class", "axis").call(d3.axisLeft(y).tickValues([0, 6, 12, 18, 23]).tickFormat(h => h + " h").tickSize(0).tickPadding(8))
      .call(a => a.select(".domain").remove());
    D.weeks.forEach(w => g.append("text").attr("x", x(Math.floor(w.start / 24) * 24)).attr("y", ih + 18).text(w.label.slice(0, 5)));
  }

  // ---------------------------------------------------------------- mida de la bateria
  const size = { cap: 2000, pow: 500, cost: 350 };
  function sizingSetup() {
    const caps = [...new Set(D.sizing.map(r => r.capacity_kwh))], pows = [...new Set(D.sizing.map(r => r.power_kw))];
    const seg = (id, vals, key) => {
      $(id).innerHTML = vals.map(v => `<button data-v="${v}">${v >= 1000 ? f(v / 1000, v % 1000 ? 1 : 0) + "k" : f(v)}</button>`).join("");
      $(id).querySelectorAll("button").forEach(b => (b.onclick = () => { size[key] = +b.dataset.v; sizing(); }));
    };
    seg("b-cap", caps, "cap");
    seg("b-pow", pows, "pow");
    $("cost").oninput = e => { size.cost = +e.target.value; sizing(true); };
  }
  function sizing(quick) {
    ["b-cap", "b-pow"].forEach((id, j) => $(id).querySelectorAll("button").forEach(b => b.classList.toggle("on", +b.dataset.v === (j ? size.pow : size.cap))));
    $("cost-v").textContent = f(size.cost);
    const rows = D.sizing.map(r => ({ ...r, invest: r.capacity_kwh * size.cost, payback: (r.capacity_kwh * size.cost) / r.eur_year }));
    const cur = rows.find(r => r.capacity_kwh === size.cap && r.power_kw === size.pow);
    const base = rows.find(r => r.capacity_kwh === 2000 && r.power_kw === 500);
    const ok = rows.filter(r => r.power_kw === size.pow && r.payback < 10);
    const best = ok.length ? ok.reduce((a, b) => (b.co2_t_year > a.co2_t_year ? b : a)) : null;
    let txt = `Amb <b>${f(size.cap)} kWh i ${f(size.pow)} kW</b> s'evitarien <b>${f(cur.co2_t_year)} t de CO₂</b> i ${eur(cur.eur_year)} l'any`;
    if (size.cap !== 2000 || size.pow !== 500) {
      const dlt = cur.co2_t_year - base.co2_t_year;
      txt += ` (${dlt >= 0 ? "+" : "−"}${f(Math.abs(dlt))} t respecte a la bateria del repte)`;
    }
    txt += `, i la inversió es recuperaria en ${f(cur.payback, 1)} anys.`;
    if (best) txt += ` Amb ${f(size.pow)} kW, l'opció que evita més CO₂ i es recupera en menys de 10 anys és <b>${f(best.capacity_kwh)} kWh</b>.`;
    $("a-size").innerHTML = txt;
    $("size-kpis").innerHTML = `<span class="k">CO₂ evitat</span><span class="v">${f(cur.co2_t_year)} t/any</span>` +
      `<span class="k">Estalvi</span><span class="v">${eur(cur.eur_year)}/any</span><span class="k">Inversió</span><span class="v">${eur(cur.invest)}</span>` +
      `<span class="k">Retorn</span><span class="v">${f(cur.payback, 1)} anys</span>`;

    const caps = [...new Set(D.sizing.map(r => r.capacity_kwh))], pows = [...new Set(D.sizing.map(r => r.power_kw))];
    const { g, iw, ih } = frame("c-size", 290, { t: 14, r: 64, b: 30, l: 44 });
    const x = d3.scaleLinear().domain([0, d3.max(caps)]).range([0, iw]);
    const y = d3.scaleLinear().domain([0, d3.max(rows, r => r.co2_t_year) * 1.1]).range([ih, 0]);
    gridY(g, y, iw, 5);
    axisX(g, x, ih, s => d3.axisBottom(s).ticks(8).tickFormat(v => f(v)));
    g.append("text").attr("x", iw).attr("y", ih + 26).attr("text-anchor", "end").text("kWh");
    pows.forEach(p => {
      const pr = rows.filter(r => r.power_kw === p), on = p === size.pow;
      const path = g.append("path").datum(pr).attr("fill", "none").attr("stroke", on ? C.accent : C.ref).attr("stroke-width", on ? 3 : 2)
        .attr("stroke-linecap", "round").attr("d", d3.line().x(r => x(r.capacity_kwh)).y(r => y(r.co2_t_year)).curve(d3.curveMonotoneX));
      if (!quick && on) {
        const L = path.node().getTotalLength();
        path.attr("stroke-dasharray", L).attr("stroke-dashoffset", L).transition().duration(900).ease(ease).attr("stroke-dashoffset", 0);
      }
      g.selectAll(null).data(pr).join("circle").attr("cx", r => x(r.capacity_kwh)).attr("cy", r => y(r.co2_t_year)).attr("r", on ? 4 : 3)
        .attr("fill", "#fff").attr("stroke", on ? C.accent : C.ref).attr("stroke-width", 2);
      const l = pr[pr.length - 1];
      g.append("text").attr("x", x(l.capacity_kwh) + 10).attr("y", y(l.co2_t_year) + 4).style("fill", on ? C.accent : C.muted).text(f(p) + " kW");
    });
    g.append("circle").attr("cx", x(cur.capacity_kwh)).attr("cy", y(cur.co2_t_year)).attr("r", 11).attr("fill", "none")
      .attr("stroke", C.text).attr("stroke-width", 1.5);

    $("t-size").innerHTML = "<tr><th>Capacitat</th><th>CO₂ evitat</th><th>Estalvi</th><th>Inversió</th><th>Retorn</th><th>€ per t CO₂ (15 anys)</th></tr>" +
      rows.filter(r => r.power_kw === size.pow).map(r => `<tr class="${r.capacity_kwh === size.cap ? "sel" : ""}"><td>${f(r.capacity_kwh)} kWh</td>` +
        `<td>${f(r.co2_t_year)} t/any</td><td>${eur(r.eur_year)}/any</td><td>${eur(r.invest)}</td><td>${f(r.payback, 1)} anys</td>` +
        `<td>${f(r.invest / (r.co2_t_year * 15))} €</td></tr>`).join("");
  }

  // ---------------------------------------------------------------- fiabilitat
  function robust() {
    const r = D.robustness, m = D.monthly;
    $("a-robust").innerHTML = `Sí. Amb un <b>50 % d'error</b> a les previsions de preu i CO₂, la puntuació només baixa de ${f(r[0].score, 2)} ` +
      `a ${f(r[r.length - 1].score, 2)}, i estalvia CO₂ <b>totes les setmanes</b> (entre un ${f(d3.min(m, d => d.co2_pct), 1)} % i un ` +
      `${f(d3.max(m, d => d.co2_pct), 1)} %). Al test oficial, amb dades que no havia vist mai, en treu <b>${f(D.official.score, 2)}</b>.`;
    let { g, iw, ih } = frame("c-robust", 250, { t: 22, r: 20, b: 30, l: 40 });
    const x = d3.scaleLinear().domain([0, 50]).range([0, iw]);
    const y = d3.scaleLinear().domain([0, 7]).range([ih, 0]);
    gridY(g, y, iw, 4);
    axisX(g, x, ih, s => d3.axisBottom(s).ticks(5).tickFormat(v => v + " %"));
    g.append("path").datum(r).attr("fill", C.accent).attr("opacity", 0.08)
      .attr("d", d3.area().x(d => x(d.error_pct)).y0(ih).y1(d => y(d.score)).curve(d3.curveMonotoneX));
    const path = g.append("path").datum(r).attr("fill", "none").attr("stroke", C.accent).attr("stroke-width", 3).attr("stroke-linecap", "round")
      .attr("d", d3.line().x(d => x(d.error_pct)).y(d => y(d.score)).curve(d3.curveMonotoneX));
    const L = path.node().getTotalLength();
    path.attr("stroke-dasharray", L).attr("stroke-dashoffset", L).transition().duration(1000).ease(ease).attr("stroke-dashoffset", 0);
    g.selectAll("circle").data(r).join("circle").attr("cx", d => x(d.error_pct)).attr("cy", d => y(d.score)).attr("r", 4.5)
      .attr("fill", "#fff").attr("stroke", C.accent).attr("stroke-width", 2);
    g.selectAll("text.lab").data(r).join("text").attr("class", "lab").attr("x", d => x(d.error_pct)).attr("y", d => y(d.score) - 12)
      .attr("text-anchor", "middle").text(d => f(d.score, 2));

    ({ g, iw, ih } = frame("c-month", 250, { t: 12, r: 12, b: 30, l: 40 }));
    const xm = d3.scaleBand().domain(m.map(d => d.month)).range([0, iw]).padding(0.3);
    const xi = d3.scaleBand().domain(["co2_pct", "cost_pct"]).range([0, xm.bandwidth()]).padding(0.12);
    const ym = d3.scaleLinear().domain([0, d3.max(m, d => Math.max(d.co2_pct, d.cost_pct)) * 1.1]).range([ih, 0]);
    gridY(g, ym, iw, 4, v => v + " %");
    axisX(g, xm, ih, s => d3.axisBottom(s));
    m.forEach((d, i) => ["co2_pct", "cost_pct"].forEach(key => g.append("rect").attr("x", xm(d.month) + xi(key)).attr("width", xi.bandwidth())
      .attr("rx", Math.min(4, xi.bandwidth() / 2)).attr("fill", key === "co2_pct" ? C.accent : C.ref).attr("y", ih).attr("height", 0)
      .transition().duration(T).ease(ease).delay(i * 40).attr("y", ym(d[key])).attr("height", ih - ym(d[key]))));
  }

  // ---------------------------------------------------------------- respostes de text
  function answers() {
    const st = D.strategies, p = D.profile;
    const top = [...p].sort((a, b) => b.battery_kw - a.battery_kw).slice(0, 3).map(r => r.hour).sort((a, b) => a - b);
    const bot = [...p].sort((a, b) => a.battery_kw - b.battery_kw).slice(0, 3).map(r => r.hour).sort((a, b) => a - b);
    $("a-strategy").innerHTML = `Control predictiu amb <b>programació lineal</b>: cada hora planifica les properes 24 h amb el preu i el CO₂ coneguts ` +
      `i aplica només la primera decisió. Treu <b>${f(st[2].score, 2)}</b> punts, el mateix que un agent que conegués tot el futur; ` +
      `les regles fixes per hores en treuen ${f(st[1].score, 2)}. Carrega sobretot a les ${top.join(", ")} h i descarrega a les ${bot.join(", ")} h.`;
  }

  // ---------------------------------------------------------------- API
  const drawn = {};
  const draw = {
    overview: () => { kpis(); profile("c-mini-profile", true); strategyBars("c-mini-strategy", 190); },
    strategy: () => { strategyBars("c-strategy", 200); profile("c-profile", false); heat(); },
    sizing: () => sizing(),
    trust: () => robust(),
    live: () => {},
  };
  let current = "overview";
  window.Charts = {
    init(data) { D = data; answers(); sizingSetup(); },
    show(view) {
      current = view;
      // es redibuixen en entrar, perquè l'animació es vegi i la mida sigui la bona
      setTimeout(() => draw[view](), 30);
      drawn[view] = true;
    },
  };
  let t;
  addEventListener("resize", () => { clearTimeout(t); t = setTimeout(() => draw[current](), 200); });
})();
