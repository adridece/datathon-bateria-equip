// Mode actiu (estàndard o difícil). Es tria a la barra superior i queda a l'adreça (#dificil),
// així en recarregar o compartir l'enllaç es veu el mateix mode.
(function () {
  const asked = location.hash.slice(1) || new URLSearchParams(location.search).get("mode");
  const key = asked in window.DATA_MODES ? asked : "estandard";
  const data = window.DATA_MODES[key];
  // el train es guarda un sol cop; al Mode Difícil la solar és 12 vegades més gran
  const scale = data.mode.pv_scale;
  data.train = scale === 1 ? window.TRAIN : { ...window.TRAIN, pv: window.TRAIN.pv.map(v => v * scale) };
  window.DATA = data;
  window.MODE = data.mode;
  // canviar de mode torna a carregar la pàgina: cada vista es dibuixa des de zero amb les dades del mode
  window.setMode = next => {
    location.hash = next === "estandard" ? "" : next;
    location.reload();
  };
  addEventListener("hashchange", () => {
    const now = location.hash.slice(1) || "estandard";
    if (now !== key && now in window.DATA_MODES) location.reload();
  });
})();
