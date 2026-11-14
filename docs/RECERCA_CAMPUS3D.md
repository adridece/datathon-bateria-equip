# Recerca: el Campus Nord real en 3D (three.js)

*Data: 14/11/2026. Complementa `docs/RECERCA_DASHBOARD.md` §5 (estil maqueta, càmera isomètrica ortogràfica).*

**Fitxers generats**
- `dashboard/static/campus_nord.json` (~51 KB): l'escena llesta per a three.js, en metres locals.
- `dashboard/static/campus_nord_osm_raw.json` (~850 KB): dades OSM en brut retallades al campus (ODbL).
- `scripts/build_campus_json.py`: regenera el primer a partir del segon (`.venv/bin/python scripts/build_campus_json.py`).

---

## 0. Resum

- **40 edificis** dins del límit OSM "Campus Nord" (relation/19836574). **39 tenen nom**: A1–A6, B0–B6, C1–C6, D1–D6, Vèrtex, Omega, Nexus 1, Nexus 2, Biblioteca Rector Gabriel Ferraté, Poliesportiu, BSC‑Repsol, Capella Torre Girona (MareNostrum), Til·lers, Residència Torre Girona, i 4 pavellons d'1 planta entre aularis A. Un edifici petit a l'est de l'Omega no té nom a OSM.
- També hi ha **94 edificis veïns de context** (fins a 120 m del límit), simplificats a 16 punts com a màxim, per pintar‑los en gris.
- **Les plaques FV són reals i són a les cobertes dels aularis A1–A6.** OSM té 6 camps `power=generator, generator:source=solar, location=roof` sobre la fila A (un d'ells porta el nom "UPC - Edifici A2"). L'informe SIRENA 2023 de la UPC hi dona **170 kWp a A1–A4 i 80 kWp a A5–A6**. La Residència Torre Girona també té 2 camps FV a OSM.
- **Bateria, escomesa de xarxa i inversors: posicions SUPOSADES.** La ubicació real no s'ha publicat i la bateria del repte és hipotètica. Totes porten `"assumption": true`.
- Alçades: 35 surten de `building:levels × 3,5 m`. Les 2 sense plantes a OSM (B0 i Poliesportiu) porten el valor per defecte del tipus i `"estimated": true`, igual que l'edifici sense nom. OSM no té cap etiqueta `height` en aquests edificis.

## 1. Com s'han obtingut les dades

1. **Overpass API** (`overpass-api.de` i el mirall `overpass.kumi.systems`): 3 intents i tots han tornat *502 – server at capacity*. Per educació no hem insistit més.
2. **Alternativa: API oficial d'OSM 0.6** amb una sola petició de lectura:
   `https://api.openstreetmap.org/api/0.6/map.json?bbox=2.1075,41.3845,2.1185,41.3925`. Va tornar 5,5 MB amb tots els nodes, ways i relacions de la caixa. User‑Agent genèric, sense dades personals.
3. `build_campus_json.py --trim-from <bolcat>` el retalla a `campus_nord_osm_raw.json`. Hi queden el límit del campus, els edificis, les vies i els generadors FV de la caixa: 9.080 elements en format OSM JSON (nodes amb lat/lon + ways amb refs).
4. `build_campus_json.py` fa la resta. Projecta en equirectangular al voltant del centroide d'àrea del límit, simplifica amb Douglas‑Peucker (≤ 40 punts per edifici), assigna alçades i marca les plaques FV per punt‑dins‑polígon. Després hi afegeix els actius energètics.

Per refrescar amb Overpass quan funcioni, aquesta consulta dona un fitxer compatible (cal `out body` + nodes, o `out geom`; el script accepta tots dos formats):
```
[out:json][timeout:60];
( rel(19836574); way(r);
  way["building"](41.3845,2.1075,41.3925,2.1185); relation["building"](41.3845,2.1075,41.3925,2.1185);
  way["highway"](41.3845,2.1075,41.3925,2.1185);
  way["generator:source"="solar"](41.3845,2.1075,41.3925,2.1185); );
(._; >;); out body;
```

## 2. Format de `campus_nord.json`

| Clau | Contingut |
|---|---|
| `attribution` | `"© OpenStreetMap contributors, ODbL"` (mostrar‑ho a l'escena) |
| `crs` | `origin_latlon` = [41.3887481, 2.1134367]; **x = est, z = sud, y = amunt (m)**: el nord queda cap a −z, igual que el món de three.js |
| `bbox` | `buildings` [−276.8, −246.1, 297.2, 179.9] i `boundary` [−303.1, −248.1, 316.4, 205.7], format `[xmin, zmin, xmax, zmax]` en m |
| `boundary` | anell del límit del campus |
| `buildings[]` | `id`, `name`, `osm`, `building`, `levels`, `height_m`, `height_source`, `estimated`, `roof`, `has_pv` (true / "unknown"), `pv_area_m2`, `role` (text per al hover), `name_inferred`, `centroid` [x,z], `area_m2`, `polygon` [[x,z],…] (anell obert, antihorari amb el nord amunt), `holes` (patis del Vèrtex i del Nexus 1), `source` |
| `pv_arrays[]` | polígons reals dels camps FV (OSM), amb `area_m2` i `centroid` |
| `energy_assets` | `grid_connection.pos`, `battery.pos` + `size_m`, `pv_inverters[]` (`pos` [x,y,z] a la coberta), `campus_load_anchor` |
| `streets[]` | polilínies `{type, name?, line}`: carrers del voltant (Gran Capità, Jordi Girona, Sor Eulàlia d'Anzizu, Av. de Pedralbes…) i camins interiors (`footway`) |
| `context_buildings[]` | `{h, ring}` dels edificis veïns |

## 3. Llista d'edificis

H = alçada en m. "Nivells" vol dir `building:levels` d'OSM × 3,5 m.

| Nom | H (m) | Origen de l'alçada | FV | Font / nota |
|---|---|---|---|---|
| A1 | 17,5 | 5 nivells | **Sí** (367 m²) | OSM way/183542827 + FV way/1321485803 |
| A2 | 17,5 | 5 nivells | **Sí** (418 m²) | OSM way/187765241 + FV "UPC - Edifici A2" |
| A3 | 17,5 | 5 nivells | **Sí** (432 m²) | OSM way/187765243 |
| A4 | 17,5 | 5 nivells | **Sí** (391 m²) | OSM way/187765244. *Nom deduït* (fila A, FV a coberta) |
| A5 | 17,5 | 5 nivells | **Sí** (353 m²) | OSM way/187765249. *Nom deduït* |
| A6 | 17,5 | 5 nivells | **Sí** (367 m²) | OSM way/187765253. *Nom deduït* |
| Pav‑A1A2…Pav‑A4A5 (×4) | 3,5 | 1 nivell | ? | OSM way/1436110223–26. Sense nom, *nom posat per nosaltres* |
| B0 | 12,0 | **estimada** | ? | OSM way/595330170 |
| B1, B2, B4, B5 | 10,5 | 3 nivells | ? | OSM |
| B3 (ETSETB) | 10,5 | 3 nivells | ? | OSM way/1124652469, que té nom "ETSETB". *Lletra B3 deduïda per posició* |
| B6 | 10,5 | 3 nivells | ? | OSM way/642719991. *Nom deduït* (final de la fila B) |
| C1–C6 | 10,5 | 3 nivells | ? | OSM |
| D1–D6 | 10,5 | 3 nivells | ? | OSM |
| Edifici Omega | 17,5 | 5 nivells | ? | OSM way/642719972 |
| Edifici Vèrtex | 24,5 | 7 nivells | ? | OSM relation/8906511 (amb patis) |
| Nexus 1 | 14,0 | 4 nivells | ? | OSM relation/18116538 (circular, amb pati) |
| Nexus 2 | 14,0 | 4 nivells | ? | OSM way/642719966 |
| Biblioteca Rector Gabriel Ferraté | 14,0 | 4 nivells | ? | OSM way/642719980 |
| Poliesportiu UPC | 9,0 | **estimada** | ? | OSM way/187660313 |
| Edifici BSC‑Repsol | 14,0 | 4 nivells | ? | OSM way/593611153 |
| Capella Torre Girona (MareNostrum) | 10,5 | 3 nivells | ? | OSM way/642719955 ("Edifici Capella") |
| Edifici Til·lers | 10,5 | 3 nivells | ? | OSM way/642719945 |
| Residència Torre Girona | 21,0 | 6 nivells | **Sí** (187 m²) | OSM way/1444137905 + FV way/1444137910–11 |
| (sense nom, a l'est de l'Omega) | 7,0 | **estimada** | ? | OSM way/1451552792 |

Notes:
- No hem trobat cap edifici anomenat **K2M** ni **TG** dins del límit OSM. "Torre Girona" sí que hi surt, però com a Residència i com a Capella (BSC). Si cal el K2M, s'ha de buscar al plànol oficial de la UPC, que no hem pogut verificar en aquesta sessió.
- Que un edifici tingui `has_pv: "unknown"` no vol dir que no tingui plaques: només que OSM no en té cap registre.

## 4. Què és real i què és estimat

| Element | Estat |
|---|---|
| Petjades d'edificis, límit del campus, carrers | **Real** (OSM). Precisió de l'ordre del metre |
| Alçades | **Aproximades**: plantes OSM × 3,5 m. Tres són valors per defecte (`estimated: true`) |
| Cobertes | Planes per defecte (OSM només diu `roof:shape=flat` a A1–A3) |
| Plaques FV a A1–A6 i a la Residència | **Real** (OSM + SIRENA 2023). Inaugurades el 20/10/2020 |
| Potència FV del nostre model (3 inversors, ~145 kW) | Ve de les dades del repte. Els 250 kWp de SIRENA són la potència pic instal·lada, que no és el mateix |
| Agrupació dels inversors (INV1 = A1–A2, INV2 = A3–A4, INV3 = A5–A6) | **Suposició** |
| Escomesa/CT de xarxa (17,2, 0, 124,8) | **Suposició**: vora sud del límit (zona C/ Jordi Girona), al costat del Poliesportiu |
| Bateria 2 MWh / 500 kW (7,5, 0, 111,5), contenidor de 20 peus de 6,1 × 2,6 × 2,4 m | **Hipotètica**. És el primer punt lliure entre l'escomesa i el Poliesportiu (≥ 10 m de qualsevol edifici) |

A la UI, cal posar una etiqueta petita "ubicació il·lustrativa" a la bateria i a la xarxa.

## 5. Composició recomanada de l'escena

**Escala:** **1 unitat three.js = 10 m**, és a dir `S = 0.1`. El campus fa ~62 × 45 u, gairebé igual que el terra de 60 × 40 u previst a RECERCA_DASHBOARD §5.3. Alçades a escala ×1 (A = 1,75 u; Vèrtex = 2,45 u). Amb una exageració vertical ×1,5 la maqueta es llegeix millor des de la isomètrica, però cal dir‑ho al peu. Els actius energètics s'han de mostrar **com a símbols ampliats ×3–4**, perquè un contenidor de 6 m faria 0,6 u i no es veuria:

| Element | Posició JSON (m) | Posició en u (`×0.1`) | Representació |
|---|---|---|---|
| Centre de l'encuadrament | (10, 0, −33) | (1.0, 0, −3.3) | `controls.target` |
| Bateria | (7.5, 0, 111.5) | (0.75, 0, 11.15) | caixa de 2,4 × 1,0 × 1,0 u amb indicador de SoC, etiqueta CSS2D a y = 2 |
| Xarxa | (17.2, 0, 124.8) | (1.72, 0, 12.48) | torre/CT a la vora, amb cable cap a la bateria i el campus |
| Plaques solars | `pv_arrays[].ring` | ×0.1, y = H·S + 0.02 | pla prim de color `#3B4A5A` a la coberta, amb brillantor ∝ pv_kw/145 |
| Inversors | `pv_inverters[].pos` | ×0.1 | punt d'origen de les partícules solars (una corba per inversor) |
| Consum del campus | `campus_load_anchor` (Omega) | (3.76, 1.75, 1.64) | etiqueta "Campus · 1.840 kW" |

**Nus elèctric** (on convergeixen els 4 fluxos): el punt mig entre la bateria i l'escomesa, uns (12, 0, 118) m. Corbes:
- xarxa → nus
- inversors (A2/A4/A6) → nus, baixant de la coberta
- nus ↔ bateria
- nus → Omega, o bé repartit als centroides de les files B/C/D

**Càmera:**
- `OrthographicCamera` amb `target` (1, 0, −3.3) i posició `target + (40, 40, 40)`. Això mira cap al nord‑oest, en perpendicular a l'eix llarg del campus, que va de SO a NE. Les pintes A/B/C/D queden en diagonal i les cobertes FV de la fila A queden davant.
- Frustum: `halfH = 26`, `halfW = halfH·aspect`. Cal recalcular‑lo en fer `resize`.
- `OrbitControls`: polar 0,6–1,2, `enablePan:false`, `minZoom 0.8`, `maxZoom 5`.

**Ombres:** la càmera d'ombra del DirectionalLight ha de cobrir ±35 u al voltant del target. `shadow.mapSize` 2048.

**Colors** (paleta mat): edificis del campus `#F4F1EA`; context `#E2DDD2` sense ombres projectades; carrers `#DDD8CC` (línies o cintes de 0,6–1,2 u segons el `type`); límit del campus en línia discontínua `#B9B2A3`.

## 6. Extrusió dels polígons a three.js

```js
const S = 0.1;                                   // 1 u = 10 m
const data = JSON.parse(document.getElementById('campus').textContent); // injectat com __CAMPUS__
function shapeFrom(ring) {                       // ring: [[x,z],...] en metres
  const s = new THREE.Shape();
  ring.forEach(([x, z], i) => (i ? s.lineTo(x * S, -z * S) : s.moveTo(x * S, -z * S)));  // OJO: y_shape = -z
  s.closePath();
  return s;
}
const matCampus = new THREE.MeshStandardMaterial({ color: '#F4F1EA', roughness: .9, metalness: 0 });
const pickables = [];
for (const b of data.buildings) {
  const shape = shapeFrom(b.polygon);
  (b.holes || []).forEach(h => shape.holes.push(new THREE.Path(h.map(([x, z]) => new THREE.Vector2(x * S, -z * S)))));
  const geo = new THREE.ExtrudeGeometry(shape, { depth: b.height_m * S, bevelEnabled: true,
              bevelThickness: .03, bevelSize: .03, bevelSegments: 1 });
  geo.rotateX(-Math.PI / 2);          // (x, y_shape, depth) -> (x, depth, -y_shape) = (x, h, z)
  const m = new THREE.Mesh(geo, matCampus);
  m.castShadow = m.receiveShadow = true;
  m.userData = b;                      // per al hover: b.name, b.role, b.height_m, b.has_pv
  scene.add(m); pickables.push(m);
}
// plaques FV: forma plana just sobre la coberta
for (const p of data.pv_arrays) {
  const host = data.buildings.find(b => b.has_pv === true && Math.hypot(b.centroid[0]-p.centroid[0], b.centroid[1]-p.centroid[1]) < 40);
  const g = new THREE.ShapeGeometry(shapeFrom(p.ring)); g.rotateX(-Math.PI / 2);
  const pv = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: '#3B4A5A', roughness: .5, emissive: '#6B8BA8', emissiveIntensity: 0 }));
  pv.position.y = (host ? host.height_m : 17.5) * S + 0.02;
  scene.add(pv);
}
```
- Fusionar el context en una sola geometria (`BufferGeometryUtils.mergeGeometries`) dona 1 draw call en lloc de 94.
- El campus ocupa unes 40 malles, que es poden deixar separades per al raycast.
- Els anells ja venen en sentit antihorari en el pla (x, −z). Si mai sortís una cara invertida, `THREE.ShapeUtils.isClockWise` serveix per comprovar‑ho.
- Per incrustar el JSON (~51 KB), cal `str.replace("__CAMPUS__", json_text)` a Python, com amb el bundle de three (§5.2). No s'ha de fer amb f‑strings.

## 7. Mode "presentació en directe" (tour guiat)

Són keyframes de càmera (`target`, `zoom`, `azimut`). Entre keyframes s'interpola en 1,8 s amb *easeInOutCubic*: el target es fa amb `lerp` i l'angle amb `slerp` o interpolant l'azimut. Mentrestant, `OrbitControls` queda desactivat. Cada keyframe porta una llegenda sincronitzada (text HTML amb fade de 300 ms) i, si cal, fixa l'hora del reproductor:

| # | Pla | target (u) | zoom | azimut | Llegenda (exemple) | Acció |
|---|---|---|---|---|---|---|
| 1 | Vista general | (1, 0, −3.3) | 1.0 | 45° | "Campus Nord UPC · 40 edificis · ~1–2,5 MW de consum" | autorotació lenta 6 s |
| 2 | Cobertes solars | (−6.3, 1.75, 2.9) (fila A) | 2.4 | 30° | "250 kWp a les cobertes dels aularis A1–A6" | salt a les 13:00, plaques brillants, partícules grogues |
| 3 | Bateria | (0.75, 0, 11.15) | 4.0 | 60° | "Bateria 2 MWh / 500 kW · carrega quan el CO₂ és baix" | salt a "propera hora de càrrega" |
| 4 | Xarxa | (1.72, 0, 12.48) | 3.2 | 80° | "Xarxa: el color del cable = g CO₂/kWh de l'hora" | salt al "pic de CO₂ següent": descàrrega |
| 5 | Tornada | (1, 0, −3.3) | 1.0 | 45° | "Resultat: −X kg CO₂ · −Y € en 12 setmanes" | comptadors animats |

- Controls: tecla `P` (o botó "Presentació") per començar o aturar, `→`/`←` per passar keyframe a mà mentre es parla, `Esc` per tornar a l'òrbita lliure.
- Cal respectar `prefers-reduced-motion`: transicions instantànies.
- La llegenda va en un `<div>` a sota, no dins del canvas, perquè es llegeixi al projector.

## 8. Interacció

- **Hover sobre un edifici** (Raycaster sobre `pickables`): contorn (o `emissive` +0,15) i tooltip amb `name` · `role` · `height_m` m · "Plaques FV" si `has_pv === true`. Exemples: "A2 · Aulari · coberta solar (418 m²) · produeix 52 kW ara". Si `name_inferred`, s'hi afegeix "(nom deduït)".
- **Hover sobre els camps FV**: kW instantanis de l'inversor associat.
- **Clic sobre la bateria**: panell lateral amb el SoC, kW (signe), l'acció de l'agent i el "per què" (frase de la §5.4), més una mini‑sèrie de 24 h. Un segon clic o `Esc` el tanca.
- **Clic sobre la xarxa**: g CO₂/kWh, €/kWh i la previsió de 24 h.
- **Doble clic** sobre qualsevol element: la càmera hi vola (reutilitza la funció del tour).
- **Llegenda d'atribució** fixa a la cantonada inferior dreta: "© OpenStreetMap contributors, ODbL".

## 9. Llicències i atribució

- **Geometria: © OpenStreetMap contributors, ODbL 1.0.** L'atribució ha de ser visible a l'escena o a la pàgina on es mostra. `campus_nord.json` és una *base de dades derivada*: si es publica, ha de mantenir l'ODbL (*share‑alike*) i l'atribució. Una imatge o un render (*produced work*) només demana l'atribució. Totes dues claus són al JSON (`attribution`, `license`).
- No s'han fet servir imatges, plànols ni geometria de la UPC. Les dades de la UPC (SIRENA) només s'han fet servir com a fet: on hi ha plaques i quants kWp.
- three.js té llicència MIT (vegeu §5.2 del document del dashboard).

## 10. Fonts

- OpenStreetMap: relació "Campus Nord" https://www.openstreetmap.org/relation/19836574 · API emprada https://api.openstreetmap.org/api/0.6/map.json?bbox=2.1075,41.3845,2.1185,41.3925 · Copyright i ODbL https://www.openstreetmap.org/copyright · https://opendatacommons.org/licenses/odbl/
- Overpass API (intentat, 502): https://overpass-api.de/api/interpreter
- Camps FV a OSM: https://www.openstreetmap.org/way/1321485802 ("UPC - Edifici A2") i ways 1321485798–1321485803, 1444137910–11
- UPC Sostenible, Informe SIRENA 2020 (planta FV del Campus Nord acabada l'octubre de 2020, 170 kW): https://sostenible.upc.edu/ca/reptes/documents-pla-2030/informe-sirena-2020.pdf
- UPC Sostenible, Informe SIRENA 2023 (170 kWp a Aularis A1–A4, 80 kWp a A5–A6): https://sostenible.upc.edu/ca/reptes/documents-pla-2030/informe-sirena-2023.pdf
- Informe SIRENA 2024: https://sostenible.upc.edu/ca/reptes/documents-pla-2030/informe-sirena-2024.pdf
- Memòria Digital UPC, "Acte virtual d'inauguració de les plaques solars al Campus Nord (20/10/2020)": https://memoriadigital.upc.edu/collections/show/4315 (col·lecció https://memoriadigital.upc.edu/collections/show/945)
- Web del campus (etiqueta `website` d'OSM): https://www.upc.edu/campusnord/
- three.js: ExtrudeGeometry https://threejs.org/docs/#api/en/geometries/ExtrudeGeometry · Shape https://threejs.org/docs/#api/en/extras/core/Shape · OrthographicCamera https://threejs.org/docs/#api/en/cameras/OrthographicCamera
