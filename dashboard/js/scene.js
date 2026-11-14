// Escena 3D del Campus Nord (edificis reals d'OpenStreetMap) amb els fluxos d'energia.
// Estil maqueta d'arquitecte: clara, amb ombres suaus, perquè es llegeixi bé també al projector.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const S = 0.1;   // 1 unitat = 10 m
const VX = 1.5;  // alçades exagerades perquè es llegeixi millor

export function createScene(container, campus, colors) {
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color("#EAE6DE");

  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 400);
  const controls = new OrbitControls(camera, renderer.domElement);
  Object.assign(controls, { enableDamping: true, enablePan: false, minPolarAngle: 0.5, maxPolarAngle: 1.2, minZoom: 0.7, maxZoom: 5 });
  const HOME = { target: new THREE.Vector3(-2, 0, 4), zoom: 1.2, dir: new THREE.Vector3(1, 1.1, 1).normalize() };

  function place(view) {
    controls.target.copy(view.target);
    camera.position.copy(view.target).addScaledVector(view.dir, 90);
    camera.zoom = view.zoom;
    camera.updateProjectionMatrix();
  }

  // l'escena es pot moure entre la targeta petita i la vista gran
  let host = null;
  const observer = new ResizeObserver(resize);
  function resize() {
    if (!host) return;
    const w = host.clientWidth, h = host.clientHeight;
    const half = h < 450 ? 19 : 27;   // a la targeta petita ens apropem més
    if (!w || !h) return;
    renderer.setSize(w, h);
    Object.assign(camera, { left: -half * w / h, right: half * w / h, top: half, bottom: -half });
    camera.updateProjectionMatrix();
  }
  function mount(el) {
    if (host) observer.unobserve(host);
    host = el;
    el.prepend(renderer.domElement);
    Object.values(tags).forEach(t => el.appendChild(t.el));
    el.appendChild(credit);
    observer.observe(el);
    resize();
    controls.enableZoom = el.clientHeight >= 450;
  }

  // llums: cel clar i un sol que es mou amb l'hora
  const hemi = new THREE.HemisphereLight("#FFFFFF", "#D9D3C7", 1.25);
  const sun = new THREE.DirectionalLight("#FFFFFF", 1.4);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  Object.assign(sun.shadow.camera, { left: -40, right: 40, top: 40, bottom: -40, near: 1, far: 220 });
  sun.shadow.bias = -0.0005;
  sun.shadow.radius = 4;
  scene.add(hemi, sun, sun.target);

  const ground = new THREE.Mesh(new THREE.PlaneGeometry(180, 140), new THREE.MeshStandardMaterial({ color: "#E2DDD3", roughness: 1 }));
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  scene.add(ground);

  const shape = ring => {
    const s = new THREE.Shape();
    ring.forEach(([x, z], i) => (i ? s.lineTo(x * S, -z * S) : s.moveTo(x * S, -z * S)));
    s.closePath();
    return s;
  };
  const extrude = (ring, h) => {
    const g = new THREE.ExtrudeGeometry(shape(ring), { depth: h, bevelEnabled: false });
    g.rotateX(-Math.PI / 2);
    return g;
  };
  const line = (pts, mat, y = 0.02) =>
    new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts.map(([x, z]) => new THREE.Vector3(x * S, y, z * S))), mat);

  // carrers i límit del campus
  const streetMat = new THREE.LineBasicMaterial({ color: "#CEC8BC" });
  campus.streets.forEach(s => scene.add(line(s.line, streetMat, 0.01)));
  const edge = line(campus.boundary, new THREE.LineDashedMaterial({ color: "#A59D8E", dashSize: 0.6, gapSize: 0.5 }));
  edge.computeLineDistances();
  scene.add(edge);

  // edificis veïns: volums grisos sense detall
  const contextMat = new THREE.MeshStandardMaterial({ color: "#D8D3C9", roughness: 1 });
  const contextEdge = new THREE.LineBasicMaterial({ color: "#C8C2B6" });
  campus.context_buildings.forEach(b => {
    const geo = extrude(b.ring, b.h * S * VX);
    const m = new THREE.Mesh(geo, contextMat);
    m.receiveShadow = true;
    scene.add(m, new THREE.LineSegments(new THREE.EdgesGeometry(geo, 30), contextEdge));
  });

  // edificis del campus: blancs; de nit s'il·luminen una mica segons el consum
  const campusMat = new THREE.MeshStandardMaterial({ color: "#FBFAF7", roughness: 0.9, emissive: "#FFC27A", emissiveIntensity: 0 });
  const campusEdge = new THREE.LineBasicMaterial({ color: "#9E978B" });
  const pickables = [], byName = {};
  const highlightMat = new THREE.MeshStandardMaterial({ color: "#CDE6E2", roughness: 0.9 });
  campus.buildings.forEach(b => {
    const geo = extrude(b.polygon, b.height_m * S * VX);
    const m = new THREE.Mesh(geo, campusMat);
    m.castShadow = m.receiveShadow = true;
    m.userData = { kind: "building", info: b };
    scene.add(m, new THREE.LineSegments(new THREE.EdgesGeometry(geo, 30), campusEdge));
    pickables.push(m);
    byName[b.id] = byName[b.name] = m;
  });

  // plaques solars reals sobre els aularis A
  const pvMat = new THREE.MeshStandardMaterial({ color: "#2F4A63", roughness: 0.35, metalness: 0.2, emissive: colors.solar, emissiveIntensity: 0 });
  campus.pv_arrays.forEach(p => {
    const host = campus.buildings.find(b => b.has_pv === true && Math.hypot(b.centroid[0] - p.centroid[0], b.centroid[1] - p.centroid[1]) < 40);
    const g = new THREE.ShapeGeometry(shape(p.ring));
    g.rotateX(-Math.PI / 2);
    const m = new THREE.Mesh(g, pvMat);
    m.position.y = (host ? host.height_m : 17.5) * S * VX + 0.06;
    m.userData = { kind: "pv", info: p };
    scene.add(m);
    pickables.push(m);
  });

  // bateria, escomesa i nus elèctric (més grans que la realitat perquè es vegin)
  const A = campus.energy_assets;
  const at = p => new THREE.Vector3(p[0] * S, p[1] * S * VX, p[2] * S);
  // l'escomesa principal fa de nus: la xarxa hi arriba pel sud (carrer), la bateria és a l'est
  // i les plaques i els centres de transformació queden al nord. Així els cables no es creuen.
  const mainCT = at(A.grid_connection.pos);
  const node = mainCT.clone().setY(0.3);
  const gridPos = mainCT.clone().add(new THREE.Vector3(0.6, 0, 4.2));
  const batPos = mainCT.clone().add(new THREE.Vector3(4.4, 0, 0.8));
  const loadPos = at(A.campus_load_anchor.pos);

  const battery = new THREE.Group();
  const shellGeo = new THREE.BoxGeometry(2.8, 1.3, 1.2);
  const shell = new THREE.Mesh(shellGeo, new THREE.MeshStandardMaterial({ color: "#FFFFFF", transparent: true, opacity: 0.35, roughness: 0.2 }));
  shell.position.y = 0.65;
  const fill = new THREE.Mesh(new THREE.BoxGeometry(2.55, 1.1, 0.95), new THREE.MeshStandardMaterial({ color: colors.accent, roughness: 0.5 }));
  const outline = new THREE.LineSegments(new THREE.EdgesGeometry(shellGeo), new THREE.LineBasicMaterial({ color: "#5E5A54" }));
  outline.position.y = 0.65;
  const pad = new THREE.Mesh(new THREE.BoxGeometry(3.2, 0.12, 1.6), new THREE.MeshStandardMaterial({ color: "#C9C3B7" }));
  battery.add(pad, fill, shell, outline);
  battery.position.copy(batPos);
  battery.traverse(o => { o.castShadow = true; });
  shell.userData = { kind: "battery" };
  scene.add(battery);
  pickables.push(shell);

  const steel = new THREE.MeshStandardMaterial({ color: "#7D776E", roughness: 0.6 });
  const tower = new THREE.Group();
  const mast = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.17, 3.4, 8), steel);
  mast.position.y = 1.7;
  tower.add(mast);
  [2.6, 3.1].forEach(y => { const a = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.07, 0.07), steel); a.position.y = y; tower.add(a); });
  tower.position.copy(gridPos);
  tower.traverse(o => { o.castShadow = true; });
  mast.userData = { kind: "grid" };
  scene.add(tower);
  pickables.push(mast);

  // centres de transformació (proposta) i subestació del BSC (real, però és un client a part)
  const conns = A.grid_connections || [];
  const connPos = {};
  const kioskMat = new THREE.MeshStandardMaterial({ color: "#EFEAE0", roughness: 0.8 });
  const roofMat = new THREE.MeshStandardMaterial({ color: "#6E6A63", roughness: 0.7 });
  conns.forEach(c => {
    const p = at(c.pos);
    connPos[c.id] = c.main ? mainCT.clone() : p;
    if (c.underground) {
      const disc = new THREE.Mesh(new THREE.CylinderGeometry(1.4, 1.4, 0.08, 40), new THREE.MeshStandardMaterial({ color: "#B9B4AA" }));
      disc.position.copy(p).setY(0.05);
      disc.userData = { kind: "ct", info: c };
      scene.add(disc);
      pickables.push(disc);
      return;
    }
    const kiosk = new THREE.Group();
    if (c.main) p.copy(mainCT);
    const box = new THREE.Mesh(new THREE.BoxGeometry(1.3, 0.9, 1.0), kioskMat);
    box.position.y = 0.45;
    const roof = new THREE.Mesh(new THREE.BoxGeometry(1.45, 0.1, 1.15), roofMat);
    roof.position.y = 0.95;
    kiosk.add(box, roof);
    kiosk.position.copy(p);
    kiosk.scale.setScalar(1.7);   // més gran que la realitat perquè es vegi
    kiosk.traverse(o => { o.castShadow = true; });
    box.userData = { kind: "ct", info: c };
    scene.add(kiosk);
    pickables.push(box);
  });
  // anell soterrat de mitja tensió: un cable fi arran de terra
  const cableMat = new THREE.MeshBasicMaterial({ color: "#A08C70", transparent: true, opacity: 0.75 });
  (A.mv_links || []).forEach(([a1, b1]) => {
    if (!connPos[a1] || !connPos[b1]) return;
    const path = new THREE.LineCurve3(connPos[a1].clone().setY(0.08), connPos[b1].clone().setY(0.08));
    scene.add(new THREE.Mesh(new THREE.TubeGeometry(path, 40, 0.06, 6), cableMat));
  });

  function highlight(names) {
    Object.values(byName).forEach(m => { m.material = campusMat; });
    (names || []).forEach(n => { if (byName[n]) byName[n].material = highlightMat; });
  }

  // ---------------------------------------------------------------- fluxos d'energia
  const sprite = (() => {
    const c = document.createElement("canvas");
    c.width = c.height = 64;
    const g = c.getContext("2d");
    g.beginPath();
    g.arc(32, 32, 26, 0, Math.PI * 2);
    g.fillStyle = "#fff";
    g.fill();
    g.lineWidth = 6;
    g.strokeStyle = "rgba(255,255,255,.9)";
    g.stroke();
    return new THREE.CanvasTexture(c);
  })();

  const curve = pts => new THREE.CatmullRomCurve3(pts, false, "centripetal");
  // camí recte per trams (per seguir l'anell soterrat)
  const polyline = pts => { const p = new THREE.CurvePath(); for (let j = 1; j < pts.length; j++) p.add(new THREE.LineCurve3(pts[j - 1], pts[j])); return p; };
  const lift = (v, y) => v.clone().setY(y);
  const flows = {
    grid: curve([lift(gridPos, 3.2), lift(gridPos.clone().lerp(node, 0.5), 1.6), lift(node, 0.6)]),
    bat: curve([lift(node, 0.6), lift(node.clone().lerp(batPos, 0.5), 0.9), lift(batPos, 0.9)]),
  };
  const flowColor = { grid: "#B79D7E", bat: "#9CC3E0" };
  const area = id => { const b = campus.buildings.find(x => x.id === id || x.name === id); return b ? b.area_m2 * b.height_m : 0; };
  const shares = {};
  conns.filter(c => c.upc_meter !== false).forEach(c => { shares[c.id] = c.feeds.reduce((s, n) => s + area(n), 0); });
  const totalShare = Object.values(shares).reduce((a, b) => a + b, 0) || 1;
  // el consum va pel mateix camí que l'anell soterrat fins a cada centre
  const ringPath = id => {
    const link = (A.mv_links || []).find(([, b]) => b === id);
    if (!link) return [node];
    return [...ringPath(link[0]), connPos[id]];
  };
  conns.filter(c => c.upc_meter !== false).forEach(c => {
    const pts = c.main ? [lift(node, 0.25), lift(at(A.pv_inverters[1].pos), 0.25)] : ringPath(c.id).map(p => lift(p, 0.25));
    flows["load_" + c.id] = polyline(pts);
    flowColor["load_" + c.id] = null;   // ja es veu el cable de l'anell
  });
  A.pv_inverters.forEach((inv, i) => {
    const p = at(inv.pos).setY(17.5 * S * VX + 0.25);
    flows["pv" + i] = curve([p, lift(p.clone().lerp(node, 0.35), 3.2), lift(p.clone().lerp(node, 0.8), 2.2), lift(node, 1.2)]);
    flowColor["pv" + i] = "#F2D08A";
  });

  const MAX_P = 28;
  const streams = {};
  for (const [name, c] of Object.entries(flows)) {
    // la guia de cada flux té un to del seu color, així es distingeixen les línies
    const guide = new THREE.Mesh(new THREE.TubeGeometry(c, 80, 0.035, 6),
      new THREE.MeshBasicMaterial({ color: flowColor[name] || "#D6D0C4", transparent: true, opacity: flowColor[name] ? 0.7 : 0 }));
    scene.add(guide);
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(MAX_P * 3), 3));
    const mat = new THREE.PointsMaterial({ size: 8 * renderer.getPixelRatio(), map: sprite, transparent: true, alphaTest: 0.3,
      depthWrite: false, sizeAttenuation: false });
    const pts = new THREE.Points(geo, mat);
    pts.frustumCulled = false;
    scene.add(pts);
    streams[name] = { curve: c, geo, mat, guide, seed: Float32Array.from({ length: MAX_P }, Math.random), kw: 0, dir: 1, phase: 0 };
  }

  function stepStreams(dt) {
    for (const s of Object.values(streams)) {
      const share = Math.min(1, s.kw / 1400);
      const n = s.kw < 1 ? 0 : Math.max(3, Math.round(MAX_P * share));
      s.phase += dt * (0.04 + 0.16 * share) * s.dir;
      const arr = s.geo.attributes.position.array;
      for (let i = 0; i < n; i++) {
        let u = (s.seed[i] + s.phase) % 1;
        if (u < 0) u += 1;
        const p = s.curve.getPointAt(u);
        arr[i * 3] = p.x; arr[i * 3 + 1] = p.y; arr[i * 3 + 2] = p.z;
      }
      s.geo.setDrawRange(0, n);
      s.geo.attributes.position.needsUpdate = true;
    }
  }

  // ---------------------------------------------------------------- etiquetes
  const tags = {};
  function addTag(name, pos, dx, dy) {
    const el = document.createElement("div");
    el.className = "tag";
    tags[name] = { el, pos, dx, dy };
  }
  addTag("battery", lift(batPos, 1.6), 70, 30);
  addTag("grid", lift(gridPos, 3.8), 90, 20);
  addTag("load", lift(loadPos, loadPos.y + 1.6), 50, -18);
  addTag("solar", at(A.pv_inverters[0].pos).setY(17.5 * S * VX + 1.6), -50, -18);
  conns.forEach(c => {
    const short = c.main ? "Escomesa principal" : c.underground ? "Subestació BSC" : c.name.replace("CT ", "Centre ").replace(" (CPD)", "");
    addTag("ct_" + c.id, lift(connPos[c.id], 2.4), 0, -4);
    tags["ct_" + c.id].el.classList.add("small");
    tags["ct_" + c.id].el.textContent = short;
  });
  const credit = document.createElement("div");
  credit.className = "credit";
  credit.textContent = "Edificis reals © OpenStreetMap contributors. Centres de transformació i bateria: proposta. Alçades ×1,5.";

  function placeTags() {
    if (!host) return;
    const w = host.clientWidth, h = host.clientHeight;
    for (const t of Object.values(tags)) {
      const v = t.pos.clone().project(camera);
      t.el.style.left = ((v.x + 1) / 2 * w + t.dx) + "px";
      t.el.style.top = ((1 - v.y) / 2 * h + t.dy) + "px";
    }
  }

  // ---------------------------------------------------------------- vols de càmera
  let flight = null;
  function flyTo(view, ms = 1800) {
    flight = { from: { target: controls.target.clone(), zoom: camera.zoom, dir: camera.position.clone().sub(controls.target).normalize() },
               to: view, t0: performance.now(), ms };
  }
  const views = {
    home: HOME,
    solar: { target: at(A.pv_inverters[1].pos), zoom: 2.3, dir: new THREE.Vector3(0.4, 1.1, 1).normalize() },
    battery: { target: batPos, zoom: 3.4, dir: new THREE.Vector3(1, 0.9, 0.5).normalize() },
    grid: { target: gridPos, zoom: 2.8, dir: new THREE.Vector3(1.2, 0.8, -0.2).normalize() },
  };

  // ---------------------------------------------------------------- estat d'una hora
  let socTarget = 0.5, socShown = 0.5;
  const fmt = (x, d = 0) => x.toLocaleString("ca-ES", { maximumFractionDigits: d, minimumFractionDigits: d });
  function setHour(h, co2Color) {
    const day = h.hour >= 7 && h.hour <= 19;
    const a = (h.hour - 6) / 14 * Math.PI;
    sun.position.set(Math.cos(a) * 45, Math.max(0.2, Math.sin(a)) * 50 + 8, 28);
    sun.intensity = day ? 0.8 + 0.8 * Math.sin(Math.max(0, a)) : 0.45;
    sun.color.set(day ? "#FFFFFF" : "#D6DEEA");
    hemi.intensity = day ? 1.25 : 0.95;
    scene.background.set(day ? "#EAE6DE" : "#DFE1E4");
    campusMat.emissiveIntensity = day ? 0 : 0.08 + 0.12 * h.busy;
    pvMat.emissiveIntensity = 0.9 * h.pv / 145;

    streams.grid.kw = h.grid;
    streams.grid.mat.color.set(co2Color);
    Object.keys(shares).forEach(id => {
      streams["load_" + id].kw = h.load * shares[id] / totalShare;
      streams["load_" + id].mat.color.set("#3E4A56");
    });
    streams.bat.kw = Math.abs(h.bat);
    streams.bat.dir = h.bat >= 0 ? -1 : 1;
    streams.bat.mat.color.set(h.bat >= 0 ? colors.charge : colors.discharge);
    A.pv_inverters.forEach((_, i) => {
      streams["pv" + i].kw = h.pv;
      streams["pv" + i].mat.color.set(colors.solar);
    });
    socTarget = h.soc;

    tags.battery.el.textContent = `Bateria ${fmt(100 * h.soc)} %, ${h.bat > 1 ? "+" : ""}${fmt(h.bat)} kW`;
    tags.grid.el.textContent = `Xarxa ${fmt(h.grid)} kW`;
    tags.load.el.textContent = `Campus ${fmt(h.load)} kW`;
    tags.solar.el.textContent = `Solar ${fmt(h.pv)} kW`;
  }

  // ---------------------------------------------------------------- selecció amb el ratolí
  const ray = new THREE.Raycaster(), mouse = new THREE.Vector2();
  function pick(x, y) {
    const r = renderer.domElement.getBoundingClientRect();
    mouse.set((x - r.left) / r.width * 2 - 1, -(y - r.top) / r.height * 2 + 1);
    ray.setFromCamera(mouse, camera);
    const hit = ray.intersectObjects(pickables)[0];
    return hit ? hit.object.userData : null;
  }

  // ---------------------------------------------------------------- bucle
  let last = performance.now();
  function frame(now) {
    const dt = Math.min(0.05, (now - last) / 1000);
    last = now;
    if (flight) {
      let t = Math.min(1, (now - flight.t0) / flight.ms);
      t = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
      place({ target: flight.from.target.clone().lerp(flight.to.target, t),
              dir: flight.from.dir.clone().lerp(flight.to.dir, t).normalize(),
              zoom: flight.from.zoom + (flight.to.zoom - flight.from.zoom) * t });
      if (t >= 1) flight = null;
    } else {
      controls.update();
    }
    socShown += (socTarget - socShown) * Math.min(1, dt * 5);
    fill.scale.y = Math.max(0.02, socShown);
    fill.position.y = 0.1 + 0.55 * fill.scale.y;
    stepStreams(dt);
    placeTags();
    renderer.render(scene, camera);
    requestAnimationFrame(frame);
  }

  place(HOME);
  mount(container);
  requestAnimationFrame(frame);
  function zoom(factor) {
    camera.zoom = Math.min(controls.maxZoom, Math.max(controls.minZoom, camera.zoom * factor));
    camera.updateProjectionMatrix();
  }

  return { setHour, flyTo, views, pick, controls, mount, zoom, highlight, canvas: renderer.domElement };
}
