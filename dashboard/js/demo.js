// Presentació guiada per a la demo davant del jurat: portada, recorregut per les vistes i resum final.
(function () {
  const f = (x, d = 0) => x.toLocaleString("ca-ES", { minimumFractionDigits: d, maximumFractionDigits: d });
  let steps = [], i = -1, ui = null, go = null, after = null, D = null;

  function makeSteps() {
    const y = D.yearly, st = D.strategies, r = D.robustness;
    return [
      { view: "overview", sel: "#kpis", title: "La resposta en quatre xifres",
        text: `Amb control predictiu, la bateria evita ${f(y.co2_t_year)} t de CO₂ i ${f(y.eur_year / 1000)} k€ l'any. Al test públic fa ${f(D.official.score, 2)} punts sense cap infracció.` },
      { view: "overview", sel: "#stage-small", title: "El Campus Nord, edifici a edifici",
        text: "Edificis reals. Les partícules són l'energia que circula: solar en taronja, xarxa en el color del seu CO₂, bateria en blau quan carrega i vermelló quan descarrega." },
      { view: "overview", sel: ".battery-now", title: "Cada decisió té un perquè",
        text: "L'estat de la bateria i la frase que explica què fa i per què, hora a hora." },
      { view: "overview", sel: "#c-plan", title: "Què farà demà",
        text: "El pla de les properes 24 hores amb l'estalvi previst. Es pot descarregar en CSV." },
      { view: "overview", sel: "#events", title: "Avisos que porten a l'hora exacta",
        text: "Fallades del comptador, consum baix, pics de CO₂. Un clic i el campus va a aquell moment." },
      { view: "strategy", sel: "#c-strategy", title: "Per què aquesta estratègia",
        text: `Programació lineal sobre 24 hores: ${f(st[2].score, 2)} punts, el mateix que un agent que conegués tot el futur. Les regles fixes en fan ${f(st[1].score, 2)}.` },
      { view: "planner", sel: "#v-planner .s4", title: "Què passaria si...",
        text: "Preus més alts, una reserva per a emergències, menys potència. El pla es recalcula al moment i es compara amb el de l'agent." },
      { view: "sizing", sel: "#c-size", title: "Quina bateria comprar",
        text: "Amb l'inversor actual, més enllà de 4 hores de capacitat ja no compensa. La taula diu quan es recupera cada opció." },
      { view: "trust", sel: "#c-robust", title: "Ens en podem refiar",
        text: `Amb un 50 % d'error a les previsions la puntuació només passa de ${f(r[0].score, 2)} a ${f(r[r.length - 1].score, 2)}.` },
    ];
  }

  function build() {
    ui = document.createElement("div");
    ui.className = "demo";
    ui.innerHTML = `
      <div class="demo-cover">
        <div class="demo-cover-in">
          <img src="static/logo-datathon.png" alt=""><div class="demo-team">LA DATONETA</div>
          <h2>Una bateria que decideix sola quan l'electricitat és neta</h2>
          <p class="demo-sub">Campus Nord de la UPC, 2 MWh i 500 kW</p>
          <div class="demo-figs"></div>
          <div class="demo-btns center"><button data-d="exit">Tancar</button><button class="primary" data-d="next">Començar</button></div>
        </div>
      </div>
      <div class="demo-spot"></div>
      <div class="demo-card">
        <div class="demo-bar"><span></span></div>
        <div class="demo-n"></div><h3></h3><p></p>
        <div class="demo-btns"><button data-d="exit">Sortir</button><span></span><button data-d="prev">Anterior</button><button class="primary" data-d="next">Següent</button></div>
      </div>`;
    document.body.appendChild(ui);
    ui.addEventListener("click", e => {
      const b = e.target.closest("[data-d]");
      if (!b) return;
      if (b.dataset.d === "next") show(i + 1);
      if (b.dataset.d === "prev") show(i - 1);
      if (b.dataset.d === "exit") stop();
      if (b.dataset.d === "live") { stop(); after && after(); }
    });
  }

  function cover(final) {
    const y = D.yearly;
    ui.classList.add("cover");
    ui.querySelector("h2").textContent = final ? "En resum" : "Una bateria que decideix sola quan l'electricitat és neta";
    ui.querySelector(".demo-sub").textContent = final
      ? "Control predictiu, al màxim teòric, robust i llest per decidir quina bateria comprar."
      : "Campus Nord de la UPC, 2 MWh i 500 kW";
    ui.querySelector(".demo-figs").innerHTML =
      `<div><b>${f(y.co2_t_year)} t</b>CO₂ evitat per any</div><div><b>${f(y.eur_year / 1000)} k€</b>estalvi per any</div>` +
      `<div><b>${f(D.official.score, 2)}</b>punts al test públic</div>`;
    ui.querySelector(".demo-cover .demo-btns").innerHTML = final
      ? `<button data-d="exit">Tancar</button><button class="primary" data-d="live">Veure el campus en directe</button>`
      : `<button data-d="exit">Tancar</button><button class="primary" data-d="next">Començar</button>`;
  }

  function place(el) {
    const r = el.getBoundingClientRect(), pad = 10;
    const spot = ui.querySelector(".demo-spot"), card = ui.querySelector(".demo-card");
    Object.assign(spot.style, { left: r.left - pad + "px", top: r.top - pad + "px", width: r.width + 2 * pad + "px", height: r.height + 2 * pad + "px" });
    // el text va on hi ha més espai: a sota, a sobre o al costat
    const cw = 400, ch = card.offsetHeight || 200;
    let left = Math.min(Math.max(16, r.left), innerWidth - cw - 16), top;
    if (innerHeight - r.bottom > ch + 40) top = r.bottom + 24;
    else if (r.top > ch + 40) top = r.top - ch - 24;
    else { top = Math.max(16, (innerHeight - ch) / 2); left = r.right + cw + 40 < innerWidth ? r.right + 24 : Math.max(16, r.left - cw - 24); }
    Object.assign(card.style, { left: left + "px", top: top + "px", width: cw + "px" });
    ui.classList.add("ready");
  }

  function show(n) {
    if (n < 0) { i = -1; cover(false); return; }
    if (n >= steps.length) { i = steps.length; ui.classList.remove("ready"); cover(true); return; }
    i = n;
    ui.classList.remove("cover", "ready");
    const s = steps[i];
    go(s.view);
    ui.querySelector(".demo-bar span").style.width = (100 * (i + 1) / steps.length) + "%";
    ui.querySelector(".demo-n").textContent = `${i + 1} de ${steps.length}`;
    ui.querySelector("h3").textContent = s.title;
    ui.querySelector(".demo-card p").textContent = s.text;
    // esperem que la vista estigui quieta abans de ressaltar
    setTimeout(() => {
      const el = document.querySelector(s.sel);
      if (!el) return;
      el.scrollIntoView({ block: "center", behavior: "smooth" });
      setTimeout(() => place(el), 500);
    }, 450);
  }

  function stop() {
    i = -1;
    if (ui) ui.classList.remove("on", "cover", "ready");
    document.body.classList.remove("demo-on");
  }

  window.Demo = {
    start(data, goTo, onEnd) {
      D = data; steps = makeSteps(); go = goTo; after = onEnd;
      if (!ui) build();
      document.body.classList.add("demo-on");
      ui.classList.add("on");
      i = -1;
      cover(false);
    },
    key(e) {
      if (!ui || !ui.classList.contains("on")) return false;
      if (e.key === "ArrowRight" || e.key === "Enter") show(i + 1);
      else if (e.key === "ArrowLeft") show(i - 1);
      else if (e.key === "Escape") stop();
      else return false;
      return true;
    },
    resize() { if (i >= 0 && i < steps.length) { const el = document.querySelector(steps[i].sel); if (el) place(el); } },
  };
})();
