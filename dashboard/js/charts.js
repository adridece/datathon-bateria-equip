// Gràfics de les seccions de decisions (D3). Mateixos colors que la portada.
(function () {
  const C = { text: "#E9E6DF", muted: "#8D8A83", dim: "#5C5A55", line: "#24282C", soft: "#1A1D20",
              accent: "#5FD3A8", ref: "#4A4844", charge: "#5AA9E6", discharge: "#F07B52", price: "#B49AE8" };
  const f = (x, d = 0) => x.toLocaleString("ca-ES", { minimumFractionDigits: d, maximumFractionDigits: d });
  const eur = x => Math.abs(x) >= 10000 ? f(x / 1000) + " k€" : f(x) + " €";
  const $ = id => document.getElementById(id);

  function svg(id, h, m = { t: 10, r: 60, b: 30, l: 50 }) {
    const el = $(id), w = el.clientWidth || 800;
    el.innerHTML = "";
    const s = d3.select(el).append("svg").attr("viewBox", `0 0 ${w} ${h}`).attr("width", "100%");
    return { s, w, h, m, iw: w - m.l - m.r, ih: h - m.t - m.b, g: s.append("g").attr("transform", `translate(${m.l},${m.t})`) };
  }
  const gridY = (g, y, iw) => g.append("g").attr("class", "grid").call(d3.axisLeft(y).ticks(4).tickSize(-iw).tickFormat(""))
    .call(a => a.select(".domain").remove());
  const axis = (sel, a) => sel.attr("class", "axis").call(a).call(x => x.select(".domain").attr("stroke", C.line));

  // ---------------------------------------------------------------- resum
  function intro(D) {
    const y = D.yearly, st = D.strategies, o = D.official;
    $("lead").innerHTML = `Amb control predictiu, la bateria evita <b>${f(y.co2_t_year)} tones de CO₂</b> i ` +
      `<b>${eur(y.eur_year)}</b> de factura cada any, i treu el <b>${f(100 * st[2].score / st[3].score)} %</b> del màxim teòric.`;
    $("kpis").innerHTML = [
      [`${f(y.co2_t_year)} t`, "CO₂ evitat per any (−" + f(y.co2_pct, 1) + " % de les emissions de la xarxa)", "main"],
      ["−" + f(y.cost_pct, 1) + " %", "factura elèctrica, " + eur(y.eur_year) + " l'any", ""],
      [f(o.score, 2), "puntuació oficial al leaderboard (test ocult)", ""],
      [f(o.violations), "infraccions físiques en tot el test", ""],
    ].map(([v, l, c]) => `<div><div class="v ${c}">${v}</div><div class="l">${l}</div></div>`).join("");
  }

  // ---------------------------------------------------------------- 01 estratègia
  function strategy(D) {
    const st = D.strategies;
    $("a-strategy").innerHTML = `Planificar les properes 24 h amb <b>programació lineal</b> dona ${f(st[2].score, 2)} punts, ` +
      `el mateix que un agent que conegués tot el futur. Les regles fixes per hores només en treuen ${f(st[1].score, 2)}.`;
    const rows = st.slice(0, 3);
    const { g, iw, ih } = svg("c-strategy", 170, { t: 18, r: 70, b: 28, l: 200 });
    const x = d3.scaleLinear().domain([0, 7]).range([0, iw]);
    const y = d3.scaleBand().domain(rows.map(r => r.strategy)).range([0, ih]).padding(0.38);
    axis(g.append("g").attr("transform", `translate(0,${ih})`), d3.axisBottom(x).ticks(7).tickSizeOuter(0));
    g.selectAll("text.n").data(rows).join("text").attr("x", -12).attr("y", r => y(r.strategy) + y.bandwidth() / 2 + 4)
      .attr("text-anchor", "end").attr("fill", r => r.strategy.startsWith("MPC") ? C.text : C.muted).style("font-size", "13px").text(r => r.strategy);
    g.selectAll("rect").data(rows).join("rect").attr("y", r => y(r.strategy)).attr("height", y.bandwidth())
      .attr("width", r => Math.max(1, x(r.score))).attr("fill", r => r.strategy.startsWith("MPC") ? C.accent : C.ref);
    g.selectAll("text.v").data(rows).join("text").attr("class", "lab").attr("x", r => x(r.score) + 8)
      .attr("y", r => y(r.strategy) + y.bandwidth() / 2 + 4).text(r => f(r.score, 2));
    const ox = x(st[3].score);
    g.append("line").attr("x1", ox).attr("x2", ox).attr("y1", -8).attr("y2", ih).attr("stroke", C.text).attr("stroke-dasharray", "3 3");
    g.append("text").attr("x", ox - 6).attr("y", -2).attr("text-anchor", "end").text("òptim teòric " + f(st[3].score, 2));
  }

  // ---------------------------------------------------------------- 02 perfil horari + mapa de calor
  function profile(D) {
    const p = D.profile;
    const top = [...p].sort((a, b) => b.battery_kw - a.battery_kw).slice(0, 3).map(r => r.hour).sort((a, b) => a - b);
    const bot = [...p].sort((a, b) => a.battery_kw - b.battery_kw).slice(0, 3).map(r => r.hour).sort((a, b) => a - b);
    $("a-profile").innerHTML = `Carrega quan la xarxa és <b>neta</b> (sobretot a les ${top.join(", ")} h, amb molta solar a la península) ` +
      `i descarrega quan és <b>bruta i cara</b> (${bot.join(", ")} h). No és un horari fix: es recalcula cada hora.`;
    const { s, g, iw, ih } = svg("c-profile", 380, { t: 16, r: 60, b: 30, l: 56 });
    const x = d3.scaleBand().domain(d3.range(24)).range([0, iw]).padding(0.18);
    const panels = [
      { key: "battery_kw", title: "Bateria (kW)", h: 140, bars: true },
      { key: "co2_g", title: "CO₂ xarxa (g/kWh)", h: 80, color: "#DA9048" },
      { key: "price_eur_mwh", title: "Preu (€/MWh)", h: 80, color: C.price },
    ];
    let y0 = 0;
    panels.forEach(pn => {
      const gg = g.append("g").attr("transform", `translate(0,${y0})`);
      const ext = d3.extent(p, r => r[pn.key]);
      const y = pn.bars ? d3.scaleLinear().domain([-500, 500]).range([pn.h, 0])
                        : d3.scaleLinear().domain([ext[0] * 0.95, ext[1] * 1.05]).range([pn.h, 0]);
      gridY(gg, y, iw);
      gg.append("g").attr("class", "axis").call(d3.axisLeft(y).ticks(pn.bars ? 4 : 3).tickSize(0).tickPadding(8))
        .call(a => a.select(".domain").remove());
      gg.append("text").attr("x", iw + 8).attr("y", 10).text(pn.title).style("font-size", "11px");
      if (pn.bars) {
        gg.selectAll("rect").data(p).join("rect").attr("x", r => x(r.hour)).attr("width", x.bandwidth())
          .attr("y", r => y(Math.max(0, r.battery_kw))).attr("height", r => Math.abs(y(r.battery_kw) - y(0)))
          .attr("fill", r => r.battery_kw > 0 ? C.charge : C.discharge);
        gg.append("line").attr("x1", 0).attr("x2", iw).attr("y1", y(0)).attr("y2", y(0)).attr("stroke", C.dim);
      } else {
        gg.append("path").datum(p).attr("fill", "none").attr("stroke", pn.color).attr("stroke-width", 2)
          .attr("d", d3.line().x(r => x(r.hour) + x.bandwidth() / 2).y(r => y(r[pn.key])).curve(d3.curveMonotoneX));
      }
      y0 += pn.h + 24;
    });
    axis(g.append("g").attr("transform", `translate(0,${y0 - 20})`),
      d3.axisBottom(x).tickValues(d3.range(0, 24, 3)).tickFormat(h => h + " h").tickSizeOuter(0));
    s.attr("viewBox", `0 0 ${iw + 116} ${y0 + 30}`);
  }

  function heat(D) {
    const H = D.hours, n = H.t.length;
    const days = [];
    for (let i = 0; i < n; i += 24) days.push(i);
    const { g, iw, ih } = svg("c-heat", Math.max(260, days.length * 5 + 40), { t: 6, r: 60, b: 26, l: 56 });
    const x = d3.scaleBand().domain(d3.range(24)).range([0, iw]);
    const y = d3.scaleBand().domain(days).range([0, ih]);
    const col = d3.scaleLinear().domain([-500, 0, 500]).range([C.discharge, "#1A1D20", C.charge]);
    const cells = [];
    days.forEach(d0 => { for (let h = 0; h < 24 && d0 + h < n; h++) cells.push([d0, h, H.bat[d0 + h]]); });
    g.selectAll("rect").data(cells).join("rect").attr("x", c => x(c[1])).attr("y", c => y(c[0]))
      .attr("width", x.bandwidth() + 0.3).attr("height", y.bandwidth() + 0.3).attr("fill", c => col(c[2]));
    axis(g.append("g").attr("transform", `translate(0,${ih})`),
      d3.axisBottom(x).tickValues(d3.range(0, 24, 3)).tickFormat(h => h + " h").tickSizeOuter(0));
    D.weeks.forEach(w => g.append("text").attr("x", -8).attr("y", y(Math.floor(w.start / 24) * 24) + 8)
      .attr("text-anchor", "end").style("font-size", "10px").text(w.label.slice(0, 5)));
  }

  // ---------------------------------------------------------------- 03 mida de la bateria
  function sizing(D) {
    const caps = [...new Set(D.sizing.map(r => r.capacity_kwh))], pows = [...new Set(D.sizing.map(r => r.power_kw))];
    const st = { cap: 2000, pow: 500, cost: 350 };
    const btns = (id, vals, key) => {
      $(id).innerHTML = vals.map(v => `<button data-v="${v}">${f(v)}</button>`).join("");
      $(id).querySelectorAll("button").forEach(b => b.onclick = () => { st[key] = +b.dataset.v; draw(); });
    };
    btns("b-cap", caps, "cap");
    btns("b-pow", pows, "pow");
    $("cost").oninput = e => { st.cost = +e.target.value; draw(); };

    function draw() {
      ["b-cap", "b-pow"].forEach((id, j) => $(id).querySelectorAll("button")
        .forEach(b => b.classList.toggle("on", +b.dataset.v === (j ? st.pow : st.cap))));
      $("cost-v").textContent = f(st.cost);
      const rows = D.sizing.map(r => ({ ...r, invest: r.capacity_kwh * st.cost, payback: r.capacity_kwh * st.cost / r.eur_year }));
      const cur = rows.find(r => r.capacity_kwh === st.cap && r.power_kw === st.pow);
      const base = rows.find(r => r.capacity_kwh === 2000 && r.power_kw === 500);
      const ok = rows.filter(r => r.power_kw === st.pow && r.payback < 10);
      const best = ok.length ? ok.reduce((a, b) => (b.co2_t_year > a.co2_t_year ? b : a)) : null;
      let txt = `Amb <b>${f(st.cap)} kWh i ${f(st.pow)} kW</b> s'evitarien <b>${f(cur.co2_t_year)} t de CO₂</b> i ${eur(cur.eur_year)} l'any`;
      if (st.cap !== 2000 || st.pow !== 500) {
        const dlt = cur.co2_t_year - base.co2_t_year;
        txt += ` (${dlt >= 0 ? "+" : "−"}${f(Math.abs(dlt))} t respecte a la bateria del repte)`;
      }
      txt += `, amb un retorn de ${f(cur.payback, 1)} anys.`;
      if (best) txt += ` Amb ${f(st.pow)} kW, la que evita més CO₂ amb retorn de menys de 10 anys és <b>${f(best.capacity_kwh)} kWh</b>.`;
      $("a-size").innerHTML = txt;

      const { g, iw, ih } = svg("c-size", 300, { t: 14, r: 80, b: 34, l: 50 });
      const x = d3.scaleLinear().domain([0, d3.max(caps)]).range([0, iw]);
      const y = d3.scaleLinear().domain([0, d3.max(rows, r => r.co2_t_year) * 1.08]).range([ih, 0]);
      gridY(g, y, iw);
      g.append("g").attr("class", "axis").call(d3.axisLeft(y).ticks(5).tickSize(0).tickPadding(8)).call(a => a.select(".domain").remove());
      axis(g.append("g").attr("transform", `translate(0,${ih})`), d3.axisBottom(x).ticks(8).tickFormat(v => f(v)).tickSizeOuter(0));
      g.append("text").attr("x", iw).attr("y", ih + 30).attr("text-anchor", "end").text("capacitat (kWh)");
      g.append("text").attr("x", 0).attr("y", -2).text("CO₂ evitat (t/any)");
      pows.forEach(p => {
        const pr = rows.filter(r => r.power_kw === p), on = p === st.pow;
        g.append("path").datum(pr).attr("fill", "none").attr("stroke", on ? C.accent : C.ref).attr("stroke-width", on ? 2.2 : 1.4)
          .attr("d", d3.line().x(r => x(r.capacity_kwh)).y(r => y(r.co2_t_year)));
        g.selectAll(null).data(pr).join("circle").attr("cx", r => x(r.capacity_kwh)).attr("cy", r => y(r.co2_t_year))
          .attr("r", 2.5).attr("fill", on ? C.accent : C.ref);
        const l = pr[pr.length - 1];
        g.append("text").attr("x", x(l.capacity_kwh) + 8).attr("y", y(l.co2_t_year) + 4)
          .attr("fill", on ? C.accent : C.muted).text(f(p) + " kW");
      });
      g.append("circle").attr("cx", x(cur.capacity_kwh)).attr("cy", y(cur.co2_t_year)).attr("r", 8)
        .attr("fill", "none").attr("stroke", C.text).attr("stroke-width", 1.5);

      const tr = rows.filter(r => r.power_kw === st.pow);
      $("t-size").innerHTML = "<tr><th>Capacitat</th><th>CO₂ evitat</th><th>Estalvi</th><th>Inversió</th><th>Retorn</th><th>€ per t CO₂ (15 anys)</th></tr>" +
        tr.map(r => `<tr class="${r.capacity_kwh === st.cap ? "sel" : ""}"><td>${f(r.capacity_kwh)} kWh</td><td>${f(r.co2_t_year)} t/any</td>` +
          `<td>${eur(r.eur_year)}/any</td><td>${eur(r.invest)}</td><td>${f(r.payback, 1)} anys</td><td>${f(r.invest / (r.co2_t_year * 15))} €</td></tr>`).join("");
    }
    draw();
    addEventListener("resize", draw);
  }

  // ---------------------------------------------------------------- 04 fiabilitat
  function robust(D) {
    const r = D.robustness, m = D.monthly;
    $("a-robust").innerHTML = `Sí. Amb un <b>50 % d'error</b> a les previsions de preu i CO₂, la puntuació només baixa de ` +
      `${f(r[0].score, 2)} a ${f(r[r.length - 1].score, 2)}, i l'estalvi de CO₂ és positiu <b>totes les setmanes</b> ` +
      `(entre un ${f(d3.min(m, d => d.co2_pct), 1)} % i un ${f(d3.max(m, d => d.co2_pct), 1)} %). Al test oficial, amb dades que l'agent no havia vist, en treu ${f(D.official.score, 2)}.`;
    const { g, iw, ih } = svg("c-robust", 230, { t: 16, r: 60, b: 34, l: 50 });
    const x = d3.scaleLinear().domain([0, 50]).range([0, iw]);
    const y = d3.scaleLinear().domain([0, 7]).range([ih, 0]);
    gridY(g, y, iw);
    g.append("g").attr("class", "axis").call(d3.axisLeft(y).ticks(4).tickSize(0).tickPadding(8)).call(a => a.select(".domain").remove());
    axis(g.append("g").attr("transform", `translate(0,${ih})`), d3.axisBottom(x).ticks(5).tickFormat(v => v + " %").tickSizeOuter(0));
    g.append("text").attr("x", iw).attr("y", ih + 30).attr("text-anchor", "end").text("error afegit a les previsions");
    g.append("path").datum(r).attr("fill", "none").attr("stroke", C.accent).attr("stroke-width", 2.2)
      .attr("d", d3.line().x(d => x(d.error_pct)).y(d => y(d.score)));
    g.selectAll("circle").data(r).join("circle").attr("cx", d => x(d.error_pct)).attr("cy", d => y(d.score)).attr("r", 3).attr("fill", C.accent);
    g.selectAll("text.lab").data(r).join("text").attr("class", "lab").attr("x", d => x(d.error_pct)).attr("y", d => y(d.score) - 10)
      .attr("text-anchor", "middle").text(d => f(d.score, 2));

    const b = svg("c-month", 220, { t: 10, r: 20, b: 30, l: 50 });
    const xm = d3.scaleBand().domain(m.map(d => d.month)).range([0, b.iw]).padding(0.3);
    const xi = d3.scaleBand().domain(["co2_pct", "cost_pct"]).range([0, xm.bandwidth()]).padding(0.1);
    const ym = d3.scaleLinear().domain([0, d3.max(m, d => Math.max(d.co2_pct, d.cost_pct)) * 1.1]).range([b.ih, 0]);
    gridY(b.g, ym, b.iw);
    b.g.append("g").attr("class", "axis").call(d3.axisLeft(ym).ticks(4).tickFormat(v => v + " %").tickSize(0).tickPadding(8))
      .call(a => a.select(".domain").remove());
    axis(b.g.append("g").attr("transform", `translate(0,${b.ih})`), d3.axisBottom(xm).tickSizeOuter(0));
    m.forEach(d => ["co2_pct", "cost_pct"].forEach(key => b.g.append("rect").attr("x", xm(d.month) + xi(key)).attr("width", xi.bandwidth())
      .attr("y", ym(d[key])).attr("height", b.ih - ym(d[key])).attr("fill", key === "co2_pct" ? C.accent : C.ref)));
  }

  window.Charts = {
    render(D) {
      intro(D);
      strategy(D);
      profile(D);
      heat(D);
      sizing(D);
      robust(D);
      addEventListener("resize", () => { strategy(D); profile(D); heat(D); robust(D); });
    },
  };
})();
