// Lògica de l'app: navegació, reproducció hora a hora, panell de la bateria i presentació guiada.
import { createScene } from "./scene.js";

const D = window.DATA, H = D.hours;
const COLORS = { accent: "#47908B", solar: "#E69F00", charge: "#0072B2", discharge: "#D55E00", muted: "#6E6A63" };
const CO2_RAMP = ["#C9D6CF", "#C9B48A", "#A9824F", "#7A5532", "#4A3220"];
const DAYS = ["dg", "dl", "dt", "dc", "dj", "dv", "ds"];
const MONTHS = ["gener", "febrer", "març", "abril", "maig", "juny", "juliol", "agost", "setembre", "octubre", "novembre", "desembre"];
const $ = id => document.getElementById(id);
const all = sel => document.querySelectorAll(sel);
const statsHTML = items => items.map(([label, value]) => `<div><span>${label}</span><b class="num">${value}</b></div>`).join("");
const f = (x, d = 0) => x.toLocaleString("ca-ES", { minimumFractionDigits: d, maximumFractionDigits: d });

const co2Ext = d3.extent(H.co2);
const co2Color = d3.scaleLinear().domain(d3.range(5).map(i => co2Ext[0] + i * (co2Ext[1] - co2Ext[0]) / 4)).range(CO2_RAMP).clamp(true);
const loadExt = d3.extent(H.load);

// ---------------------------------------------------------------- vistes
const VIEWS = {
  live: ["En directe", "Què fa la bateria del Campus Nord ara mateix i per què"],
  overview: ["Decisions", "Què convé fer, amb l'impacte i l'evidència de cada decisió"],
  trust: ["Històric", "Com ha funcionat la bateria setmana a setmana i dia a dia"],
  strategy: ["Anàlisi", "Quan i per què convé carregar i descarregar"],
  planner: ["Simulador", "Què passaria si canvien el preu, el CO₂ o les condicions de la bateria"],
  sizing: ["Inversió", "Quanta bateria convé tenir i quan es recupera la inversió"],
};
let scene;
function go(name) {
  all(".nav button").forEach(b => b.classList.toggle("on", b.dataset.view === name));
  all(".view").forEach(v => v.classList.toggle("on", v.id === "v-" + name));
  $("v-" + name).scrollTop = 0;
  document.querySelectorAll(".stage.expanded").forEach(s => toggleExpand(s, false));
  $("title").textContent = VIEWS[name][0];
  $("subtitle").textContent = VIEWS[name][1];
  if (name === "trust") setTimeout(drawCalendar, 60);
  if (name === "live") { scene.mount($("stage-big")); drawStrip(); setTimeout(() => { drawStrip(); drawPlan(); window.Explorer.drawLive(); }, 450); }
  if (name === "trust") setTimeout(() => window.Explorer.draw(), 80);   // es torna a dibuixar quan la vista ja és oberta
  window.Charts.show(name);
  if (name === "planner") stop();   // l'escenari no s'ha de moure mentre es prova
  if (name === "planner") setTimeout(() => window.Planner.update({ H, k, co2Color }), 30);
}
all(".nav button").forEach(b => b.onclick = () => go(b.dataset.view));

// ---------------------------------------------------------------- reproductor (es repeteix a cada vista amb 3D)
const PLAYER = `<button class="primary" data-act="play">Reproduir</button>
  <span class="seg"><button data-speed="0.4">Lent</button><button data-speed="1.2" class="on">Normal</button><button data-speed="4">Ràpid</button></span>
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
function show(i, fromPlayer) {
  k = Math.max(week.start, Math.min(week.end - 1, i));
  if (!fromPlayer) clock = k;
  const t = new Date(H.t[k].replace(" ", "T"));
  const b = H.bat[k];
  const mode = b > 1 ? ["Carregant", COLORS.charge] : b < -1 ? ["Descarregant", COLORS.discharge] : ["En espera", COLORS.muted];
  $("chip-time").textContent = `${DAYS[t.getDay()]} ${t.getDate()}/${t.getMonth() + 1}, ${H.t[k].slice(11, 16)} h`;
  setAll("[data-mode]", e => (e.innerHTML = `<i style="width:8px;height:8px;border-radius:50%;background:${mode[1]}"></i>${mode[0]} <span class="num">${b > 1 ? "+" : ""}${f(b)} kW</span>`));
  setAll("[data-why]", e => (e.textContent = H.why[k]));
  liveNumbers(fromPlayer ? clock : k);
  drawClock();
  signal();
  const sv = savedUntil(k);
  setAll("[data-saved]", e => (e.innerHTML = `${f(sv.co2)} kg CO₂<br>${f(sv.eur)} €`));
  setAll("[data-clock]", e => (e.textContent = $("chip-time").textContent));
  setAll("[data-pos]", e => (e.textContent = `hora ${k - week.start + 1} de ${week.end - week.start}`));
  setAll("[data-cycles]", e => (e.textContent = f(weekCycles(), 1)));
  sceneAt(k);
  window.Explorer.setNow(k);
  drawPlan();
  window.Planner.update({ H, k, co2Color });
  if (cursor) cursor.attr("x", sx(k) - 1.5);
}

// ---------------------------------------------------------------- franja de la setmana (vista 3D)
let sx, cursor;
function drawStrip() {
  const svg = d3.select("#strip"), w = $("strip").clientWidth, h = 54;
  if (!w) return;
  svg.attr("viewBox", `0 0 ${w} ${h}`).attr("preserveAspectRatio", "none").selectAll("*").remove();
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
  $("week").value = i;
  syncWeekPicker();
  clockDay = -1;
  Charts.setWeek(week);
  drawStrip();
  events();
  show(week.start);
}
$("week").onchange = e => { stop(); setWeek(+e.target.value); };

// ---------------------------------------------------------------- selector de setmanes propi
// el <select> natiu es veu diferent a cada sistema; aquest es veu igual a Mac, Windows i Linux
const wkBtn = document.querySelector(".wk-btn"), wkList = document.querySelector(".wk-list");
wkList.innerHTML = [...$("week").options].map((o, i) => `<li role="option" tabindex="-1" data-wk="${i}">
  <span>${o.text}</span><b class="num">${f(D.weekly[i].co2_kg)} kg</b></li>`).join("");
function syncWeekPicker() {
  $("wk-label").textContent = $("week").selectedOptions[0]?.text || "";
  wkList.querySelectorAll("li").forEach(li => li.setAttribute("aria-selected", li.dataset.wk === $("week").value));
}
function openWeeks(open) {
  wkList.hidden = !open;
  wkBtn.setAttribute("aria-expanded", open);
  if (open) (wkList.querySelector('[aria-selected="true"]') || wkList.firstElementChild).focus();
}
function pickWeek(i) {
  $("week").value = i;
  $("week").dispatchEvent(new Event("change"));
  openWeeks(false);
  wkBtn.focus();
}
wkBtn.onclick = () => openWeeks(wkList.hidden);
wkList.onclick = e => { const li = e.target.closest("li"); if (li) pickWeek(li.dataset.wk); };
wkList.onkeydown = e => {
  const li = document.activeElement.closest("li");
  if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); (e.key === "ArrowDown" ? li?.nextElementSibling : li?.previousElementSibling)?.focus(); }
  if (e.key === "Enter" && li) pickWeek(li.dataset.wk);
  if (e.key === "Escape") { openWeeks(false); wkBtn.focus(); }
  e.stopPropagation();
};
document.addEventListener("click", e => { if (!e.target.closest("#wkpick")) openWeeks(false); });

// ---------------------------------------------------------------- mapa ampliat
// fem servir una capa pròpia (no la pantalla completa del navegador), així funciona igual a tot arreu
const ICON_EXPAND = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg>';
const ICON_CLOSE = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>';
function toggleExpand(stage, force) {
  const on = force ?? !stage.classList.contains("expanded");
  if (on && !stage._home) {
    // el traiem de la targeta i el posem sobre tota la pàgina; en tancar torna al seu lloc
    stage._home = { parent: stage.parentNode, next: stage.nextSibling };
    document.body.appendChild(stage);
  } else if (!on && stage._home) {
    stage._home.parent.insertBefore(stage, stage._home.next);
    stage._home = null;
  }
  stage.classList.toggle("expanded", on);
  document.body.classList.toggle("has-expanded", on);
  stage.querySelector('[data-act="full"]').innerHTML = on ? ICON_CLOSE : ICON_EXPAND;
  stage.querySelector('[data-act="full"]').setAttribute("aria-label", on ? "Tancar el mapa ampliat" : "Ampliar el mapa");
  scene.controls.enableZoom = on || stage.id === "stage-big";
  // pantalla completa de debò (Safari fa servir el prefix webkit)
  const fs = document.fullscreenElement || document.webkitFullscreenElement;
  if (on && !fs) {
    const req = stage.requestFullscreen || stage.webkitRequestFullscreen;
    if (req) { const r = req.call(stage); if (r && r.catch) r.catch(() => {}); }
  } else if (!on && fs) {
    (document.exitFullscreen || document.webkitExitFullscreen).call(document);
  }
}
// si se surt de la pantalla completa amb Esc del navegador, el mapa torna a la seva targeta
["fullscreenchange", "webkitfullscreenchange"].forEach(ev => document.addEventListener(ev, () => {
  if (!(document.fullscreenElement || document.webkitFullscreenElement))
    document.querySelectorAll(".stage.expanded").forEach(s => toggleExpand(s, false));
}));

// ---------------------------------------------------------------- cicles de la bateria
// un cicle = descarregar l'equivalent a tota la capacitat (2.000 kWh); serveix per vigilar el desgast
function weekCycles() {
  let out = 0;
  for (let i = week.start; i < week.end; i++) out += Math.max(0, -H.bat[i]);
  return out / 2000;
}

// ---------------------------------------------------------------- pla de les properes 24 h
function next24() { return d3.range(k, Math.min(k + 24, week.end)); }
// incertesa: refem el pla amb previsions amb error i mirem quantes vegades es manté la decisió de cada hora
const agreeCache = new Map();
function planAgreement(idx) {
  if (agreeCache.has(k)) return agreeCache.get(k);
  // mateix model d'error que a Fiabilitat: l'hora actual es coneix i l'error creix com més lluny mirem
  const N = 20, rnd = d3.randomNormal.source(d3.randomLcg(0.42))(0, 1);
  const err = j => 1 + 0.2 * Math.sqrt(j / 23) * rnd();
  const net = idx.map(i => Math.max(0, H.load[i] - H.pv[i]));
  const soc0 = (k > 0 ? H.soc[k - 1] : 0.5) * 2000;
  const kind = p => (p > 20 ? 1 : p < -20 ? -1 : 0);
  const hits = idx.map(() => 0);
  for (let s = 0; s < N; s++) {
    const w = idx.map((i, j) => 0.7 * H.co2[i] * err(j) / 0.0921 + 0.3 * H.price[i] * err(j) / 0.1568);
    window.Planner.solve(w, net, soc0, 500, 0, H.soc[idx[idx.length - 1]] * 2000).plan.forEach((p, j) => { if (kind(p) === kind(H.bat[idx[j]])) hits[j]++; });
  }
  const out = hits.map(h => h / N);
  agreeCache.set(k, out);
  return out;
}
function drawPlan() {
  const el = $("c-plan");
  if (!el || !el.clientWidth) return;
  const idx = next24();
  let co2 = 0, eur = 0, cin = 0, cout = 0;
  idx.forEach(i => {
    co2 += (H.base[i] - H.grid[i]) * H.co2[i];
    eur += (H.base[i] - H.grid[i]) * H.price[i];
    cin += Math.max(0, H.bat[i]);
    cout += Math.max(0, -H.bat[i]);
  });
  $("plan-sum").innerHTML = `<div><b class="good">${f(co2)} kg</b>CO₂ evitat</div><div><b class="good">${f(eur)} €</b>estalviats</div>` +
    `<div><b>${f(cin)} kWh</b>carregats</div><div><b>${f(cout)} kWh</b>descarregats</div>`;

  const w = el.clientWidth, h = 240, m = { t: 8, r: 46, b: 92, l: 40 };
  const iw = w - m.l - m.r, ih = h - m.t - m.b;
  el.innerHTML = "";
  const svg = d3.select(el).append("svg").attr("viewBox", `0 0 ${w} ${h}`).attr("width", "100%");
  const g = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);
  const x = d3.scaleBand().domain(idx).range([0, iw]).padding(0.18);
  const y = d3.scaleLinear().domain([-500, 500]).range([ih, 0]);
  // franja de CO2 a dalt i barres de la bateria
  g.selectAll("rect.c").data(idx).join("rect").attr("x", i => x(i)).attr("y", 0).attr("width", x.bandwidth())
    .attr("height", 8).attr("rx", 3).attr("fill", i => co2Color(H.co2[i]));
  g.selectAll("rect.b").data(idx).join("rect").attr("x", i => x(i)).attr("width", x.bandwidth()).attr("rx", 3)
    .attr("y", i => y(Math.max(0, H.bat[i]))).attr("height", i => Math.abs(y(H.bat[i]) - y(0)))
    .attr("fill", i => (H.bat[i] > 0 ? COLORS.charge : COLORS.discharge));
  g.append("line").attr("x1", 0).attr("x2", iw).attr("y1", y(0)).attr("y2", y(0)).attr("stroke", "#E6E2DA");
  // franja d'acord: com més fosca, més segura és la decisió d'aquella hora
  const agree = planAgreement(idx);
  g.selectAll("rect.a").data(idx).join("rect").attr("x", i => x(i)).attr("y", ih + 24).attr("width", x.bandwidth()).attr("height", 10).attr("rx", 3)
    .attr("fill", COLORS.accent).attr("fill-opacity", (_, j) => 0.1 + 0.9 * agree[j]);
  g.append("text").attr("x", -6).attr("y", ih + 33).attr("text-anchor", "end").style("font-size", "10px").text("segur");
  // càrrega de la bateria al final de cada hora: es veu com s'omple i es buida al llarg del pla
  const ys = d3.scaleLinear().domain([0, 1]).range([ih + 82, ih + 44]);
  const cx = i => x(i) + x.bandwidth() / 2;
  g.append("path").datum(idx).attr("fill", COLORS.accent).attr("fill-opacity", 0.15)
    .attr("d", d3.area().x(cx).y0(ys(0)).y1(i => ys(H.soc[i])).curve(d3.curveMonotoneX));
  g.append("path").datum(idx).attr("fill", "none").attr("stroke", COLORS.accent).attr("stroke-width", 2)
    .attr("d", d3.line().x(cx).y(i => ys(H.soc[i])).curve(d3.curveMonotoneX));
  g.append("line").attr("x1", 0).attr("x2", iw).attr("y1", ys(1)).attr("y2", ys(1)).attr("stroke", "#E6E2DA").attr("stroke-dasharray", "2 3");
  g.append("text").attr("x", -6).attr("y", ys(0.5) + 3).attr("text-anchor", "end").style("font-size", "10px").text("càrrega");
  g.append("text").attr("x", iw + 6).attr("y", ys(1) + 3).style("font-size", "10px").text("100 %");
  g.append("text").attr("x", iw + 6).attr("y", ys(0) + 3).style("font-size", "10px").text("0 %");
  // zona invisible per hora amb el motiu de la decisió
  g.selectAll("rect.hit").data(idx).join("rect").attr("x", i => x(i) - x.step() * x.paddingInner() / 2).attr("y", 0)
    .attr("width", x.step()).attr("height", ih + 34).attr("fill", "transparent")
    .attr("data-tip", (i, j) => `<b>${H.t[i].slice(11, 13)} h: ${H.bat[i] > 20 ? "carrega " + f(H.bat[i]) + " kW" : H.bat[i] < -20 ? "descarrega " + f(-H.bat[i]) + " kW" : "espera"}</b><br>` +
      `${H.why[i]}<br>CO₂ ${f(H.co2[i] * 1000)} g/kWh, preu ${f(H.price[i] * 1000)} €/MWh.<br>` +
      `Amb un 20 % d'error a les previsions, la decisió es manté en ${f(agree[j] * 100)} % dels escenaris.`);
  const firstHours = d3.mean(agree.slice(0, 6));
  $("plan-take").innerHTML = statsHTML([["Decisió d'ara segura", `${f(agree[0] * 100)} %`], ["Properes 6 h", `${f(firstHours * 100)} %`],
    ["Tot el dia", `${f(d3.mean(agree) * 100)} %`], ["Amb previsions que fallen", "fins a un 20 %"]]);
  // preu com a línia fina amb el seu propi eix
  const yp = d3.scaleLinear().domain(d3.extent(idx, i => H.price[i])).nice().range([ih, 14]);
  g.append("path").datum(idx).attr("fill", "none").attr("stroke", "#7A5195").attr("stroke-width", 1.6).attr("stroke-dasharray", "3 3")
    .attr("d", d3.line().x(i => x(i) + x.bandwidth() / 2).y(i => yp(H.price[i])).curve(d3.curveMonotoneX));
  g.append("g").attr("class", "axis").call(d3.axisLeft(y).ticks(4).tickSize(0).tickPadding(6)).call(a => a.select(".domain").remove());
  g.append("g").attr("class", "axis").attr("transform", `translate(${iw},0)`)
    .call(d3.axisRight(yp).ticks(3).tickSize(0).tickPadding(6).tickFormat(v => f(v * 1000))).call(a => a.select(".domain").remove());
  g.append("g").attr("class", "axis").attr("transform", `translate(0,${ih})`)
    .call(d3.axisBottom(x).tickValues(idx.filter((_, j) => j % 3 === 0)).tickFormat(i => H.t[i].slice(11, 13) + " h").tickSize(0).tickPadding(6))
    .call(a => a.select(".domain").remove());
  g.append("text").attr("x", -34).attr("y", 4).style("font-size", "10px").text("kW");
  g.append("text").attr("x", iw + 8).attr("y", 4).style("font-size", "10px").text("€/MWh");
}

function downloadPlan() {
  const rows = [["hora", "co2_g_kwh", "preu_eur_mwh", "bateria_kw", "carrega_pct", "compra_xarxa_kw", "compra_sense_bateria_kw"]];
  next24().forEach(i => rows.push([H.t[i], (H.co2[i] * 1000).toFixed(0), (H.price[i] * 1000).toFixed(1), H.bat[i].toFixed(0),
    (100 * H.soc[i]).toFixed(0), H.grid[i].toFixed(0), H.base[i].toFixed(0)]));
  const blob = new Blob([rows.map(r => r.join(",")).join("\n")], { type: "text/csv" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `pla_bateria_${H.t[k].slice(0, 13).replace(" ", "_")}h.csv`;
  a.click();
}

// ---------------------------------------------------------------- avisos de la setmana
function events() {
  const idx = d3.range(week.start, week.end), list = [];
  const label = i => { const d = new Date(H.t[i].replace(" ", "T")); return `${DAYS[d.getDay()]} ${d.getDate()}/${d.getMonth() + 1}, ${H.t[i].slice(11, 13)} h`; };
  const off = idx.filter(i => H.load[i] < 50);
  if (off.length) list.push({ i: off[0], color: "#D55E00", title: "Fallada del comptador", text: `${off.length} hores amb consum 0. La bateria no descarrega per no perdre energia.` });
  const low = idx.filter(i => H.load[i] >= 50 && H.load[i] - H.pv[i] < 500);
  if (low.length) list.push({ i: low[0], color: "#E69F00", title: "Consum baix", text: `${low.length} hores amb menys de 500 kW de consum net (cap de setmana o festiu).` });
  const peaks = [...idx].sort((a, b) => H.co2[b] - H.co2[a]).slice(0, 1);
  peaks.forEach(i => list.push({ i, color: "#7A5532", title: "Pic de CO₂ de la setmana", text: `${f(H.co2[i] * 1000)} g/kWh. La bateria ${H.bat[i] < -1 ? "descarrega " + f(-H.bat[i]) + " kW" : "ja és buida"}.` }));
  const clean = [...idx].sort((a, b) => H.co2[a] - H.co2[b])[0];
  list.push({ i: clean, color: "#0072B2", title: "Hora més neta", text: `${f(H.co2[clean] * 1000)} g/kWh. ${H.bat[clean] > 1 ? "Aprofita per carregar " + f(H.bat[clean]) + " kW." : "La bateria ja és plena."}` });
  // millor dia per CO2 evitat
  let best = null;
  for (let d = week.start; d < week.end; d += 24) {
    let s = 0;
    for (let i = d; i < Math.min(d + 24, week.end); i++) s += (H.base[i] - H.grid[i]) * H.co2[i];
    if (!best || s > best.s) best = { d, s };
  }
  list.push({ i: best.d + 20, color: "#47908B", title: "Millor dia", text: `${f(best.s)} kg de CO₂ evitats en un sol dia.` });
  // hora mes cara: on mes es nota l'estalvi a la factura
  const dear = [...idx].sort((a, b) => H.price[b] - H.price[a])[0];
  list.push({ i: dear, color: "#7A5195", title: "Hora més cara", text: `${f(H.price[dear] * 1000)} €/MWh. ${H.bat[dear] < -1 ? "La bateria hi estalvia " + f(-H.bat[dear] * H.price[dear]) + " €." : "La bateria no hi descarrega: no li queda energia o hi ha hores més brutes."}` });
  // comptador congelat de nit (dada que cal revisar)
  const night = idx.filter(i => i > week.start && (+H.t[i].slice(11, 13) >= 23 || +H.t[i].slice(11, 13) <= 5));
  const frozen = night.filter(i => H.load[i] === H.load[i - 1]);
  if (frozen.length) list.push({ i: frozen[0], color: "#B0480E", title: "Comptador sense canvis", text: `${f(100 * frozen.length / night.length)} % de les hores de nit repeteixen el consum anterior: cal revisar el comptador.` });
  $("events").innerHTML = list.map(e => `<button class="event" data-go="${e.i}"><i style="background:${e.color}"></i><div><b>${e.title}</b><span>${label(e.i)}</span><span>${e.text}</span></div></button>`).join("");
}

// ---------------------------------------------------------------- calendari d'estalvi (clic = anar a aquell dia)
function drawCalendar() {
  const el = $("c-calendar");
  if (!el || !el.clientWidth) return;
  const days = [];
  D.weeks.forEach((w, wi) => {
    for (let d = w.start, j = 0; d < w.end; d += 24, j++) {
      let s = 0;
      for (let i = d; i < Math.min(d + 24, w.end); i++) s += (H.base[i] - H.grid[i]) * H.co2[i];
      days.push({ wi, j, d, s });
    }
  });
  // les caselles ocupen tota l'amplada de la targeta
  const w = el.clientWidth, cols = D.weeks.length, cell = (w - 46) / cols - 6, ch = Math.min(26, Math.max(16, cell * 0.3)), h = 7 * (ch + 4) + 22;
  el.innerHTML = "";
  const svg = d3.select(el).append("svg").attr("viewBox", `0 0 ${w} ${h}`).attr("width", "100%");
  const col = d3.scaleSequential([0, d3.max(days, d => d.s)], d3.interpolateRgb("#EEF4F2", "#1F5F59"));
  svg.selectAll("rect.day").data(days).join("rect").attr("class", "day").attr("x", d => 40 + d.wi * (cell + 6)).attr("y", d => d.j * (ch + 4))
    .attr("width", cell).attr("height", ch).attr("rx", 5).style("cursor", "pointer").attr("fill", d => col(d.s))
    .on("click", (_, d) => { $("week").value = d.wi; setWeek(d.wi); go("live"); show(d.d + 12); })
    .append("title").text(d => `${f(d.s)} kg de CO₂ evitats`);
  D.weeks.forEach((wk, wi) => svg.append("text").attr("x", 40 + wi * (cell + 6) + cell / 2).attr("y", h - 6).attr("text-anchor", "middle")
    .style("font-size", "10px").text(MONTHS[+wk.label.slice(3, 5) - 1].slice(0, 3)));
  ["1r dia", "", "", "4t", "", "", "7è"].forEach((t, j) => svg.append("text").attr("x", 0).attr("y", j * (ch + 4) + ch / 2 + 4).style("font-size", "10px").text(t));
}

// ---------------------------------------------------------------- reproducció
// el temps avança de manera contínua: entre dues hores tot canvia suaument (fluxos, bateria, sol)
let timer = null, speed = 1.2, clock = 0, last = 0;   // speed = hores per segon
const lerp = (a, b, x) => a + (b - a) * x;
// cada hora té un sol valor (la bateria rep una consigna per hora): en començar l'hora es passa al nou valor en poc temps i suau
const hourly = (key, c) => {
  // sempre dins de la setmana triada (el rellotge pot venir d'una altra setmana si s'ha canviat a mitja reproduccio)
  c = Math.max(week.start, Math.min(week.end - 1, Number.isFinite(c) ? c : week.start));
  const i = Math.min(Math.floor(c), week.end - 1), x = (c - i) / 0.15;
  if (x >= 1 || i === week.start) return H[key][i];
  return lerp(H[key][i - 1], H[key][i], x * x * (3 - 2 * x));
};
function sceneAt(c) {
  const i = Math.min(Math.floor(c), week.end - 1);
  const v = key => hourly(key, c);
  const hour = (+H.t[i].slice(11, 13) + (c - i)) % 24;
  scene.setHour({ hour, load: v("load"), pv: v("pv"), busy: (v("load") - loadExt[0]) / (loadExt[1] - loadExt[0]),
                  grid: v("grid"), bat: v("bat"), soc: socAt(c) }, co2Color(v("co2")));
}
// ---------------------------------------------------------------- xifres en directe i rellotge del dia
// la càrrega es guarda al final de cada hora: durant l'hora va de la de l'hora anterior a la nova
// (la simulació és contínua: la setmana comença amb la càrrega amb què va acabar l'anterior)
const socAt = c => {
  c = Math.max(week.start, Math.min(week.end - 1, Number.isFinite(c) ? c : week.start));
  const i = Math.min(Math.floor(c), week.end - 1), x = c - i;
  return lerp(i > 0 ? H.soc[i - 1] : 0.5, H.soc[i], x);
};
function liveNumbers(c) {
  const v = key => hourly(key, c);
  setAll("[data-soc]", e => (e.textContent = f(100 * socAt(c)) + " %"));
  battery(c);
  setAll("[data-grid]", e => (e.textContent = f(v("grid")) + " kW"));
  setAll("[data-co2]", e => (e.textContent = f(v("co2") * 1000) + " g/kWh"));
  setAll("[data-price]", e => (e.textContent = f(v("price") * 1000) + " €/MWh"));
  clockHand(c);
}

// bateria gran del panell: com d'plena està, què fa i quan s'omplirà o es buidarà al ritme d'ara
function battery(c) {
  const el = $("batt");
  if (!el) return;
  const soc = socAt(c), b = hourly("bat", c), eta = Math.sqrt(0.9);
  el.querySelector(".batt-fill").style.width = (100 * soc).toFixed(1) + "%";
  el.querySelector(".batt-fill").className = "batt-fill" + (b > 1 ? " charging" : b < -1 ? " discharging" : "");
  el.querySelector(".batt-kwh").textContent = `${f(2000 * soc)} de 2.000 kWh`;
  let state = "En espera";
  if (b > 1) {
    const hrs = (1 - soc) * 2000 / (b * eta);
    state = `Carregant ${f(b)} kW` + (soc < 0.99 ? `: plena en ${hrs < 1 ? f(hrs * 60) + " min" : f(hrs, 1) + " h"}` : "");
  } else if (b < -1) {
    const hrs = soc * 2000 * eta / -b;
    state = `Descarregant ${f(-b)} kW` + (soc > 0.01 ? `: buida en ${hrs < 1 ? f(hrs * 60) + " min" : f(hrs, 1) + " h"}` : "");
  } else state = soc > 0.99 ? "Plena, esperant una hora bruta" : soc < 0.01 ? "Buida, esperant una hora neta" : "En espera";
  el.querySelector(".batt-state").textContent = state;
}

const CLK = { c: 110, rOut: 104, rIn: 90, rBat: 58 };
let clockDay = -1;
const arc = d3.arc();
const dayStart = c => week.start + Math.floor((Math.floor(c) - week.start) / 24) * 24;
function drawClock() {
  const svg = d3.select("#clock24");
  if (svg.empty()) return;
  const d0 = dayStart(k);
  if (d0 === clockDay) return;
  clockDay = d0;
  svg.selectAll("*").remove();
  const g = svg.append("g").attr("transform", `translate(${CLK.c},${CLK.c})`);
  const a = h => (h / 24) * 2 * Math.PI, hours = d3.range(24).filter(h => d0 + h < week.end);
  // anell de fora: CO₂ de la xarxa de cada hora del dia
  g.selectAll("path.co2").data(hours).join("path").attr("class", "co2")
    .attr("d", h => arc({ innerRadius: CLK.rIn, outerRadius: CLK.rOut, startAngle: a(h) + 0.01, endAngle: a(h + 1) - 0.01 }))
    .attr("fill", h => co2Color(H.co2[d0 + h])).attr("opacity", 0).transition().duration(500).delay(h => h * 15).attr("opacity", 1);
  // dins: què fa la bateria (blau carrega, vermelló descarrega), més llarg com més potència
  g.selectAll("path.bat").data(hours.filter(h => Math.abs(H.bat[d0 + h]) > 1)).join("path").attr("class", "bat")
    .attr("d", h => arc({ innerRadius: CLK.rBat, outerRadius: CLK.rBat + 4 + 24 * Math.abs(H.bat[d0 + h]) / 500, startAngle: a(h) + 0.02, endAngle: a(h + 1) - 0.02 }))
    .attr("fill", h => (H.bat[d0 + h] > 0 ? COLORS.charge : COLORS.discharge)).attr("opacity", 0).transition().duration(500).delay(h => 200 + h * 15).attr("opacity", 0.85);
  [0, 6, 12, 18].forEach(h => g.append("text").attr("class", "tick")
    .attr("x", Math.sin(a(h)) * 50).attr("y", -Math.cos(a(h)) * 50 + 3).attr("text-anchor", "middle").text(h + " h"));
  g.append("path").attr("class", "past");
  g.append("g").attr("class", "hand").call(s => {
    s.append("line").attr("y1", -CLK.rBat + 2).attr("y2", -CLK.rOut - 4);
    s.append("circle").attr("cy", -CLK.rOut - 4).attr("r", 3.5);
  });
  g.append("text").attr("class", "soc num").attr("y", 4).attr("text-anchor", "middle");
  g.append("text").attr("class", "mode").attr("y", 20).attr("text-anchor", "middle");
}
function clockHand(c) {
  const svg = d3.select("#clock24");
  if (svg.empty() || clockDay < 0) return;
  // mateixos valors que el 3D, interpolats dins de l'hora
  const b = hourly("bat", c);
  const h = Math.max(0, Math.min(24, c - clockDay));
  svg.select(".hand").attr("transform", `rotate(${h * 15})`);
  svg.select(".past").attr("d", arc({ innerRadius: CLK.rIn - 2, outerRadius: CLK.rOut + 2, startAngle: 0, endAngle: h / 24 * 2 * Math.PI }));
  const mins = Math.floor((c % 1) * 60);
  svg.select(".soc").text(`${H.t[Math.min(Math.floor(c), week.end - 1)].slice(11, 13)}:${String(mins).padStart(2, "0")}`);
  svg.select(".mode").text("avui");
}

// semàfor per al campus: és bon moment per fer servir electricitat (equips de laboratori, càrrega de cotxes...)?
function signal() {
  const el = $("signal");
  if (!el) return;
  const ahead = d3.range(k, Math.min(k + 24, H.t.length)).map(i => H.co2[i]);
  const rank = ahead.filter(v => v < H.co2[k]).length / ahead.length;
  const best = k + d3.minIndex(ahead), less = 100 * (1 - H.co2[best] / H.co2[k]);
  const [cls, title, text] = rank <= 0.25
    ? ["go", "Bon moment per consumir", "Ara la xarxa és de les més netes de les properes 24 h."]
    : rank >= 0.6
      ? ["stop", "Millor esperar si es pot", `A les ${H.t[best].slice(11, 13)} h la xarxa serà un ${f(less)} % més neta.`]
      : ["wait", "Moment normal", `L'hora més neta de les properes 24 h és a les ${H.t[best].slice(11, 13)} h.`];
  el.className = "signal " + cls;
  el.querySelector("b").textContent = title;
  el.querySelector("p").textContent = text;
}

function frame(now) {
  if (!timer) return;
  const dt = Math.min(0.1, (now - last) / 1000);
  last = now;
  clock += dt * speed;
  if (clock >= week.end - 1) { clock = week.end - 1; show(week.end - 1); stop(); return; }
  if (Math.floor(clock) !== k) show(Math.floor(clock), true);
  sceneAt(clock);
  liveNumbers(clock);
  const min = Math.floor((clock % 1) * 60);
  $("chip-time").textContent = $("chip-time").textContent.replace(/\d\d:\d\d h$/, `${H.t[k].slice(11, 13)}:${String(min).padStart(2, "0")} h`);
  setAll("[data-clock]", e => (e.textContent = $("chip-time").textContent));
  timer = requestAnimationFrame(frame);
}
// vista inicial: càmera a lloc i rellotge al començament de la setmana
function goHome() {
  stop();
  show(week.start);
  scene.flyTo(scene.views.home);
}
function stop() { cancelAnimationFrame(timer); timer = null; scene.setPlaying(false); $("chip-time").classList.remove("live"); setAll("[data-act=play]", b => (b.textContent = "Reproduir")); }
function start() {
  // si ja s'havia arribat al final de la setmana, torna a començar
  if (!(clock >= week.start && clock < week.end - 1.01)) { clock = week.start; show(week.start); }
  last = performance.now(); scene.setPlaying(true); timer = requestAnimationFrame(frame); $("chip-time").classList.add("live"); setAll("[data-act=play]", b => (b.textContent = "Pausa")); }
const next = test => { for (let i = k + 1; i < week.end; i++) if (test(i)) return i; return k; };
document.addEventListener("click", e => {
  const row = e.target.closest("[data-row-week]");
  if (row) { $("week").value = row.dataset.rowWeek; setWeek(+row.dataset.rowWeek); go("live"); return; }
  const ev = e.target.closest("[data-goto]");
  if (ev) {
    go(ev.dataset.goto);
    if (ev.dataset.sel) setTimeout(() => document.querySelector(ev.dataset.sel)?.scrollIntoView({ block: "center", behavior: "smooth" }), 400);
    return;
  }
  const dec = e.target.closest("[data-dec]");
  if (dec) { window.Explorer.open(window.Charts.decisionData(+dec.dataset.dec).keys, week.start + 84); go("trust"); return; }
  const jump = e.target.closest("[data-go]");
  if (jump) { show(+jump.dataset.go); return; }
  const b = e.target.closest("[data-act],[data-speed]");
  if (!b) return;
  if (b.dataset.speed) {
    speed = +b.dataset.speed;
    setAll("[data-speed]", x => x.classList.toggle("on", +x.dataset.speed === speed));
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
  if (act === "home") goHome();
  if (act === "zoom-in") scene.zoom(1.25);
  if (act === "zoom-out") scene.zoom(0.8);
  if (act === "full") toggleExpand(b.closest(".stage"));
  if (act === "csv") downloadPlan();
  if (act === "open-explorer") { window.Explorer.open(["grid", "base", "co2", "savedco2"], k); go("trust"); }
  if (act === "csv-weeks") window.Charts.downloadWeeks();
  if (act === "report") window.Report.open(D);
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
let step = -1, tourTimer = null, tween = null;
// el temps avança suaument fins a l'hora del pas (així la llum i els fluxos no fan salts)
function animateClock(target, ms) {
  cancelAnimationFrame(tween);
  const from = clock, t0 = performance.now();
  const tick = now => {
    let x = Math.min(1, (now - t0) / ms);
    x = x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2;
    clock = from + (target - from) * x;
    if (Math.floor(clock) !== k) show(Math.floor(clock), true);
    sceneAt(clock);
    if (x < 1) tween = requestAnimationFrame(tick);
    else show(target);
  };
  tween = requestAnimationFrame(tick);
}
function showStep(i) {
  step = i;
  const s = tour[i];
  scene.flyTo(scene.views[s.view], 2400);
  // busquem l'hora dins les properes 24 h perquè el canvi de temps sigui curt
  if (s.hour && s.hour !== "end") {
    let target = k;
    for (let j = k + 1; j < Math.min(week.end, k + 25); j++) if (s.hour(j)) { target = j; break; }
    if (target !== k) animateClock(target, 2400);
  }
  const c = $("caption");
  c.style.opacity = 0;
  setTimeout(() => { c.textContent = s.text(); c.style.opacity = 1; }, 400);
}
function endTour() {
  clearTimeout(tourTimer);
  cancelAnimationFrame(tween);
  scene.setPlaying(false);
  step = -1;
  $("caption").style.opacity = 0;
  setAll("[data-act=tour]", b => b.classList.remove("on"));
  scene.controls.enabled = true;
}
function runTour() {
  stop();
  go("live");
  scene.controls.enabled = false;
  scene.setPlaying(true);   // durant la presentació l'energia es mou
  show(week.start);         // la presentació sempre comença a les 00:00 de la setmana
  setAll("[data-act=tour]", b => b.classList.add("on"));
  const run = i => {
    if (i >= tour.length) { tourTimer = setTimeout(endTour, 3500); return; }
    showStep(i);
    tourTimer = setTimeout(() => run(i + 1), 7000);
  };
  run(0);
}
addEventListener("keydown", e => {
  if (["INPUT", "SELECT"].includes(e.target.tagName)) return;
  if (e.code === "Space") { e.preventDefault(); timer ? stop() : start(); }
  // zoom del mapa amb el teclat
  if (e.key === "+" || e.key === "=") scene.zoom(1.2);
  if (e.key === "-" || e.key === "_") scene.zoom(1 / 1.2);
  if (e.key === "0") goHome();
  if (e.key === "p" || e.key === "P") step >= 0 ? endTour() : runTour();
  if (e.key === "Escape") { endTour(); document.querySelectorAll(".stage.expanded").forEach(s => toggleExpand(s, false)); }
  if (step >= 0 && e.key === "ArrowRight") { clearTimeout(tourTimer); showStep(Math.min(tour.length - 1, step + 1)); }
  if (step >= 0 && e.key === "ArrowLeft") { clearTimeout(tourTimer); showStep(Math.max(0, step - 1)); }
});

// ---------------------------------------------------------------- informació en passar el ratolí pel 3D
document.addEventListener("pointermove", e => {
  const tip = $("tip");
  const own = e.target.closest("[data-tip]");
  if (own) {
    tip.innerHTML = own.dataset.tip;
    tip.style.display = "block";
    tip.style.left = Math.min(e.clientX + 14, innerWidth - 300) + "px";
    tip.style.top = e.clientY + 14 + "px";
    return;
  }
  if (!e.target.closest(".stage") || e.target.tagName !== "CANVAS") { tip.style.display = "none"; return; }
  const u = scene.pick(e.clientX, e.clientY);
  scene.highlight(u && u.kind === "ct" ? u.info.feeds : null);
  if (!u) { tip.style.display = "none"; return; }
  let html = "";
  if (u.kind === "building") {
    const b = u.info;
    html = `<b>${b.name}</b><br>${b.role || ""}<br>${f(b.height_m)} m d'alçada${b.has_pv === true ? ", coberta solar" : ""}`;
  } else if (u.kind === "pv") html = `<b>Plaques solars</b><br>${f(u.info.area_m2)} m². Ara el campus en produeix ${f(H.pv[k])} kW ara`;
  else if (u.kind === "battery") html = `<b>Bateria</b> (ubicació proposada, al costat de l'escomesa principal)<br>${f(100 * H.soc[k])} %, ${f(H.bat[k])} kW<br>${H.why[k]}`;
  else if (u.kind === "ct") html = `<b>${u.info.name}</b> (${u.info.confidence === "documentada" ? "documentat" : "proposta"})<br>` +
    (u.info.upc_meter === false ? "Client a part: no forma part del consum de la UPC." : `Alimenta ${u.info.feeds.length} edificis (ressaltats al mapa).`);
  else if (u.kind === "grid") html = `<b>Escomesa principal</b> (proposta)<br>${f(H.grid[k])} kW, ${f(H.co2[k] * 1000)} g CO₂/kWh`;
  tip.innerHTML = html;
  tip.style.display = "block";
  tip.style.left = Math.min(e.clientX + 14, innerWidth - 300) + "px";
  tip.style.top = e.clientY + 14 + "px";
});

d3.select("#ramp").attr("viewBox", "0 0 56 8").selectAll("rect").data(CO2_RAMP).join("rect")
  .attr("x", (_, i) => i * 11.2).attr("width", 11.6).attr("height", 8).attr("fill", c => c);
document.addEventListener("change", e => {
});
addEventListener("resize", () => { drawPlan(); drawCalendar(); });

scene = createScene($("stage-big"), window.CAMPUS, COLORS);
window.Charts.init(D, { co2Color });
window.Explorer.init(D);

// des de l'explorador: anar a una hora concreta al 3D
document.addEventListener("explorer:goto", e => {
  const i = e.detail, wi = D.weeks.findIndex(w => i >= w.start && i < w.end);
  if (wi < 0) return;
  stop();
  if (D.weeks[wi] !== week) setWeek(wi);
  go("live");
  show(i);
});

// clic (sense arrossegar) a un element del 3D: el grafic en directe mostra les seves dades
const FOCUS = {
  battery: [["bat", "soc"], "Bateria: potència i càrrega"],
  grid: [["grid", "base", "co2"], "Escomesa: compra a la xarxa i CO₂"],
  pv: [["pv", "load"], "Plaques solars i consum del campus"],
  building: [["load", "pv"], "Consum del campus i solar"],
  ct: [["load", "pv"], "Consum del campus i solar"],
};
let downAt = null;
document.addEventListener("pointerdown", e => { downAt = e.target.tagName === "CANVAS" ? [e.clientX, e.clientY] : null; });
document.addEventListener("pointerup", e => {
  if (!downAt || e.target.tagName !== "CANVAS") return;
  const moved = Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]);
  downAt = null;
  if (moved > 5) return;                       // era un arrossegament de la camera
  const u = scene.pick(e.clientX, e.clientY);
  if (u && FOCUS[u.kind]) window.Explorer.focusLive(...FOCUS[u.kind]);
});
window.Planner.init();
setWeek(0);
go("live");
setTimeout(() => { drawPlan(); drawCalendar(); }, 60);
