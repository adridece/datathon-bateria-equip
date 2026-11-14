// Lògica de la portada: reproducció hora a hora, panells i presentació guiada.
import { createScene } from "./scene.js";

const D = window.DATA, H = D.hours;
const COLORS = { accent: "#5FD3A8", solar: "#F0B44C", charge: "#5AA9E6", discharge: "#F07B52", muted: "#8D8A83" };
const CO2_RAMP = ["#2E3439", "#5B5246", "#9C7147", "#DA9048", "#F5C46E"];
const DAYS = ["diumenge", "dilluns", "dimarts", "dimecres", "dijous", "divendres", "dissabte"];
const MONTHS = ["gener", "febrer", "març", "abril", "maig", "juny", "juliol", "agost", "setembre", "octubre", "novembre", "desembre"];
const $ = id => document.getElementById(id);
const f = (x, d = 0) => x.toLocaleString("ca-ES", { minimumFractionDigits: d, maximumFractionDigits: d });

// escala de color del CO2: de net (fosc) a brut (ambre calent)
const co2Ext = d3.extent(H.co2);
const co2Color = d3.scaleLinear().domain(d3.range(5).map(i => co2Ext[0] + i * (co2Ext[1] - co2Ext[0]) / 4))
  .range(CO2_RAMP).clamp(true);
const loadExt = d3.extent(H.load);

// ---------------------------------------------------------------- setmana activa
let week = D.weeks[0], k = week.start;
D.weeks.forEach((w, i) => {
  const [dd, mm, yy] = w.label.split("/");
  $("week").add(new Option(`Setmana del ${+dd} de ${MONTHS[+mm - 1]} de ${yy}`, i));
});

const scene = createScene($("scene"), window.CAMPUS, COLORS);

function hourState(i) {
  return { hour: +H.t[i].slice(11, 13), load: H.load[i], pv: H.pv[i], grid: H.grid[i], bat: H.bat[i], soc: H.soc[i],
           busy: (H.load[i] - loadExt[0]) / (loadExt[1] - loadExt[0]) };
}

function sumSaved(i) {
  let co2 = 0, eur = 0;
  for (let j = week.start; j <= i; j++) {
    co2 += (H.base[j] - H.grid[j]) * H.co2[j];
    eur += (H.base[j] - H.grid[j]) * H.price[j];
  }
  return { co2, eur };
}

function show(i) {
  k = Math.max(week.start, Math.min(week.end - 1, i));
  const t = new Date(H.t[k].replace(" ", "T"));
  const b = H.bat[k];
  $("time").textContent = H.t[k].slice(11, 16);
  $("date").textContent = `${DAYS[t.getDay()]} ${t.getDate()} de ${MONTHS[t.getMonth()]} de ${t.getFullYear()}`;
  $("soc").textContent = f(100 * H.soc[k]) + " %";
  $("ring").setAttribute("stroke-dashoffset", 194.8 * (1 - H.soc[k]));
  const mode = b > 1 ? ["Carregant", COLORS.charge] : b < -1 ? ["Descarregant", COLORS.discharge] : ["En espera", COLORS.muted];
  $("mode").innerHTML = `<span style="color:${mode[1]}">${mode[0]}</span> <span class="num">${b > 1 ? "+" : ""}${f(b)} kW</span>`;
  $("v-grid").textContent = f(H.grid[k]) + " kW";
  $("dot-grid").style.background = co2Color(H.co2[k]);
  $("v-load").textContent = f(H.load[k]) + " kW";
  $("v-pv").textContent = f(H.pv[k]) + " kW";
  $("v-co2").textContent = f(H.co2[k] * 1000) + " g/kWh";
  $("v-price").textContent = f(H.price[k] * 1000) + " €/MWh";
  const s = sumSaved(k);
  $("t-co2").textContent = f(s.co2) + " kg";
  $("t-eur").textContent = f(s.eur) + " €";
  $("why").textContent = H.why[k];
  $("why").style.borderLeftColor = mode[1];
  $("pos").textContent = `hora ${k - week.start + 1} de ${week.end - week.start}`;
  scene.setHour(hourState(k), co2Color(H.co2[k]));
  moveCursor();
}

// ---------------------------------------------------------------- franja de la setmana
const strip = d3.select("#strip");
let sx, cursor, sparkCursor, sparkX;
function drawStrip() {
  const w = $("strip").clientWidth, h = 58, n = week.end - week.start;
  strip.attr("viewBox", `0 0 ${w} ${h}`).selectAll("*").remove();
  sx = d3.scaleLinear().domain([week.start, week.end]).range([0, w]);
  const bw = w / n;
  const idx = d3.range(week.start, week.end);
  strip.selectAll("rect.c").data(idx).join("rect").attr("x", i => sx(i)).attr("y", 0)
    .attr("width", bw + 0.5).attr("height", 22).attr("fill", i => co2Color(H.co2[i]));
  strip.selectAll("rect.b").data(idx.filter(i => Math.abs(H.bat[i]) > 1)).join("rect")
    .attr("x", i => sx(i) + bw * 0.15).attr("width", Math.max(1, bw * 0.7))
    .attr("y", i => H.bat[i] > 0 ? 42 - 14 * H.bat[i] / 500 : 42).attr("height", i => 14 * Math.abs(H.bat[i]) / 500)
    .attr("fill", i => H.bat[i] > 0 ? COLORS.charge : COLORS.discharge);
  strip.append("line").attr("x1", 0).attr("x2", w).attr("y1", 42).attr("y2", 42).attr("stroke", "#24282C");
  idx.filter(i => H.t[i].endsWith("00:00")).forEach(i => {
    strip.append("line").attr("x1", sx(i)).attr("x2", sx(i)).attr("y1", 0).attr("y2", h).attr("stroke", "#0B0C0D").attr("stroke-width", 1.5);
    const d = new Date(H.t[i].replace(" ", "T"));
    strip.append("text").attr("x", sx(i) + 4).attr("y", 15).attr("fill", "#0B0C0D").attr("font-size", 10)
      .attr("font-family", "Plex Mono").text(`${DAYS[d.getDay()].slice(0, 2)} ${d.getDate()}`);
  });
  cursor = strip.append("rect").attr("y", 0).attr("height", h).attr("width", 2).attr("fill", "#E9E6DF");
  const drag = e => show(Math.floor(sx.invert(d3.pointer(e, $("strip"))[0])));
  strip.on("click", drag).call(d3.drag().on("drag", drag));
  drawSpark();
}

function drawSpark() {
  const svg = d3.select("#spark"), w = 248, h = 70;
  svg.selectAll("*").remove();
  const idx = d3.range(week.start, week.end);
  const x = d3.scaleLinear().domain([week.start, week.end - 1]).range([0, w]);
  const y = d3.scaleLinear().domain([0, d3.max(idx, i => Math.max(H.base[i], H.grid[i]))]).range([h - 2, 4]);
  const ln = key => d3.line().x(i => x(i)).y(i => y(H[key][i]));
  svg.append("path").attr("d", ln("base")(idx)).attr("fill", "none").attr("stroke", "#5C5A55").attr("stroke-width", 1);
  svg.append("path").attr("d", ln("grid")(idx)).attr("fill", "none").attr("stroke", COLORS.accent).attr("stroke-width", 1.2);
  sparkCursor = svg.append("line").attr("y1", 0).attr("y2", h).attr("stroke", "#E9E6DF");
  sparkX = x;
}

function moveCursor() {
  if (cursor) cursor.attr("x", sx(k) - 1);
  if (sparkCursor) sparkCursor.attr("x1", sparkX(k)).attr("x2", sparkX(k));
}

function setWeek(i) {
  week = D.weeks[i];
  drawStrip();
  show(week.start);
}
$("week").onchange = e => { stop(); setWeek(+e.target.value); };
addEventListener("resize", () => { drawStrip(); moveCursor(); });

// ---------------------------------------------------------------- reproducció
let timer = null, speed = 160;
function stop() { clearInterval(timer); timer = null; $("play").textContent = "Reproduir"; }
function start() { timer = setInterval(() => (k < week.end - 1 ? show(k + 1) : stop()), speed); $("play").textContent = "Pausa"; }
$("play").onclick = () => (timer ? stop() : start());
document.querySelectorAll("[data-speed]").forEach(b => b.onclick = () => {
  document.querySelectorAll("[data-speed]").forEach(x => x.classList.remove("on"));
  b.classList.add("on");
  speed = +b.dataset.speed;
  if (timer) { stop(); start(); }
});
const next = test => { for (let i = k + 1; i < week.end; i++) if (test(i)) return i; return k; };
$("next-charge").onclick = () => show(next(i => H.bat[i] > 1 && !(H.bat[i - 1] > 1)));
$("next-peak").onclick = () => {
  let best = Math.min(k + 1, week.end - 1);
  for (let i = k + 1; i < Math.min(week.end, k + 25); i++) if (H.co2[i] > H.co2[best]) best = i;
  show(best);
};
$("home").onclick = () => scene.flyTo(scene.views.home);

// ---------------------------------------------------------------- presentació guiada
const saved = () => sumSaved(week.end - 1);
const tour = [
  { view: "home", hour: null, text: () => `Campus Nord de la UPC: ${window.CAMPUS.buildings.length} edificis reals i un consum d'entre 1 i 2,5 MW.` },
  { view: "solar", hour: i => +H.t[i].slice(11, 13) === 13, text: () => "Les plaques solars dels aularis A cobreixen menys d'un 10 % del consum fins i tot al migdia." },
  { view: "battery", hour: i => H.bat[i] > 200, text: () => "La bateria (2 MWh, 500 kW) carrega quan l'electricitat de la xarxa és neta i barata." },
  { view: "grid", hour: i => H.bat[i] < -200, text: () => "Quan la xarxa és bruta i cara, descarrega. El color de la línia de la xarxa indica el CO₂ de cada hora." },
  { view: "home", hour: "end", text: () => `Aquesta setmana: ${f(saved().co2)} kg de CO₂ i ${f(saved().eur)} € estalviats, al màxim teòric.` },
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
  $("tour").classList.remove("on");
  scene.controls.enabled = true;
}
function runTour() {
  stop();
  window.scrollTo({ top: 0, behavior: "smooth" });
  scene.controls.enabled = false;
  $("tour").classList.add("on");
  const go = i => {
    if (i >= tour.length) { tourTimer = setTimeout(endTour, 3500); return; }
    showStep(i);
    tourTimer = setTimeout(() => go(i + 1), 6500);
  };
  go(0);
}
$("tour").onclick = () => (step >= 0 ? endTour() : runTour());
addEventListener("keydown", e => {
  if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;
  if (e.code === "Space") { e.preventDefault(); $("play").click(); }
  if (e.key === "p" || e.key === "P") $("tour").click();
  if (e.key === "Escape") endTour();
  if (step >= 0 && e.key === "ArrowRight") { clearTimeout(tourTimer); showStep(Math.min(tour.length - 1, step + 1)); }
  if (step >= 0 && e.key === "ArrowLeft") { clearTimeout(tourTimer); showStep(Math.max(0, step - 1)); }
});

// ---------------------------------------------------------------- informació en passar el ratolí
$("scene").addEventListener("pointermove", e => {
  const u = scene.pick(e.clientX, e.clientY), tip = $("tip");
  if (!u) { tip.style.display = "none"; return; }
  let html = "";
  if (u.kind === "building") {
    const b = u.info;
    html = `<b>${b.name}</b>${b.name_inferred ? " (nom deduït)" : ""}<br><span style="color:var(--muted)">${b.role || ""}</span><br>` +
           `${f(b.height_m)} m d'alçada${b.has_pv === true ? " · coberta solar" : ""}`;
  } else if (u.kind === "pv") {
    html = `<b>Plaques solars</b><br>${f(u.info.area_m2)} m² · el campus produeix ${f(H.pv[k])} kW ara`;
  } else if (u.kind === "battery") {
    html = `<b>Bateria</b> (ubicació suposada)<br>${f(100 * H.soc[k])} % · ${f(H.bat[k])} kW<br>${H.why[k]}`;
  } else if (u.kind === "grid") {
    html = `<b>Connexió a la xarxa</b> (ubicació suposada)<br>${f(H.grid[k])} kW · ${f(H.co2[k] * 1000)} g CO₂/kWh · ${f(H.price[k] * 1000)} €/MWh`;
  }
  tip.innerHTML = html;
  tip.style.display = "block";
  tip.style.left = Math.min(e.clientX + 14, innerWidth - 300) + "px";
  tip.style.top = (e.clientY + 14 + scrollY) + "px";
});

// llegenda de la rampa de CO2
d3.select("#ramp").attr("viewBox", "0 0 60 8").selectAll("rect").data(CO2_RAMP).join("rect")
  .attr("x", (_, i) => i * 12).attr("width", 12).attr("height", 8).attr("fill", c => c);

setWeek(0);
window.Charts.render(D, { co2Color });
