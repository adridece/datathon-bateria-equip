// Presentació guiada de tot el dashboard per a la demo davant del jurat.
(function () {
  const f = (x, d = 0) => x.toLocaleString("ca-ES", { minimumFractionDigits: d, maximumFractionDigits: d });
  let steps = [], i = -1, ui = null, go = null, after = null;

  function makeSteps(D) {
    const y = D.yearly, st = D.strategies, r = D.robustness;
    return [
      { view: "overview", sel: "#kpis", title: "La resposta en 4 xifres",
        text: `Operar la bateria amb control predictiu evita ${f(y.co2_t_year)} t de CO₂ i ${f(y.eur_year / 1000)} k€ l'any. Al test oficial fa ${f(D.official.score, 2)} punts, el màxim teòric, sense cap infracció.` },
      { view: "overview", sel: "#stage-small", title: "El Campus Nord real",
        text: "Edificis reals d'OpenStreetMap. Les partícules són l'energia: com més n'hi ha, més potència. El color de la xarxa indica el CO₂ de cada hora." },
      { view: "overview", sel: "[data-why]", title: "Cada decisió s'explica",
        text: "A cada hora l'agent diu què fa i per què: carrega quan la xarxa és neta i barata, descarrega quan és bruta i cara." },
      { view: "overview", sel: "#c-plan", title: "El pla de les properes 24 hores",
        text: "El que farà la bateria, amb el CO₂ i els euros que s'estalviaran. Es pot descarregar en CSV per a l'equip de manteniment." },
      { view: "overview", sel: "#events", title: "Avisos automàtics",
        text: "Detecta fallades del comptador, hores de consum baix i pics de CO₂. Clicant un avís, el campus va a aquella hora." },
      { view: "overview", sel: "#c-calendar", title: "Tot l'any d'un cop d'ull",
        text: "El CO₂ evitat cada dia de les 12 setmanes de validació. Funciona en totes les estacions." },
      { view: "strategy", sel: "#c-strategy", title: "Per què aquesta estratègia",
        text: `Programació lineal sobre 24 hores: ${f(st[2].score, 2)} punts, el mateix que un agent que conegués tot el futur. Les regles fixes en fan ${f(st[1].score, 2)}.` },
      { view: "planner", sel: "#v-planner .s4", title: "Què passaria si...",
        text: "Proveu escenaris: preus més alts, una reserva per a emergències o menys potència. El pla es recalcula al moment i es compara amb el de l'agent." },
      { view: "sizing", sel: "#c-size", title: "Quina bateria comprar",
        text: "Amb l'inversor actual, més enllà de 4 hores de capacitat ja no compensa. La taula diu en quants anys es recupera cada opció." },
      { view: "trust", sel: "#c-robust", title: "Ens en podem refiar",
        text: `Amb un 50 % d'error a les previsions la puntuació només baixa de ${f(r[0].score, 2)} a ${f(r[r.length - 1].score, 2)}.` },
      { view: "live", sel: "#stage-big", title: "I ara, en directe",
        text: "Comencem la presentació del campus en 3D.", end: true },
    ];
  }

  function build() {
    ui = document.createElement("div");
    ui.className = "demo";
    ui.innerHTML = `<div class="demo-spot"></div><div class="demo-card"><div class="demo-n"></div><h3></h3><p></p>
      <div class="demo-btns"><button data-d="exit">Sortir</button><span></span><button data-d="prev">Anterior</button><button class="primary" data-d="next">Següent</button></div></div>`;
    document.body.appendChild(ui);
    ui.addEventListener("click", e => {
      const b = e.target.closest("[data-d]");
      if (!b) return;
      if (b.dataset.d === "next") show(i + 1);
      if (b.dataset.d === "prev") show(i - 1);
      if (b.dataset.d === "exit") stop();
    });
  }

  function place(el) {
    const r = el.getBoundingClientRect(), pad = 10;
    const spot = ui.querySelector(".demo-spot"), card = ui.querySelector(".demo-card");
    Object.assign(spot.style, { left: r.left - pad + "px", top: r.top - pad + "px", width: r.width + 2 * pad + "px", height: r.height + 2 * pad + "px" });
    // la targeta de text va on hi ha més espai: sota, a sobre o al costat
    const cw = 380, below = innerHeight - r.bottom > 230;
    const left = Math.min(Math.max(16, r.left), innerWidth - cw - 16);
    const top = below ? r.bottom + 22 : Math.max(16, r.top - 22 - card.offsetHeight);
    Object.assign(card.style, { left: left + "px", top: top + "px", width: cw + "px" });
  }

  function show(n) {
    if (n < 0) return;
    if (n >= steps.length) { stop(); return; }
    i = n;
    const s = steps[i];
    go(s.view);
    ui.querySelector(".demo-n").textContent = `${i + 1} de ${steps.length}`;
    ui.querySelector("h3").textContent = s.title;
    ui.querySelector("p").textContent = s.text;
    ui.querySelector('[data-d="next"]').textContent = s.end ? "Començar" : "Següent";
    setTimeout(() => {
      const el = document.querySelector(s.sel);
      if (!el) return;
      el.scrollIntoView({ block: "center", behavior: "smooth" });
      setTimeout(() => place(el), 450);
    }, 380);
    if (s.end) ui.querySelector('[data-d="next"]').onclick = () => { stop(); after && after(); };
    else ui.querySelector('[data-d="next"]').onclick = null;
  }

  function stop() {
    i = -1;
    if (ui) ui.classList.remove("on");
  }

  window.Demo = {
    start(D, goTo, onEnd) {
      steps = makeSteps(D);
      go = goTo;
      after = onEnd;
      if (!ui) build();
      ui.classList.add("on");
      show(0);
    },
    key(e) {
      if (i < 0) return false;
      if (e.key === "ArrowRight") show(i + 1);
      else if (e.key === "ArrowLeft") show(i - 1);
      else if (e.key === "Escape") stop();
      else return false;
      return true;
    },
    resize() { if (i >= 0) { const el = document.querySelector(steps[i].sel); if (el) place(el); } },
  };
})();
