// Escena 3D del Campus Nord (edificis reals d'OpenStreetMap) amb els fluxos d'energia.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const S = 0.1;   // 1 unitat = 10 m
const VX = 1.5;  // alçades exagerades perquè la maqueta es llegeixi millor

export function createScene(container, campus, colors) {
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  container.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color("#0B0C0D");
  scene.fog = new THREE.Fog("#0B0C0D", 90, 170);

  // càmera isomètrica, com una maqueta
  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 400);
  const controls = new OrbitControls(camera, renderer.domElement);
  Object.assign(controls, { enableDamping: true, enablePan: false, minPolarAngle: 0.5, maxPolarAngle: 1.2,
                            minZoom: 0.7, maxZoom: 5 });
  const HOME = { target: new THREE.Vector3(-2, 0, 4), zoom: 1.15, dir: new THREE.Vector3(1, 1.1, 1).normalize() };

  function place(view) {
    controls.target.copy(view.target);
    camera.position.copy(view.target).addScaledVector(view.dir, 90);
    camera.zoom = view.zoom;
    camera.updateProjectionMatrix();
  }
  function resize() {
    const w = container.clientWidth, h = container.clientHeight, half = 30;
    renderer.setSize(w, h);
    Object.assign(camera, { left: -half * w / h, right: half * w / h, top: half, bottom: -half });
    camera.updateProjectionMatrix();
  }
  new ResizeObserver(resize).observe(container);
  resize();
  place(HOME);

  // llum de nit: lluna freda i un sol que es mou amb l'hora
  const hemi = new THREE.HemisphereLight("#9FB0C4", "#1A1814", 0.55);
  const sun = new THREE.DirectionalLight("#EEF0F2", 0.9);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  Object.assign(sun.shadow.camera, { left: -40, right: 40, top: 40, bottom: -40, near: 1, far: 220 });
  sun.shadow.bias = -0.0005;
  scene.add(hemi, sun, sun.target);

  const ground = new THREE.Mesh(new THREE.PlaneGeometry(180, 140), new THREE.MeshStandardMaterial({ color: "#121416", roughness: 1 }));
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  scene.add(ground);

  const shape = ring => {
    const s = new THREE.Shape();
    ring.forEach(([x, z], i) => (i ? s.lineTo(x * S, -z * S) : s.moveTo(x * S, -z * S)));
    s.closePath();
    return s;
  };
  const extrude = (ring, h, bevel) => {
    const g = new THREE.ExtrudeGeometry(shape(ring), bevel
      ? { depth: h, bevelEnabled: true, bevelThickness: 0.03, bevelSize: 0.03, bevelSegments: 1 }
      : { depth: h, bevelEnabled: false });
    g.rotateX(-Math.PI / 2);
    return g;
  };
  const line = (pts, mat, y = 0.02) =>
    new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts.map(([x, z]) => new THREE.Vector3(x * S, y, z * S))), mat);

  // carrers i límit del campus
  const streetMat = new THREE.LineBasicMaterial({ color: "#26292D" });
  campus.streets.forEach(s => scene.add(line(s.line, streetMat, 0.01)));
  const edge = line(campus.boundary, new THREE.LineDashedMaterial({ color: "#3C4146", dashSize: 0.6, gapSize: 0.5 }));
  edge.computeLineDistances();
  scene.add(edge);

  // edificis veïns: només volum, sense detall
  const contextMat = new THREE.MeshStandardMaterial({ color: "#17191C", roughness: 1 });
  const contextEdge = new THREE.LineBasicMaterial({ color: "#26292D" });
  campus.context_buildings.forEach(b => {
    const geo = extrude(b.ring, b.h * S * VX, false);
    const m = new THREE.Mesh(geo, contextMat);
    m.receiveShadow = true;
    scene.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo, 30), contextEdge));
    scene.add(m);
  });

  // edificis del campus: les "finestres" brillen segons el consum
  const campusMat = new THREE.MeshStandardMaterial({ color: "#34393E", roughness: 0.85, emissive: "#FFB36B", emissiveIntensity: 0.02 });
  const edgeMat = new THREE.LineBasicMaterial({ color: "#565C62" });
  const pickables = [];
  campus.buildings.forEach(b => {
    const geo = extrude(b.polygon, b.height_m * S * VX, false);
    const m = new THREE.Mesh(geo, campusMat);
    m.castShadow = m.receiveShadow = true;
    scene.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo, 30), edgeMat));
    m.userData = { kind: "building", info: b };
    scene.add(m);
    pickables.push(m);
  });

  // plaques solars reals sobre els aularis A
  const pvMat = new THREE.MeshStandardMaterial({ color: "#1E2A36", roughness: 0.4, emissive: colors.solar, emissiveIntensity: 0 });
  campus.pv_arrays.forEach(p => {
    const host = campus.buildings.find(b => b.has_pv === true &&
      Math.hypot(b.centroid[0] - p.centroid[0], b.centroid[1] - p.centroid[1]) < 40);
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
  const batPos = at(A.battery.pos);
  const gridPos = at(A.grid_connection.pos).add(new THREE.Vector3(2.4, 0, 1.4));
  const loadPos = at(A.campus_load_anchor.pos);
  const node = batPos.clone().lerp(gridPos, 0.5).setY(0.3);

  const battery = new THREE.Group();
  const shell = new THREE.Mesh(new THREE.BoxGeometry(2.8, 1.3, 1.2),
    new THREE.MeshStandardMaterial({ color: "#C9D2D8", transparent: true, opacity: 0.18, roughness: 0.2 }));
  shell.position.y = 0.65;
  const fill = new THREE.Mesh(new THREE.BoxGeometry(2.55, 1.1, 0.95),
    new THREE.MeshStandardMaterial({ color: colors.accent, emissive: colors.accent, emissiveIntensity: 0.55 }));
  const outline = new THREE.LineSegments(new THREE.EdgesGeometry(shell.geometry), new THREE.LineBasicMaterial({ color: "#7E8A90" }));
  outline.position.y = 0.65;
  battery.add(fill, shell, outline);
  battery.position.copy(batPos);
  shell.userData = { kind: "battery" };
  scene.add(battery);
  pickables.push(shell);

  const steel = new THREE.MeshStandardMaterial({ color: "#6E6A63", roughness: 0.6 });
  const tower = new THREE.Group();
  const mast = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.16, 3.4, 6), steel);
  mast.position.y = 1.7;
  tower.add(mast);
  [2.6, 3.1].forEach(y => { const a = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.06, 0.06), steel); a.position.y = y; tower.add(a); });
  tower.position.copy(gridPos);
  mast.userData = { kind: "grid" };
  scene.add(tower);
  pickables.push(mast);

  // ---------------------------------------------------------------- fluxos d'energia
  const sprite = (() => {
    const c = document.createElement("canvas");
    c.width = c.height = 64;
    const g = c.getContext("2d"), r = g.createRadialGradient(32, 32, 0, 32, 32, 32);
    r.addColorStop(0, "rgba(255,255,255,1)");
    r.addColorStop(0.25, "rgba(255,255,255,.75)");
    r.addColorStop(1, "rgba(255,255,255,0)");
    g.fillStyle = r;
    g.fillRect(0, 0, 64, 64);
    return new THREE.CanvasTexture(c);
  })();

  const curve = pts => new THREE.CatmullRomCurve3(pts, false, "centripetal");
  const lift = (v, y) => v.clone().setY(y);
  const flows = {
    grid: curve([lift(gridPos, 3.2), lift(gridPos.clone().lerp(node, 0.5), 1.3), node]),
    bat: curve([node, lift(node.clone().lerp(batPos, 0.5), 0.7), lift(batPos, 0.9)]),
    load: curve([node, lift(node.clone().lerp(loadPos, 0.35), 1.6), lift(node.clone().lerp(loadPos, 0.75), 2.6), lift(loadPos, loadPos.y + 0.2)]),
  };
  A.pv_inverters.forEach((inv, i) => {
    const p = at(inv.pos).setY(17.5 * S * VX + 0.25);
    flows["pv" + i] = curve([p, lift(p.clone().lerp(node, 0.3), 2.0), lift(p.clone().lerp(node, 0.7), 0.9), node]);
  });

  const MAX_P = 80;
  const streams = {};
  for (const [name, c] of Object.entries(flows)) {
    const guide = new THREE.Mesh(new THREE.TubeGeometry(c, 80, 0.035, 6),
      new THREE.MeshBasicMaterial({ color: "#3A3D41", transparent: true, opacity: 0.8 }));
    scene.add(guide);
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(MAX_P * 3), 3));
    const mat = new THREE.PointsMaterial({ size: 9 * renderer.getPixelRatio(), map: sprite, transparent: true,
      depthWrite: false, sizeAttenuation: false, color: "#FFFFFF" });
    const pts = new THREE.Points(geo, mat);
    pts.frustumCulled = false;
    scene.add(pts);
    streams[name] = { curve: c, geo, mat, seed: Float32Array.from({ length: MAX_P }, Math.random), kw: 0, dir: 1, phase: 0, guide };
  }

  function stepStreams(dt) {
    for (const s of Object.values(streams)) {
      const share = Math.min(1, s.kw / 1400);
      const n = s.kw < 1 ? 0 : Math.max(6, Math.round(40 * share));
      s.phase += dt * (0.05 + 0.25 * share) * s.dir;
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
    el.style.cssText = "position:absolute;z-index:4;pointer-events:none;white-space:nowrap;font:500 11px var(--mono);" +
      "color:var(--text);background:rgba(11,12,13,.78);border:1px solid var(--line);padding:3px 7px;border-radius:2px;transform:translate(-50%,-100%)";
    container.parentElement.appendChild(el);
    tags[name] = { el, pos, dx, dy };
  }
  addTag("battery", lift(batPos, 1.6), -100, 46);
  addTag("grid", lift(gridPos, 3.8), 120, 14);
  addTag("load", lift(loadPos, loadPos.y + 1.6), 50, -18);
  addTag("solar", at(A.pv_inverters[0].pos).setY(17.5 * S * VX + 1.6), -50, -18);
  function placeTags() {
    const w = container.clientWidth, h = container.clientHeight;
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
  function setHour(h, co2Color) {
    const day = h.hour >= 7 && h.hour <= 19;
    const a = (h.hour - 6) / 14 * Math.PI;
    sun.position.set(Math.cos(a) * 45, Math.max(0.15, Math.sin(a)) * 50 + 6, 28);
    sun.intensity = day ? 0.35 + 0.9 * Math.sin(Math.max(0, a)) : 0.12;
    hemi.intensity = day ? 0.75 : 0.45;
    campusMat.emissiveIntensity = (day ? 0.0 : 0.04) + 0.1 * h.busy;
    pvMat.emissiveIntensity = 1.1 * h.pv / 145;

    streams.grid.kw = h.grid;
    streams.grid.mat.color.set(co2Color);
    streams.grid.guide.material.color.set(co2Color).multiplyScalar(0.45);
    streams.load.kw = h.load;
    streams.load.mat.color.set("#B9B4AA");
    streams.bat.kw = Math.abs(h.bat);
    streams.bat.dir = h.bat >= 0 ? -1 : 1;
    streams.bat.mat.color.set(h.bat >= 0 ? colors.charge : colors.discharge);
    A.pv_inverters.forEach((_, i) => {
      streams["pv" + i].kw = h.pv / 3 * 6;   // la solar és petita: l'ampliem perquè es vegi el moviment
      streams["pv" + i].mat.color.set(colors.solar);
    });
    socTarget = h.soc;

    const f = (x, d = 0) => x.toLocaleString("ca-ES", { maximumFractionDigits: d, minimumFractionDigits: d });
    tags.battery.el.textContent = `BATERIA ${f(100 * h.soc)} % · ${h.bat > 1 ? "+" : ""}${f(h.bat)} kW`;
    tags.grid.el.textContent = `XARXA ${f(h.grid)} kW`;
    tags.load.el.textContent = `CAMPUS ${f(h.load)} kW`;
    tags.solar.el.textContent = `SOLAR ${f(h.pv)} kW`;
  }

  // ---------------------------------------------------------------- hover
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
  requestAnimationFrame(frame);

  return { setHour, flyTo, views, pick, controls };
}
