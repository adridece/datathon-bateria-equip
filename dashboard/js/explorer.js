// Explorador de dades: totes les hores de les setmanes, per analitzar l'historic, i el grafic en directe del 3D.
(function () {
  const f = (x, d = 0) => x.toLocaleString("ca-ES", { minimumFractionDigits: d, maximumFractionDigits: d });
  const $ = id => document.getElementById(id);
  const statsHTML = items => items.map(([label, value]) => `<div><span>${label}</span><b class="num">${value}</b></div>`).join("");
  let D, H, n, now = 0, SIM, nSim;

  // series que es poden veure; "sum" vol dir que al passar a dies se sumen (la resta es fa la mitjana)
  const SIM_SERIES = {
    grid: { name: "Compra a la xarxa", unit: "kW", color: "#1F2326", get: i => H.grid[i] },
    base: { name: "Compra sense bateria", unit: "kW", color: "#A19C93", dash: "4 3", get: i => H.base[i] },
    load: { name: "Consum del campus", unit: "kW", color: "#3E4A56", get: i => H.load[i] },
    pv: { name: "Solar", unit: "kW", color: "#E69F00", get: i => H.pv[i] },
    bat: { name: "Bateria (+ carrega, − descarrega)", unit: "kW bateria", color: "#0072B2", get: i => H.bat[i], bars: true },
    soc: { name: "Càrrega de la bateria", unit: "%", color: "#47908B", get: i => 100 * H.soc[i] },
    co2: { name: "CO₂ de la xarxa", unit: "g/kWh", color: "#A9824F", get: i => 1000 * H.co2[i] },
    price: { name: "Preu", unit: "€/MWh", color: "#7A5195", get: i => 1000 * H.price[i] },
    savedco2: { name: "CO₂ evitat", unit: "kg", color: "#47908B", get: i => (H.base[i] - H.grid[i]) * H.co2[i], sum: true, bars: true },
    savedeur: { name: "Estalvi", unit: "€", color: "#7A5195", get: i => (H.base[i] - H.grid[i]) * H.price[i], sum: true, bars: true },
  };
  // les dades amb que s'ha fet el model (tot el train): les mateixes variables que veu el control
  const TRAIN_SERIES = {
    load: { name: "Consum del campus", unit: "kW", color: "#3E4A56", get: i => H.load[i] },
    pv: { name: "Solar", unit: "kW", color: "#E69F00", get: i => H.pv[i] },
    net: { name: "Consum net (consum − solar)", unit: "kW", color: "#1F2326", dash: "4 3", get: i => H.load[i] - H.pv[i] },
    co2: { name: "CO₂ de la xarxa", unit: "g/kWh", color: "#A9824F", get: i => 1000 * H.co2[i] },
    price: { name: "Preu", unit: "€/MWh", color: "#7A5195", get: i => 1000 * H.price[i] },
    irr: { name: "Irradiància", unit: "W/m²", color: "#C9A227", get: i => H.irr[i] },
    temp: { name: "Temperatura", unit: "°C", color: "#0072B2", get: i => H.temp[i] },
  };
  let SERIES = SIM_SERIES, blocks = [];
  const ex = { ds: "sim", keys: ["grid", "base", "co2", "savedco2"], res: "d", range: null };   // per dies es llegeix millor el periode sencer
  const DEFAULT_KEYS = { sim: ["grid", "base", "co2", "savedco2"], train: ["load", "pv", "co2"] };

  // trams continus de les dades (setmanes de simulacio o trossos del train)
  function findBlocks() {
    if (ex.ds === "sim") return D.weeks.map(w => ({ start: w.start, label: w.label.slice(0, 5) }));
    const out = [{ start: 0 }];
    for (let i = 1; i < n; i++) if (new Date(H.t[i].replace(" ", "T")) - new Date(H.t[i - 1].replace(" ", "T")) > 2 * 3600e3) out.push({ start: i });
    return out.map(b => ({ ...b, label: `${H.t[b.start].slice(8, 10)}/${H.t[b.start].slice(5, 7)}` }));
  }
  function useDataset(ds) {
    ex.ds = ds; ex.range = null; ex.keys = DEFAULT_KEYS[ds];
    H = ds === "sim" ? SIM : D.train; n = H.t.length; SERIES = ds === "sim" ? SIM_SERIES : TRAIN_SERIES;
    blocks = findBlocks();
    document.querySelectorAll("[data-ds]").forEach(x => x.classList.toggle("on", x.dataset.ds === ds));
    chips(); drawExplorer();
  }

  // punts d'una serie: per hores o sumats/mitjana per dies
  function points(key, lo, hi, res) {
    const s = SERIES[key];
    if (res === "h") return d3.range(lo, hi).map(i => [i, s.get(i)]);
    const out = [];
    for (let d0 = lo - (lo % 24); d0 < hi; d0 += 24) {
      const idx = d3.range(Math.max(d0, lo), Math.min(d0 + 24, hi));
      if (idx.length) out.push([d0, s.sum ? d3.sum(idx, s.get) : d3.mean(idx, s.get)]);
    }
    return out;
  }
  const label = i => `${H.t[i].slice(8, 10)}/${H.t[i].slice(5, 7)}`;

  // ------------------------------------------------------------ explorador (Historic)
  function drawExplorer() {
    const el = $("ex-chart");
    if (!el || !el.clientWidth) return;
    const [lo, hi] = ex.range || [0, n];
    const units = [...new Set(ex.keys.map(k => SERIES[k].unit))];
    const rowH = 96, gap = 18, ctxH = 46, m = { t: 6, r: 16, b: 22, l: 64 };
    const w = el.clientWidth, h = m.t + units.length * (rowH + gap) + ctxH + 28 + m.b;
    el.innerHTML = "";
    const svg = d3.select(el).append("svg").attr("viewBox", `0 0 ${w} ${h}`).attr("width", "100%");
    const iw = w - m.l - m.r, g = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);
    const x = d3.scaleLinear().domain([lo, hi - 1]).range([0, iw]);
    const res = ex.res;
    // una fila per unitat: les series amb la mateixa unitat es comparen al mateix eix
    units.forEach((u, r) => {
      const gg = g.append("g").attr("transform", `translate(0,${r * (rowH + gap)})`);
      const keys = ex.keys.filter(k => SERIES[k].unit === u);
      const all = keys.flatMap(k => points(k, lo, hi, res).map(p => p[1]));
      const y = d3.scaleLinear().domain(d3.extent([0, ...all])).nice().range([rowH, 0]);
      gg.append("g").attr("class", "grid").call(d3.axisLeft(y).ticks(3).tickSize(-iw).tickFormat("")).call(a => a.select(".domain").remove());
      gg.append("g").attr("class", "axis").call(d3.axisLeft(y).ticks(3).tickSize(0).tickPadding(6).tickFormat(v => f(v))).call(a => a.select(".domain").remove());
      gg.append("text").attr("class", "ex-unit").attr("x", -m.l + 2).attr("y", -1).text(u);
      keys.forEach(k => {
        const s = SERIES[k], pts = points(k, lo, hi, res);
        if (s.bars) {
          const bw = Math.max(1, iw / pts.length * 0.8);
          gg.selectAll(null).data(pts).join("rect").attr("x", p => x(p[0])).attr("width", bw)
            .attr("y", p => y(Math.max(0, p[1]))).attr("height", p => Math.abs(y(p[1]) - y(0)))
            .attr("fill", p => (k === "bat" ? (p[1] >= 0 ? "#0072B2" : "#D55E00") : s.color)).attr("opacity", 0.85);
        } else {
          gg.append("path").datum(pts).attr("fill", "none").attr("stroke", s.color).attr("stroke-width", 1.5)
            .attr("stroke-dasharray", s.dash || null).attr("d", d3.line().x(p => x(p[0])).y(p => y(p[1])));
        }
      });
    });
    const top = units.length * (rowH + gap);
    // separacio entre setmanes (no son seguides al calendari)
    blocks.filter(wk => wk.start > lo && wk.start < hi).forEach(wk => g.append("line").attr("class", "ex-week")
      .attr("x1", x(wk.start)).attr("x2", x(wk.start)).attr("y1", 0).attr("y2", top - gap));
    const ticks = res === "d" ? d3.range(lo - (lo % 24), hi, 24) : d3.range(lo, hi).filter(i => +H.t[i].slice(11, 13) === 0);
    const every = Math.max(1, Math.ceil(ticks.length / 12));
    g.append("g").attr("class", "axis").attr("transform", `translate(0,${top - gap + 4})`)
      .call(d3.axisBottom(x).tickValues(ticks.filter((_, j) => j % every === 0)).tickFormat(label).tickSize(0).tickPadding(6))
      .call(a => a.select(".domain").remove());
    // linia d'"ara" (l'hora que es veu al 3D)
    if (ex.ds === "sim" && now >= lo && now < hi) g.append("line").attr("class", "ex-now").attr("x1", x(now)).attr("x2", x(now)).attr("y1", 0).attr("y2", top - gap);
    // capa per passar el ratoli i clicar (obre aquella hora al 3D)
    const rule = g.append("line").attr("class", "ex-rule").attr("y1", 0).attr("y2", top - gap).style("opacity", 0);
    g.append("rect").attr("width", iw).attr("height", top - gap).attr("fill", "transparent").style("cursor", "pointer")
      .on("mousemove", ev => {
        const i = Math.max(lo, Math.min(hi - 1, Math.round(x.invert(d3.pointer(ev)[0]))));
        const j = res === "d" ? i - (i % 24) : i;
        rule.attr("x1", x(j)).attr("x2", x(j)).style("opacity", 1);
        const tip = $("tip");
        tip.innerHTML = `<b>${res === "d" ? label(j) : label(j) + ", " + H.t[j].slice(11, 13) + " h"}</b><br>` +
          ex.keys.map(k => { const p = points(k, j, Math.min(j + (res === "d" ? 24 : 1), n), res)[0]; return `${SERIES[k].name}: ${f(p ? p[1] : 0)} ${SERIES[k].unit.replace(" bateria", "")}`; }).join("<br>") +
          (ex.ds === "sim" ? `<br><span style="opacity:.7">Clic per veure-ho al 3D</span>` : "");
        tip.style.display = "block"; tip.style.left = Math.min(ev.clientX + 14, innerWidth - 300) + "px"; tip.style.top = ev.clientY + 14 + "px";
      })
      .on("mouseleave", () => { rule.style("opacity", 0); $("tip").style.display = "none"; })
      .on("click", ev => {
        if (ex.ds !== "sim") return;
        const i = Math.max(lo, Math.min(hi - 1, Math.round(x.invert(d3.pointer(ev)[0]))));
        $("tip").style.display = "none";
        document.dispatchEvent(new CustomEvent("explorer:goto", { detail: i }));
      });
    // franja de context: tot el periode, arrossegar per triar el tros que es mira
    const cg = g.append("g").attr("transform", `translate(0,${top + 22})`);
    const cx = d3.scaleLinear().domain([0, n - 1]).range([0, iw]);
    const cy = d3.scaleLinear().domain(d3.extent(H.co2)).range([ctxH, 0]);
    cg.append("path").datum(d3.range(n)).attr("fill", "#EEEAE3").attr("stroke", "#C9C3B8")
      .attr("d", d3.area().x(i => cx(i)).y0(ctxH).y1(i => cy(H.co2[i])));
    const lblEvery = Math.max(1, Math.ceil(blocks.length / 12));
    blocks.filter((_, j) => j % lblEvery === 0).forEach(wk => cg.append("text").attr("class", "ex-wk").attr("x", cx(wk.start) + 3).attr("y", ctxH + 13).text(wk.label));
    const brush = d3.brushX().extent([[0, 0], [iw, ctxH]]).on("end", ev => {
      if (!ev.sourceEvent) return;
      ex.range = ev.selection ? ev.selection.map(v => Math.round(cx.invert(v))) : null;
      if (ex.range && ex.range[1] - ex.range[0] < 12) ex.range = null;
      drawExplorer();
    });
    const bsel = cg.append("g").attr("class", "ex-brush").call(brush);
    if (ex.range) bsel.call(brush.move, ex.range.map(cx));
    stats(lo, hi);
  }

  // estadistiques del periode triat
  function stats(lo, hi) {
    if (ex.ds === "train") {
      const idx = d3.range(lo, hi), mean = k => d3.mean(idx, SERIES[k].get);
      const flat = idx.filter(i => i > lo && H.load[i] === H.load[i - 1]).length / Math.max(1, idx.length - 1);
      $("ex-stats").innerHTML = statsHTML([
        ["Període", `${label(lo)} – ${label(hi - 1)} (${f(idx.length)} h)`], ["Consum mitjà", `${f(mean("load"))} kW`],
        ["Solar total", `${f(d3.sum(idx, i => H.pv[i]) / 1000, 1)} MWh`], ["CO₂ mitjà de la xarxa", `${f(mean("co2"))} g/kWh`],
        ["Preu mitjà", `${f(mean("price"))} €/MWh`], ["Temperatura mitjana", `${f(mean("temp"), 1)} °C`],
        ["Hores amb el comptador repetit", `${f(100 * flat)} %`],
      ]);
      return;
    }
    const idx = d3.range(lo, hi), sum = k => d3.sum(idx, SERIES[k].get), mean = k => d3.mean(idx, SERIES[k].get);
    const charge = idx.filter(i => H.bat[i] > 1).length, dis = idx.filter(i => H.bat[i] < -1).length;
    $("ex-stats").innerHTML = statsHTML([
      ["Període", `${label(lo)} – ${label(hi - 1)} (${f(idx.length)} h)`],
      ["CO₂ evitat", `${f(sum("savedco2"))} kg`], ["Estalvi", `${f(sum("savedeur"))} €`],
      ["Compra amb / sense bateria", `${f(sum("grid") / 1000)} / ${f(sum("base") / 1000)} MWh`],
      ["CO₂ mitjà de la xarxa", `${f(mean("co2"))} g/kWh`], ["Preu mitjà", `${f(mean("price"))} €/MWh`],
      ["Hores carregant / descarregant", `${f(charge)} / ${f(dis)}`],
      ["Cicles complets", f(d3.sum(idx, i => Math.max(0, -H.bat[i])) / 2000, 1)],
    ]);
  }

  function chips() {
    $("ex-series").innerHTML = Object.entries(SERIES).map(([k, s]) =>
      `<button data-ex="${k}" class="${ex.keys.includes(k) ? "on" : ""}"><i style="background:${s.color}"></i>${s.name}</button>`).join("");
  }

  // ------------------------------------------------------------ grafic en directe (vista del 3D)
  const live = { keys: ["grid", "base", "co2"], title: "Compra a la xarxa i CO₂" };
  function drawLive() {
    const el = $("live-chart");
    if (!el || !el.clientWidth) return;
    const keepH = H, keepS = SERIES, keepN = n;
    H = SIM; SERIES = SIM_SERIES; n = nSim;
    const lo = Math.max(0, now - 48), hi = Math.min(n, now + 25);
    const units = [...new Set(live.keys.map(k => SERIES[k].unit))];
    const rowH = 62, gap = 14, m = { t: 6, r: 12, b: 20, l: 64 };
    const w = el.clientWidth, h = m.t + units.length * (rowH + gap) + m.b;
    el.innerHTML = "";
    const svg = d3.select(el).append("svg").attr("viewBox", `0 0 ${w} ${h}`).attr("width", "100%");
    const iw = w - m.l - m.r, g = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);
    const x = d3.scaleLinear().domain([lo, hi - 1]).range([0, iw]);
    // el futur (pla) es veu mes clar que el passat
    g.append("rect").attr("x", x(now)).attr("width", Math.max(0, iw - x(now))).attr("height", units.length * (rowH + gap) - gap).attr("fill", "#F6F4F0");
    units.forEach((u, r) => {
      const gg = g.append("g").attr("transform", `translate(0,${r * (rowH + gap)})`);
      const keys = live.keys.filter(k => SERIES[k].unit === u);
      const all = keys.flatMap(k => d3.range(lo, hi).map(SERIES[k].get));
      const y = d3.scaleLinear().domain(d3.extent([0, ...all])).nice().range([rowH, 0]);
      gg.append("g").attr("class", "axis").call(d3.axisLeft(y).ticks(2).tickSize(0).tickPadding(6).tickFormat(v => f(v))).call(a => a.select(".domain").remove());
      gg.append("text").attr("class", "ex-unit").attr("x", -m.l + 2).attr("y", -1).text(u);
      keys.forEach(k => {
        const s = SERIES[k];
        if (s.bars) {
          const bw = Math.max(1, iw / (hi - lo) * 0.75);
          gg.selectAll(null).data(d3.range(lo, hi)).join("rect").attr("x", i => x(i) - bw / 2).attr("width", bw)
            .attr("y", i => y(Math.max(0, s.get(i)))).attr("height", i => Math.abs(y(s.get(i)) - y(0)))
            .attr("fill", i => (k === "bat" ? (s.get(i) >= 0 ? "#0072B2" : "#D55E00") : s.color)).attr("opacity", i => (i > now ? 0.4 : 0.9));
        } else {
          const line = d3.line().x(i => x(i)).y(i => y(s.get(i)));
          gg.append("path").datum(d3.range(lo, now + 1)).attr("fill", "none").attr("stroke", s.color).attr("stroke-width", 1.8).attr("stroke-dasharray", s.dash || null).attr("d", line);
          gg.append("path").datum(d3.range(now, hi)).attr("fill", "none").attr("stroke", s.color).attr("stroke-width", 1.4).attr("opacity", 0.45).attr("stroke-dasharray", "2 3").attr("d", line);
        }
      });
    });
    const top = units.length * (rowH + gap) - gap;
    g.append("line").attr("class", "ex-now").attr("x1", x(now)).attr("x2", x(now)).attr("y1", 0).attr("y2", top);
    g.append("text").attr("class", "ex-wk").attr("x", x(now) + 4).attr("y", 10).text("ara");
    g.append("g").attr("class", "axis").attr("transform", `translate(0,${top + 4})`)
      .call(d3.axisBottom(x).tickValues(d3.range(lo, hi).filter(i => +H.t[i].slice(11, 13) % 6 === 0)).tickFormat(i => `${H.t[i].slice(11, 13)} h`).tickSize(0).tickPadding(6))
      .call(a => a.select(".domain").remove());
    $("live-title").textContent = live.title;
    $("live-legend").innerHTML = live.keys.map(k => `<span><i style="background:${SERIES[k].color}"></i>${SERIES[k].name}</span>`).join("");
    H = keepH; SERIES = keepS; n = keepN;
  }

  window.Explorer = {
    init(data) {
      D = data; SIM = data.hours; H = SIM; n = nSim = H.t.length;
      blocks = findBlocks();
      chips();
      document.addEventListener("click", e => {
        const b = e.target.closest("[data-ex]");
        if (b) {
          const k = b.dataset.ex;
          ex.keys = ex.keys.includes(k) ? ex.keys.filter(x => x !== k) : [...ex.keys, k];
          if (!ex.keys.length) ex.keys = [k];
          chips(); drawExplorer();
        }
        const r = e.target.closest("[data-res]");
        if (r) { ex.res = r.dataset.res; document.querySelectorAll("[data-res]").forEach(x => x.classList.toggle("on", x === r)); drawExplorer(); }
        if (e.target.closest("[data-ex-reset]")) { ex.range = null; drawExplorer(); }
        const ds = e.target.closest("[data-ds]");
        if (ds && D.train) useDataset(ds.dataset.ds);
      });
    },
    draw: drawExplorer,
    // l'hora que es mira al 3D: mou la linia d'"ara" i el grafic en directe
    setNow(k) { now = k; drawLive(); if (ex.ds === "sim" && $("v-trust") && $("v-trust").classList.contains("on")) drawExplorer(); },
    drawLive,
    // el 3D tria que es veu al grafic en directe
    focusLive(keys, title) { live.keys = keys; live.title = title; drawLive(); },
    // obre l'explorador amb unes series i el periode al voltant d'una hora
    open(keys, around) {
      if (ex.ds !== "sim") useDataset("sim");
      ex.keys = keys; chips();
      if (around != null) ex.range = [Math.max(0, around - 72), Math.min(n, around + 72)];
    },
  };
})();
