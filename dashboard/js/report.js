// Informe d'una pàgina per a UPC Sostenible. Es genera a partir de les mateixes dades i s'imprimeix (o es desa en PDF).
(function () {
  const f = (x, d = 0) => x.toLocaleString("ca-ES", { minimumFractionDigits: d, maximumFractionDigits: d });
  const eur = x => (Math.abs(x) >= 10000 ? f(x / 1000) + " k€" : f(x) + " €");

  function build(D) {
    const y = D.yearly, st = D.strategies, o = D.official, r = D.robustness, m = D.monthly;
    const sz = D.sizing.filter(s => s.power_kw === 500).map(s => ({ ...s, payback: s.capacity_kwh * 350 / s.eur_year }));
    const best = sz.filter(s => s.payback < 10).reduce((a, b) => (b.co2_t_year > a.co2_t_year ? b : a));
    const today = new Date().toLocaleDateString("ca-ES", { day: "numeric", month: "long", year: "numeric" });
    const strat = document.querySelector("#c-mini-strategy svg"), prof = document.querySelector("#c-mini-profile svg");
    return `
      <header><img src="static/logo-datathon.png" alt=""><div><div class="team">LA DATONETA</div>
        <h1>Bateria del Campus Nord: recomanacions per a UPC Sostenible</h1><p>Datathon FME 2026, ${today}</p></div></header>
      <section class="lead">Operar la bateria amb control predictiu evitaria <b>${f(y.co2_t_year)} tones de CO₂</b> i
        <b>${eur(y.eur_year)}</b> de factura cada any, el ${f(100 * st[2].score / st[3].score)} % del màxim possible.</section>
      <section class="kpis">
        <div><b>${f(y.co2_t_year)} t</b>CO₂ evitat per any (estimació)</div>
        <div><b>−${f(y.cost_pct, 1)} %</b>factura elèctrica</div>
        <div><b>${f(o.score, 2)}</b>puntuació oficial del repte</div>
        <div><b>${f(o.violations)}</b>infraccions físiques</div>
      </section>
      <section class="two">
        <div><h2>Decisions</h2><ol>
          <li><b>Estratègia.</b> Control predictiu amb programació lineal: cada hora planifica les 24 hores següents amb el preu i el CO₂ coneguts. Fa ${f(st[2].score, 2)} punts, igual que l'òptim teòric (${f(st[3].score, 2)}); les regles fixes per hores en fan ${f(st[1].score, 2)}.</li>
          <li><b>Horari.</b> Carrega quan la xarxa és neta (migdia i matinada) i descarrega al vespre, quan el CO₂ i el preu són alts. Es recalcula cada hora.</li>
          <li><b>Mida.</b> Amb l'inversor de 500 kW, la bateria de 2.000 kWh evita ${f(sz.find(s => s.capacity_kwh === 2000).co2_t_year)} t/any. La millor opció amb retorn de menys de 10 anys (a 350 €/kWh) és ${f(best.capacity_kwh)} kWh: ${f(best.co2_t_year)} t/any i retorn de ${f(best.payback, 1)} anys.</li>
          <li><b>Fiabilitat.</b> Amb un 50 % d'error a les previsions la puntuació passa de ${f(r[0].score, 2)} a ${f(r[r.length - 1].score, 2)}. Estalvia CO₂ totes les setmanes (entre ${f(Math.min(...m.map(x => x.co2_pct)), 1)} % i ${f(Math.max(...m.map(x => x.co2_pct)), 1)} %).</li>
        </ol></div>
        <div>${strat ? `<h2>Estratègies</h2>${strat.outerHTML}` : ""}${prof ? `<h2>Perfil horari</h2>${prof.outerHTML}` : ""}</div>
      </section>
      <section class="foot"><b>Supòsits.</b> Preu i CO₂ de les 24 hores següents coneguts; xifres anuals a partir de 12 setmanes de validació;
        rendiment del 90 % i sense degradació; cost de la bateria orientatiu. Dades: telemetria real del Campus Nord, REE i OpenStreetMap.</section>`;
  }

  window.Report = {
    open(D) {
      let el = document.getElementById("report");
      if (!el) { el = document.createElement("div"); el.id = "report"; document.body.appendChild(el); }
      el.innerHTML = build(D);
      setTimeout(() => window.print(), 300);   // deixem temps per carregar el logo
    },
  };
})();
