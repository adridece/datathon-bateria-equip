// Gràfics del tauler (D3). Tots fan servir els mateixos colors i s'animen en entrar.
(function () {
  const C = { text: "#1F2326", muted: "#6E6A63", dim: "#A19C93", line: "#E6E2DA", soft: "#F0EDE7",
              accent: "#47908B", ref: "#CFC9BD", charge: "#0072B2", discharge: "#D55E00", price: "#7A5195", co2: "#A9824F" };
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
    const y = D.yearly, H = D.hours, toYear = 8760 / H.t.length;
    const out = d3.sum(H.bat, v => Math.max(0, -v)) * toYear;   // kWh descarregats per any
    const cards = [
      { cls: "hero", label: "CO₂ evitat per any (estimació)", v: y.co2_t_year, fmt: v => f(v) + " t", delta: `−${f(y.co2_pct, 1)} % d'emissions` },
      { cls: "", label: "Estalvi a la factura per any (estimació)", v: y.eur_year, fmt: v => eur(v), delta: `−${f(y.cost_pct, 1)} % de cost` },
      { cls: "", label: "Energia moguda a hores netes per any", v: out / 1000, fmt: v => f(v) + " MWh", delta: "descarregada al vespre i al matí", n: true },
      { cls: "", label: "Cicles complets per any", v: out / 2000, fmt: v => f(v), delta: "desgast de la bateria", n: true },
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

  // ---------------------------------------------------------------- conclusions i decisions (el que demana la Tukey)
  function decisions() {
    const st = D.strategies, p = D.profile, r = D.robustness, H = D.hours, y = D.yearly;
    const tons = s => s.co2_pct / y.co2_pct * y.co2_t_year;
    const top = [...p].sort((a, b) => b.battery_kw - a.battery_kw).slice(0, 3).map(x => x.hour).sort((a, b) => a - b);
    const bot = [...p].sort((a, b) => a.battery_kw - b.battery_kw).slice(0, 3).map(x => x.hour).sort((a, b) => a - b);
    const sz = D.sizing.filter(s => s.power_kw === 500).map(s => ({ ...s, payback: s.capacity_kwh * 350 / s.eur_year }));
    const now = sz.find(s => s.capacity_kwh === 2000);
    const best = sz.filter(s => s.payback < 10).reduce((a, b) => (b.co2_t_year > a.co2_t_year ? b : a));
    const low = Math.min(...H.load);
    const rows = [
      { d: "Operar la bateria amb control predictiu", view: "strategy",
        c: `Evita ${f(tons(st[2]))} t de CO₂ i ${eur(y.eur_year)} l'any, el ${f(100 * st[2].co2_pct / st[3].co2_pct)} % del que s'evitaria coneixent el futur. Un horari fix per hores només n'evita ${f(tons(st[1]))} t.` },
      { d: "Carregar a les hores de sol, descarregar al matí i al vespre", view: "strategy",
        c: `Les hores amb més càrrega (${top.join(", ")} h) són les de menys CO₂; les de descàrrega (${bot.join(", ")} h), les de més CO₂ i preu.` },
      { d: `Ampliar la bateria a ${f(best.capacity_kwh)} kWh amb el mateix inversor`, view: "sizing",
        c: `Passaria de ${f(now.co2_t_year)} a ${f(best.co2_t_year)} t de CO₂ l'any i es recuperaria en ${f(best.payback, 1)} anys (a 350 €/kWh). Per sobre de 6.000 kWh el CO₂ gairebé no baixa.` },
      { d: "Posar-la en marxa amb les previsions públiques de REE", view: "trust",
        c: `Amb un 50 % d'error a les previsions de preu i CO₂ encara conserva el ${f(100 * r[r.length - 1].score / r[0].score)} % de l'estalvi: no cal una previsió perfecta.` },
      { d: "Mantenir el límit de 500 kW de consum net", view: "trust",
        c: `El consum mínim del campus és de ${f(low)} kW i la bateria no baixa mai del límit en les 11 setmanes. Un horari fix l'hauria superat ${f(st[1].violations)} vegades.` },
    ];
    $("decisions").innerHTML = rows.map((r, i) => `<div class="decision"><div class="n">${String(i + 1).padStart(2, "0")}</div>
      <div><b>${r.d}</b><p>${r.c}</p></div>
      <button data-goto="${r.view}" data-sel="${r.go || ""}">Veure l'evidència</button></div>`).join("");
  }

  // ---------------------------------------------------------------- estratègies
  function strategyBars(id, h) {
    const st = D.strategies, rows = st.slice(0, 3), y0 = D.yearly;
    const tons = s => s.co2_pct / y0.co2_pct * y0.co2_t_year, euros = s => s.cost_pct / y0.cost_pct * y0.eur_year;
    const { g, iw, ih } = frame(id, h, { t: 22, r: 96, b: 26, l: 170 });
    const x = d3.scaleLinear().domain([0, tons(st[3]) * 1.1]).range([0, iw]);
    const y = d3.scaleBand().domain(rows.map(r => r.strategy)).range([0, ih]).padding(0.35);
    axisX(g, x, ih, s => d3.axisBottom(s).ticks(5).tickFormat(v => v + " t"));
    g.selectAll("text.n").data(rows).join("text").attr("x", -12).attr("y", r => y(r.strategy) + y.bandwidth() / 2 + 4)
      .attr("text-anchor", "end").style("font-size", "12.5px").style("fill", r => (r.strategy.startsWith("MPC") ? C.text : C.muted)).text(r => r.strategy);
    g.selectAll("rect").data(rows).join("rect").attr("y", r => y(r.strategy)).attr("height", y.bandwidth()).attr("rx", y.bandwidth() / 2)
      .attr("fill", r => (r.strategy.startsWith("MPC") ? C.accent : C.ref)).attr("width", 0)
      .transition().duration(T).ease(ease).delay((_, i) => i * 90).attr("width", r => (tons(r) < 0.01 ? 0 : Math.max(y.bandwidth(), x(tons(r)))));
    g.selectAll("text.v").data(rows).join("text").attr("class", "lab").attr("x", r => Math.max(y.bandwidth(), x(tons(r))) + 8)
      .attr("y", r => y(r.strategy) + y.bandwidth() / 2 + 4).text(r => `${f(tons(r))} t, ${eur(euros(r))}`).style("opacity", 0)
      .transition().delay(T).style("opacity", 1);
    const ox = x(tons(st[3]));
    g.append("line").attr("x1", ox).attr("x2", ox).attr("y1", -10).attr("y2", ih).attr("stroke", C.text).attr("stroke-dasharray", "3 4");
    g.append("text").attr("x", ox).attr("y", -12).attr("text-anchor", "middle").text("màxim si es conegués el futur");
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

  // ---------------------------------------------------------------- diagrama de caixa (Tukey) del CO₂ per hora
  function hourBoxes() {
    const H = D.hours, n = H.t.length;
    const hourOf = i => +H.t[i].slice(11, 13);
    const byHour = d3.range(24).map(h => ({ h, co2: [], bat: [] }));
    for (let i = 0; i < n; i++) { byHour[hourOf(i)].co2.push(H.co2[i] * 1000); byHour[hourOf(i)].bat.push(H.bat[i]); }
    const stats = byHour.map(b => {
      const v = b.co2.slice().sort(d3.ascending);
      const q1 = d3.quantileSorted(v, 0.25), med = d3.quantileSorted(v, 0.5), q3 = d3.quantileSorted(v, 0.75), iqr = q3 - q1;
      // bigotis fins a l'últim valor dins d'1,5 vegades el rang interquartílic, com ho feia Tukey
      const lo = d3.min(v.filter(x => x >= q1 - 1.5 * iqr)), hi = d3.max(v.filter(x => x <= q3 + 1.5 * iqr));
      return { h: b.h, n: v.length, q1, med, q3, lo, hi, out: v.filter(x => x < lo || x > hi), bat: d3.mean(b.bat) };
    });

    const { g, iw, ih } = frame("c-box", 260, { t: 10, r: 16, b: 28, l: 44 });
    const x = d3.scaleBand().domain(d3.range(24)).range([0, iw]).padding(0.3);
    const y = d3.scaleLinear().domain([0, d3.max(H.co2) * 1040]).nice().range([ih, 0]);   // kg/kWh a g/kWh
    const col = d3.scaleLinear().domain([-500, 0, 500]).range([C.discharge, "#DDD8CF", C.charge]).clamp(true);
    gridY(g, y, iw, 4, d => d + " g");
    axisX(g, x, ih, s => d3.axisBottom(s).tickValues(d3.range(0, 24, 3)).tickFormat(h => h + " h"));

    const cx = s => x(s.h) + x.bandwidth() / 2;
    const box = g.selectAll("g.box").data(stats).join("g").attr("class", "box").style("opacity", 0);
    box.append("line").attr("x1", cx).attr("x2", cx).attr("y1", s => y(s.lo)).attr("y2", s => y(s.hi)).attr("stroke", C.dim);
    // caixa amb osca: mediana ± 1,58·IQR/√n (McGill, Tukey i Larsen, 1978)
    const notched = s => {
      const k = 1.58 * (s.q3 - s.q1) / Math.sqrt(s.n), bw = x.bandwidth(), x0 = x(s.h), x1 = x0 + bw, xi = bw * 0.22;
      const top = y(s.q3), bot = y(s.q1), nt = Math.max(top, y(s.med + k)), nb = Math.min(bot, y(s.med - k)), m = y(s.med);
      return `M${x0},${top}H${x1}V${nt}L${x1 - xi},${m}L${x1},${nb}V${bot}H${x0}V${nb}L${x0 + xi},${m}L${x0},${nt}Z`;
    };
    box.append("path").attr("d", notched).attr("fill", s => col(s.bat));
    box.append("line").attr("x1", s => x(s.h)).attr("x2", s => x(s.h) + x.bandwidth())
      .attr("y1", s => y(s.med)).attr("y2", s => y(s.med)).attr("stroke", C.text).attr("stroke-width", 1.6)
      .attr("transform", s => `translate(${x.bandwidth() * 0.22},0)`).attr("x2", s => x(s.h) + x.bandwidth() * 0.56);
    box.selectAll("circle").data(s => s.out.map(v => [s, v])).join("circle")
      .attr("cx", d => cx(d[0])).attr("cy", d => y(d[1])).attr("r", 1.8).attr("fill", "none").attr("stroke", C.dim);
    box.append("title").text(s => `${s.h} h. Resum de cinc nombres: ${f(s.lo)}, ${f(s.q1)}, ${f(s.med)}, ${f(s.q3)}, ${f(s.hi)} g/kWh. Bateria de mitjana ${f(s.bat)} kW`);
    box.transition().duration(T).delay(s => s.h * 20).style("opacity", 1);

    // conclusió: quants dies l'hora més neta no és la de sempre
    const days = d3.range(0, n - 23, 24).map(d0 => d3.minIndex(d3.range(24), h => H.co2[d0 + h]));
    const usual = d3.greatest(d3.rollups(days, v => v.length, h => h), r => r[1]);
    const other = days.filter(h => h !== usual[0]).length / days.length;
    const wide = d3.greatest(stats, s => s.hi - s.lo);
    $("box-take").innerHTML = `A les ${wide.h} h el CO₂ va de ${f(wide.lo)} a ${f(wide.hi)} g/kWh segons el dia, i ` +
      `<b>${f(other * 100)} % dels dies</b> l'hora més neta no és la de sempre (les ${usual[0]} h). ` +
      `Per això la bateria decideix amb la previsió de cada dia i no amb un horari fix.`;
  }

  // ---------------------------------------------------------------- amb bateria i sense (setmana triada)
  let wk = null;
  function counterfactual() {
    const H = D.hours, w = wk || D.weeks[0], idx = d3.range(w.start, w.end);
    let acc = 0, eur = 0;
    const rows = idx.map(i => {
      acc += (H.base[i] - H.grid[i]) * H.co2[i];
      eur += (H.base[i] - H.grid[i]) * H.price[i];
      return { i, base: H.base[i], grid: H.grid[i], acc };
    });
    const { g, iw } = frame("c-counter", 300, { t: 10, r: 70, b: 26, l: 52 });
    const x = d3.scaleLinear().domain([w.start, w.end - 1]).range([0, iw]);
    const top = 170, gap = 26, low = 70;
    const y = d3.scaleLinear().domain([0, d3.max(rows, r => Math.max(r.base, r.grid)) * 1.05]).nice().range([top, 0]);
    gridY(g, y, iw, 4, d => f(d) + " kW");
    // zona entre les dues corbes: verd si la bateria fa comprar menys, blau si en fa comprar més (carrega)
    const between = (cond) => d3.area().defined(r => cond(r)).x(r => x(r.i)).y0(r => y(r.base)).y1(r => y(r.grid)).curve(d3.curveStepAfter);
    g.append("path").datum(rows).attr("fill", C.accent).attr("opacity", 0.28).attr("d", between(r => r.grid <= r.base));
    g.append("path").datum(rows).attr("fill", C.charge).attr("opacity", 0.22).attr("d", between(r => r.grid >= r.base));
    const line = k => d3.line().x(r => x(r.i)).y(r => y(r[k])).curve(d3.curveStepAfter);
    g.append("path").datum(rows).attr("fill", "none").attr("stroke", C.dim).attr("stroke-dasharray", "4 3").attr("d", line("base"));
    g.append("path").datum(rows).attr("fill", "none").attr("stroke", C.text).attr("stroke-width", 1.4).attr("d", line("grid"));
    // CO₂ evitat acumulat: baixa quan carrega i puja quan descarrega
    const g2 = g.append("g").attr("transform", `translate(0,${top + gap})`);
    const y2 = d3.scaleLinear().domain(d3.extent([0, ...rows.map(r => r.acc)])).nice().range([low, 0]);
    gridY(g2, y2, iw, 2, d => f(d) + " kg");
    g2.append("path").datum(rows).attr("fill", "none").attr("stroke", C.accent).attr("stroke-width", 2).attr("d", d3.line().x(r => x(r.i)).y(r => y2(r.acc)));
    g2.append("text").attr("x", iw + 8).attr("y", y2(acc) + 4).attr("fill", C.accent).text(f(acc) + " kg");
    const days = d3.range(w.start, w.end, 24);
    g2.append("g").attr("class", "axis").attr("transform", `translate(0,${low})`)
      .call(d3.axisBottom(x).tickValues(days).tickFormat(i => H.t[i].slice(8, 10) + "/" + H.t[i].slice(5, 7)).tickSize(0).tickPadding(8))
      .call(s => s.select(".domain").remove());
    $("counter-take").innerHTML = `Aquesta setmana la bateria evita <b>${f(acc)} kg de CO₂</b> i <b>${f(eur)} €</b>. ` +
      `Compra més a la xarxa al migdia, quan és neta (zona blava), i menys al vespre, quan és bruta (zona verda): ` +
      `el consum total gairebé no canvia, el que canvia és <b>quan</b> es compra.`;
  }

  // ---------------------------------------------------------------- dia a dia: quan compensa més
  function dailyRows() {
    const H = D.hours, out = [];
    for (let d0 = 0; d0 + 24 <= H.t.length; d0 += 24) {
      const c = d3.range(d0, d0 + 24).map(i => H.co2[i] * 1000);
      out.push({ d0, spread: d3.max(c) - d3.min(c), saved: d3.sum(d3.range(d0, d0 + 24), i => (H.base[i] - H.grid[i]) * H.co2[i]) });
    }
    return out;
  }
  // recta resistent de Tukey: medianes dels terços esquerre i dret per al pendent
  function resistantLine(pts) {
    const s = pts.slice().sort((a, b) => a.x - b.x), k = Math.floor(s.length / 3);
    const L = s.slice(0, k), M = s.slice(k, s.length - k), R = s.slice(s.length - k);
    const med = (a, key) => d3.median(a, p => p[key]);
    const b = (med(R, "y") - med(L, "y")) / (med(R, "x") - med(L, "x"));
    const a = d3.mean([L, M, R], grp => med(grp, "y") - b * med(grp, "x"));
    return { a, b };
  }
  function scatter() {
    const rows = dailyRows(), pts = rows.map(r => ({ x: r.spread, y: r.saved, d0: r.d0 }));
    const { g, iw, ih } = frame("c-scatter", 250, { t: 10, r: 16, b: 34, l: 52 });
    const x = d3.scaleLinear().domain([0, d3.max(pts, p => p.x) * 1.05]).nice().range([0, iw]);
    const y = d3.scaleLinear().domain([Math.min(0, d3.min(pts, p => p.y)), d3.max(pts, p => p.y) * 1.08]).nice().range([ih, 0]);
    gridY(g, y, iw, 4, d => f(d) + " kg");
    axisX(g, x, ih, s => d3.axisBottom(s).ticks(5).tickFormat(d => f(d)));
    g.append("text").attr("x", iw).attr("y", ih + 30).attr("text-anchor", "end").attr("fill", C.muted).text("diferència de CO₂ dins del dia (g/kWh)");
    const { a, b } = resistantLine(pts);
    const xs = x.domain();
    g.append("line").attr("x1", x(xs[0])).attr("x2", x(xs[1])).attr("y1", y(a + b * xs[0])).attr("y2", y(a + b * xs[1]))
      .attr("stroke", C.text).attr("stroke-dasharray", "5 4");
    g.selectAll("circle").data(pts).join("circle").attr("cx", p => x(p.x)).attr("cy", p => y(p.y)).attr("r", 4)
      .attr("fill", C.accent).attr("fill-opacity", 0.55).attr("stroke", "#fff")
      .append("title").text(p => `${D.hours.t[p.d0].slice(0, 10)}: ${f(p.x)} g/kWh de diferència, ${f(p.y)} kg evitats`);
    const lo = d3.quantile(pts.map(p => p.x).sort(d3.ascending), 0.25), hi = d3.quantile(pts.map(p => p.x).sort(d3.ascending), 0.75);
    const yLo = d3.median(pts.filter(p => p.x <= lo), p => p.y), yHi = d3.median(pts.filter(p => p.x >= hi), p => p.y);
    $("scatter-take").innerHTML = `Cada 10 g/kWh més de diferència dins del dia, la bateria evita uns <b>${f(b * 10)} kg</b> més. ` +
      `Els dies més variables n'evita ${f(yHi)} kg i els més plans ${f(yLo)} kg (medianes): ` +
      `com més renovables hi hagi a la xarxa, més valdrà la bateria.`;
  }

  // ---------------------------------------------------------------- polit de medianes (dia de la setmana × hora)
  function medianPolish(m, iters = 10) {
    const r = m.map(row => row.slice()), R = m.length, Cn = m[0].length;
    let all = 0; const row = Array(R).fill(0), col = Array(Cn).fill(0);
    for (let it = 0; it < iters; it++) {
      for (let i = 0; i < R; i++) { const md = d3.median(r[i]); row[i] += md; for (let j = 0; j < Cn; j++) r[i][j] -= md; }
      const dc = d3.median(col); all += dc; for (let j = 0; j < Cn; j++) col[j] -= dc;
      for (let j = 0; j < Cn; j++) { const md = d3.median(r, rr => rr[j]); col[j] += md; for (let i = 0; i < R; i++) r[i][j] -= md; }
      const dr = d3.median(row); all += dr; for (let i = 0; i < R; i++) row[i] -= dr;
    }
    return { all, row, col, res: r };
  }
  function polish() {
    // taula dia × hora amb els 77 dies reals (sense fer mitjanes, per no amagar la variació entre dies)
    const H = D.hours, m = [];
    for (let d0 = 0; d0 + 24 <= H.t.length; d0 += 24) m.push(d3.range(24).map(h => H.co2[d0 + h] * 1000));
    const P = medianPolish(m);
    const ssH = m.length * d3.sum(P.col, v => v * v), ssD = 24 * d3.sum(P.row, v => v * v), ssR = d3.sum(P.res.flat(), v => v * v), tot = ssH + ssD + ssR;
    const { g, iw } = frame("c-polish", 250, { t: 10, r: 12, b: 0, l: 52 });
    const lim = d3.max([...P.col, ...P.row].map(Math.abs)) * 1.1;
    const panel = (y0, h, keys, vals, lab, every) => {
      const gg = g.append("g").attr("transform", `translate(0,${y0})`);
      const x = d3.scaleBand().domain(keys).range([0, iw]).padding(0.2), y = d3.scaleLinear().domain([-lim, lim]).range([h, 0]);
      gridY(gg, y, iw, 2, d => (d > 0 ? "+" : "") + f(d));
      gg.selectAll("rect").data(vals).join("rect").attr("x", (_, i) => x(keys[i])).attr("width", x.bandwidth()).attr("rx", 1.5)
        .attr("y", v => y(Math.max(0, v))).attr("height", v => Math.abs(y(v) - y(0))).attr("fill", v => (v < 0 ? C.accent : C.co2))
        .append("title").text((v, i) => `${lab(keys[i])}: ${v > 0 ? "+" : ""}${f(v)} g/kWh`);
      gg.append("g").attr("class", "axis").attr("transform", `translate(0,${h})`)
        .call(d3.axisBottom(x).tickValues(keys.filter((_, i) => i % every === 0)).tickFormat(lab).tickSize(0).tickPadding(6))
        .call(s => s.select(".domain").remove());
    };
    panel(0, 110, d3.range(24), P.col, h => h + " h", 3);
    panel(145, 75, d3.range(m.length), P.row, i => H.t[i * 24].slice(8, 10) + "/" + H.t[i * 24].slice(5, 7), 14);
    $("polish-take").innerHTML = `Nivell típic ${f(P.all)} g/kWh. L'hora explica el <b>${f(ssH / tot * 100)} %</b> de la variació, ` +
      `el nivell de cada dia el ${f(ssD / tot * 100)} % i la forma pròpia de cada dia el ${f(ssR / tot * 100)} %. ` +
      `Un horari fix només aprofita la part de l'hora; la previsió diària aprofita també la resta.`;
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
  // cost net per tona en 15 anys: (inversió − estalvi acumulat) / tones evitades. Negatiu = es paga sola i encara en sobra
  function netPerTon(r) {
    const v = (r.invest - r.eur_year * 15) / (r.co2_t_year * 15);
    return v < 0 ? `es paga sola (+${f(-v)} €/t)` : `${f(v)} €/t`;
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

    $("t-size").innerHTML = "<tr><th>Capacitat</th><th>CO₂ evitat</th><th>Estalvi</th><th>Inversió</th><th>Retorn</th><th>Cost net per t CO₂ (15 anys)</th></tr>" +
      rows.filter(r => r.power_kw === size.pow).map(r => `<tr class="${r.capacity_kwh === size.cap ? "sel" : ""}"><td>${f(r.capacity_kwh)} kWh</td>` +
        `<td>${f(r.co2_t_year)} t/any</td><td>${eur(r.eur_year)}/any</td><td>${eur(r.invest)}</td><td>${f(r.payback, 1)} anys</td>` +
        `<td>${netPerTon(r)}</td></tr>`).join("");
  }

  // ---------------------------------------------------------------- fiabilitat
  function robust() {
    const r = D.robustness, m = D.monthly;
    let { g, iw, ih } = frame("c-robust", 250, { t: 22, r: 20, b: 30, l: 40 });
    const x = d3.scaleLinear().domain([0, 50]).range([0, iw]);
    const keep = d => 100 * d.score / r[0].score;   // part de l'estalvi (CO₂ i factura) que es conserva
    const y = d3.scaleLinear().domain([0, 100]).range([ih, 0]);
    gridY(g, y, iw, 4, v => v + " %");
    axisX(g, x, ih, s => d3.axisBottom(s).ticks(5).tickFormat(v => v + " %"));
    g.append("path").datum(r).attr("fill", C.accent).attr("opacity", 0.08)
      .attr("d", d3.area().x(d => x(d.error_pct)).y0(ih).y1(d => y(keep(d))).curve(d3.curveMonotoneX));
    const path = g.append("path").datum(r).attr("fill", "none").attr("stroke", C.accent).attr("stroke-width", 3).attr("stroke-linecap", "round")
      .attr("d", d3.line().x(d => x(d.error_pct)).y(d => y(keep(d))).curve(d3.curveMonotoneX));
    const L = path.node().getTotalLength();
    path.attr("stroke-dasharray", L).attr("stroke-dashoffset", L).transition().duration(1000).ease(ease).attr("stroke-dashoffset", 0);
    g.selectAll("circle").data(r).join("circle").attr("cx", d => x(d.error_pct)).attr("cy", d => y(keep(d))).attr("r", 4.5)
      .attr("fill", "#fff").attr("stroke", C.accent).attr("stroke-width", 2);
    g.selectAll("text.lab").data(r).join("text").attr("class", "lab").attr("x", d => x(d.error_pct)).attr("y", d => y(keep(d)) - 12)
      .attr("text-anchor", "middle").text(d => f(keep(d)) + " %");

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

  // ---------------------------------------------------------------- API
  const drawn = {};
  const draw = {
    overview: () => { kpis(); decisions(); counterfactual(); },
    strategy: () => { strategyBars("c-strategy", 200); profile("c-profile", false); hourBoxes(); scatter(); polish(); heat(); },
    sizing: () => sizing(),
    trust: () => robust(),
    live: () => {},
    planner: () => {},
  };
  let current = "live";
  window.Charts = {
    init(data) { D = data; sizingSetup(); },
    setWeek(w) { wk = w; if (current === "overview") counterfactual(); },
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
