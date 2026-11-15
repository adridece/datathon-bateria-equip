// Mode actiu (estàndard o difícil). Es tria a la barra superior i queda a l'adreça (?mode=dificil),
// així en recarregar o compartir l'enllaç es veu el mateix mode.
(function () {
  const asked = new URLSearchParams(location.search).get("mode");
  const key = asked in window.DATA_MODES ? asked : "estandard";
  const data = window.DATA_MODES[key];
  // el train es guarda un sol cop; al Mode Difícil la solar és 12 vegades més gran
  const scale = data.mode.pv_scale;
  data.train = scale === 1 ? window.TRAIN : { ...window.TRAIN, pv: window.TRAIN.pv.map(v => v * scale) };
  window.DATA = data;
  window.MODE = data.mode;
  window.setMode = next => {
    const url = new URL(location.href);
    if (next === "estandard") url.searchParams.delete("mode");
    else url.searchParams.set("mode", next);
    location.href = url.toString();
  };
})();
