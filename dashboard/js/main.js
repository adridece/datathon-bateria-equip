// Lògica de l'app: navegació, reproducció hora a hora, panell de la bateria i presentació guiada.
import { createScene } from "./scene.js";

const D = window.DATA, H = D.hours;
const COLORS = { accent: "#0F7A62", solar: "#E69F00", charge: "#0072B2", discharge: "#D55E00", muted: "#6E6A63" };
const CO2_RAMP = ["#C9D6CF", "#C9B48A", "#A9824F", "#7A5532", "#4A3220"];
const DAYS = ["dg", "dl", "dt", "dc", "dj", "dv", "ds"];
const MONTHS = ["gener", "febrer", "març", "abril", "maig", "juny", "juliol", "agost", "setembre", "octubre", "novembre", "desembre"];
const $ = id => document.getElementById(id);
const all = sel => document.querySelectorAll(sel);
const f = (x, d = 0) => x.toLocaleString("ca-ES", { minimumFractionDigits: d, maximumFractionDigits: d });

const co2Ext = d3.extent(H.co2);
const co2Color = d3.scaleLinear().domain(d3.range(5).map(i => co2Ext[0] + i * (co2Ext[1] - co2Ext[0]) / 4)).range(CO2_RAMP).clamp(true);
const loadExt = d3.extent(H.load);

// ---------------------------------------------------------------- vistes
const VIEWS = {
  overview: ["Visió general", "Com està anant la bateria i què decideix a cada hora"],
  live: ["Campus en directe", "El Campus Nord real en 3D, hora a hora"],
  strategy: ["Estratègia", "Com s'ha de controlar la bateria i per què"],
  sizing: ["Mida de la bateria", "Quina bateria li convé comprar a la UPC"],
  trust: ["Fiabilitat", "Fins a quin punt ens en podem refiar"],
};
let scene;
function go(name) {
  all(".nav button").forEach(b => b.classList.toggle("on", b.dataset.view === name));
  all(".view").forEach(v => v.classList.toggle("on", v.id === "v-" + name));
  $("title").textContent = VIEWS[name][0];
  $("subtitle").textContent = VIEWS[name][1];
  if (name === "overview") scene.mount($("stage-small"));
  if (name === "live") { scene.mount($("stage-big")); drawStrip(); }
  window.Charts.show(name);
}
all(".nav button").forEach(b => b.onclick = () => go(b.dataset.view));

// ---------------------------------------------------------------- reproductor (es repeteix a cada vista amb 3D)
const PLAYER = `<button class="primary" data-act="play">Reproduir</button>
  <span class="seg"><button data-speed="600">1×</button><button data-speed="160" class="on">4×</button><button data-speed="45">16×</button></span>
  <button data-act="charge">Propera càrrega</button><button data-act="peak">Pic de CO₂</button>
  <button data-act="tour">Presentació guiada</button><button data-act="home">Vista inicial</button>
  <span class="pos num" data-pos></span>`;
all("[data-player]").forEach(p => (p.innerHTML = PLAYER));

// ---------------------------------------------------------------- setmana i hora actual
let week = D.weeks[0], k = week.start;
D.weeks.forEach((w, i) => {
  const [dd, mm, yy] = w.label.split("/");
  $("week").add(new Option(`Setmana del ${+dd} de ${MONTHS[+mm - 1]} ${yy}`, i));
});

function savedUntil(i) {
  let co2 = 0, eur = 0;
  for (let j = week.start; j <= i; j++) {
    co2 += (H.base[j] - H.grid[j]) * H.co2[j];
    eur += (H.base[j] - H.grid[j]) * H.price[j];
  }
  return { co2, eur };
}

const setAll = (sel, fn) => all(sel).forEach(fn);
function show(i) {
  k = Math.max(week.start, Math.min(week.end - 1, i));
  const t = new Date(H.t[k].replace(" ", "T"));
  const b = H.bat[k];
  const mode = b > 1 ? ["Carregant", COLORS.charge] : b < -1 ? ["Descarregant", COLORS.discharge] : ["En espera", COLORS.muted];
  $("chip-time").textContent = `${DAYS[t.getDay()]} ${t.getDate()}/${t.getMonth() + 1} · ${H.t[k].slice(11, 16)}`;
  setAll("[data-soc]", e => (e.textContent = f(100 * H.soc[k]) + " %"));
  setAll(".ring", e => e.setAttribute("stroke-dashoffset", 238.8 * (1 - H.soc[k])));
  setAll("[data-mode]", e => (e.innerHTML = `<i style="width:8px;height:8px;border-radius:50%;background:${mode[1]}"></i>${mode[0]} · <span class="num">${b > 1 ? "+" : ""}${f(b)} kW</span>`));
  setAll("[data-grid]", e => (e.textContent = f(H.grid[k]) + " kW"));
  setAll("[data-dot-grid]", e => (e.style.background = co2Color(H.co2[k])));
  setAll("[data-load]", e => (e.textContent = f(H.load[k]) + " kW"));
  setAll("[data-pv]", e => (e.textContent = f(H.pv[k]) + " kW"));
  setAll("[data-co2]", e => (e.textContent = f(H.co2[k] * 1000) + " g/kWh"));
  setAll("[data-price]", e => (e.textContent = f(H.price[k] * 1000) + " €/MWh"));
  setAll("[data-why]", e => (e.textContent = H.why[k]));
  setAll("[data-pos]", e => (e.textContent = `hora ${k - week.start + 1} de ${week.end - week.start}`));
  scene.setHour({ hour: +H.t[k].slice(11, 13), load: H.load[k], pv: H.pv[k], grid: H.grid[k], bat: b, soc: H.soc[k],
                  busy: (H.load[k] - loadExt[0]) / (loadExt[1] - loadExt[0]) }, co2Color(H.co2[k]));
  if (cursor) cursor.attr("x", sx(k) - 1.5);
}

// ---------------------------------------------------------------- franja de la setmana (vista 3D)
let sx, cursor;
function drawStrip() {
  const svg = d3.select("#strip"), w = $("strip").clientWidth, h = 54;
  if (!w) return;
  svg.attr("viewBox", `0 0 ${w} ${h}`).selectAll("*").remove();
  sx = d3.scaleLinear().domain([week.start, week.end]).range([0, w]);
  const bw = w / (week.end - week.start), idx = d3.range(week.start, week.end);
  svg.append("rect").attr("width", w).attr("height", h).attr("rx", 10).attr("fill", "#F7F5F1");
  svg.selectAll("rect.c").data(idx).join("rect").attr("x", i => sx(i)).attr("y", 0).attr("width", bw + 0.5).attr("height", 22).attr("fill", i => co2Color(H.co2[i]));
  svg.selectAll("rect.b").data(idx.filter(i => Math.abs(H.bat[i]) > 1)).join("rect")
    .attr("x", i => sx(i) + bw * 0.15).attr("width", Math.max(1, bw * 0.7)).attr("rx", 1)
    .attr("y", i => (H.bat[i] > 0 ? 40 - 13 * H.bat[i] / 500 : 40)).attr("height", i => 13 * Math.abs(H.bat[i]) / 500)
    .attr("fill", i => (H.bat[i] > 0 ? COLORS.charge : COLORS.discharge));
  idx.filter(i => H.t[i].endsWith("00:00")).forEach(i => {
    const d = new Date(H.t[i].replace(" ", "T"));
    svg.append("line").attr("x1", sx(i)).attr("x2", sx(i)).attr("y1", 0).attr("y2", h).attr("stroke", "#fff").attr("stroke-width", 2);
    svg.append("text").attr("x", sx(i) + 5).attr("y", 15).attr("fill", "#fff").attr("font-size", 10).attr("font-weight", 600).text(`${DAYS[d.getDay()]} ${d.getDate()}`);
  });
  cursor = svg.append("rect").attr("y", 0).attr("height", h).attr("width", 3).attr("rx", 1.5).attr("fill", "#1F2326");
  const move = e => show(Math.floor(sx.invert(d3.pointer(e, $("strip"))[0])));
  svg.on("click", move).call(d3.drag().on("drag", move));
  cursor.attr("x", sx(k) - 1.5);
}
addEventListener("resize", drawStrip);

function setWeek(i) {
  week = D.weeks[i];
  drawStrip();
  show(week.start + 12);
}
$("week").onchange = e => { stop(); setWeek(+e.target.value); };

// ---------------------------------------------------------------- reproducció
let timer = null, speed = 160;
function stop() { clearInterval(timer); timer = null; setAll("[data-act=play]", b => (b.textContent = "Reproduir")); }
function start() { timer = setInterval(() => (k < week.end - 1 ? show(k + 1) : stop()), speed); setAll("[data-act=play]", b => (b.textContent = "Pausa")); }
const next = test => { for (let i = k + 1; i < week.end; i++) if (test(i)) return i; return k; };
document.addEventListener("click", e => {
  const b = e.target.closest("[data-act],[data-speed]");
  if (!b) return;
  if (b.dataset.speed) {
    speed = +b.dataset.speed;
    setAll("[data-speed]", x => x.classList.toggle("on", +x.dataset.speed === speed));
    if (timer) { stop(); start(); }
    return;
  }
  const act = b.dataset.act;
  if (act === "play") timer ? stop() : start();
  if (act === "charge") show(next(i => H.bat[i] > 1 && !(H.bat[i - 1] > 1)));
  if (act === "peak") {
    let best = Math.min(k + 1, week.end - 1);
    for (let i = k + 1; i < Math.min(week.end, k + 25); i++) if (H.co2[i] > H.co2[best]) best = i;
    show(best);
  }
  if (act === "home") scene.flyTo(scene.views.home);
  if (act === "tour") step >= 0 ? endTour() : runTour();
});

// ---------------------------------------------------------------- presentació guiada
const tour = [
  { view: "home", hour: null, text: () => `Campus Nord de la UPC: ${window.CAMPUS.buildings.length} edificis reals i un consum d'entre 1 i 2,5 MW.` },
  { view: "solar", hour: i => +H.t[i].slice(11, 13) === 13, text: () => "Les plaques solars dels aularis A cobreixen menys d'un 10 % del consum, fins i tot al migdia." },
  { view: "battery", hour: i => H.bat[i] > 200, text: () => "La bateria (2 MWh, 500 kW) carrega quan l'electricitat de la xarxa és neta i barata." },
  { view: "grid", hour: i => H.bat[i] < -200, text: () => "Quan la xarxa és bruta i cara, descarrega. El color de la línia de la xarxa indica el CO₂ de cada hora." },
  { view: "home", hour: "end", text: () => { const s = savedUntil(week.end - 1); return `Aquesta setmana: ${f(s.co2)} kg de CO₂ i ${f(s.eur)} € estalviats.`; } },
];
let step = -1, tourTimer = null;
function showStep(i) {
  step = i;
  const s = tour[i];
  scene.flyTo(scene.views[s.view]);
  if (s.hour === "end") show(week.end - 1);
  else if (s.hour) show(next(s.hour));
  const c = $("caption");
  c.style.opacity = 0;
  setTimeout(() => { c.textContent = s.text(); c.style.opacity = 1; }, 350);
}
function endTour() {
  clearTimeout(tourTimer);
  step = -1;
  $("caption").style.opacity = 0;
  setAll("[data-act=tour]", b => b.classList.remove("on"));
  scene.controls.enabled = true;
}
function runTour() {
  stop();
  go("live");
  scene.controls.enabled = false;
  setAll("[data-act=tour]", b => b.classList.add("on"));
  const run = i => {
    if (i >= tour.length) { tourTimer = setTimeout(endTour, 3500); return; }
    showStep(i);
    tourTimer = setTimeout(() => run(i + 1), 6500);
  };
  run(0);
}
addEventListener("keydown", e => {
  if (["INPUT", "SELECT"].includes(e.target.tagName)) return;
  if (e.code === "Space") { e.preventDefault(); timer ? stop() : start(); }
  if (e.key === "p" || e.key === "P") step >= 0 ? endTour() : runTour();
  if (e.key === "Escape") endTour();
  if (step >= 0 && e.key === "ArrowRight") { clearTimeout(tourTimer); showStep(Math.min(tour.length - 1, step + 1)); }
  if (step >= 0 && e.key === "ArrowLeft") { clearTimeout(tourTimer); showStep(Math.max(0, step - 1)); }
});

// ---------------------------------------------------------------- informació en passar el ratolí pel 3D
document.addEventListener("pointermove", e => {
  const tip = $("tip");
  if (!e.target.closest(".stage") || e.target.tagName !== "CANVAS") { tip.style.display = "none"; return; }
  const u = scene.pick(e.clientX, e.clientY);
  if (!u) { tip.style.display = "none"; return; }
  let html = "";
  if (u.kind === "building") {
    const b = u.info;
    html = `<b>${b.name}</b>${b.name_inferred ? " (nom deduït)" : ""}<br>${b.role || ""}<br>${f(b.height_m)} m d'alçada${b.has_pv === true ? " · coberta solar" : ""}`;
  } else if (u.kind === "pv") html = `<b>Plaques solars</b><br>${f(u.info.area_m2)} m² · el campus produeix ${f(H.pv[k])} kW ara`;
  else if (u.kind === "battery") html = `<b>Bateria</b> (ubicació suposada)<br>${f(100 * H.soc[k])} % · ${f(H.bat[k])} kW<br>${H.why[k]}`;
  else if (u.kind === "grid") html = `<b>Connexió a la xarxa</b> (ubicació suposada)<br>${f(H.grid[k])} kW · ${f(H.co2[k] * 1000)} g CO₂/kWh`;
  tip.innerHTML = html;
  tip.style.display = "block";
  tip.style.left = Math.min(e.clientX + 14, innerWidth - 300) + "px";
  tip.style.top = e.clientY + 14 + "px";
});

d3.select("#ramp").attr("viewBox", "0 0 56 8").selectAll("rect").data(CO2_RAMP).join("rect")
  .attr("x", (_, i) => i * 11.2).attr("width", 11.6).attr("height", 8).attr("fill", c => c);
$("chip-score").textContent = f(D.official.score, 2);

scene = createScene($("stage-small"), window.CAMPUS, COLORS);
window.Charts.init(D, { co2Color });
setWeek(0);
go("overview");
