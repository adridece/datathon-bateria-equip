"""Regenera dashboard/static/campus_nord.json a partir de les dades OSM en brut.

Ús:
    .venv/bin/python scripts/build_campus_json.py
    .venv/bin/python scripts/build_campus_json.py --trim-from bolcat_complet.json   # (opcional)

Entrada: dashboard/static/campus_nord_osm_raw.json
    Llista "elements" en format OSM JSON (API 0.6 /map.json o Overpass `out body` amb
    nodes): nodes amb lat/lon i ways amb llista de refs de nodes. També accepta ways
    amb "geometry" (Overpass `out geom`).
    --trim-from: retalla un bolcat gran (p. ex. https://api.openstreetmap.org/api/0.6/
    map.json?bbox=2.1075,41.3845,2.1185,41.3925) i el desa com a fitxer en brut.

Sortida: dashboard/static/campus_nord.json (coordenades locals en metres).
    Origen = centroide (d'àrea) del límit OSM "Campus Nord" (relació 19836574).
    x = metres cap a l'EST, z = metres cap al SUD  (=> coincideix amb el món de three.js
    amb el nord cap a -z). Projecció equirectangular al voltant de l'origen.

Dades: © OpenStreetMap contributors, ODbL 1.0 (https://www.openstreetmap.org/copyright).
Només stdlib + numpy.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "dashboard" / "static" / "campus_nord_osm_raw.json"
OUT = ROOT / "dashboard" / "static" / "campus_nord.json"

ATTRIBUTION = "© OpenStreetMap contributors, ODbL"
CAMPUS_REL = 19836574          # relació multipolygon "Campus Nord" (UPC)
LEVEL_H = 3.5                  # m per planta
MAX_PTS = 40
CONTEXT_BUFFER_M = 120         # edificis veïns (context gris) fins a aquesta distància del límit
BBOX = (41.3845, 2.1075, 41.3925, 2.1185)  # S, W, N, E (només per retallar)

# Fonts dels noms que OSM no porta a "name"
UPC_TENDER_2009 = ("https://seuelectronica.upc.edu/ca/perfil-de-contractant/historic-de-licitacions/"
                   "Licitacions_Previes_28-feb-2011/procediments-oberts-any-2009-carpeta/"
                   "conse160000ho2009111-83/plec-tec.pdf")
# Noms confirmats: OSM hi posa addr:housenumber (A4, A5, A6, B6) i la UPC els llista al plec de
# manteniment del Campus Nord (2009). B3 = ETSETB ho diu la mateixa escola.
CONFIRMED_NAMES = {
    187765244: ("A4", UPC_TENDER_2009),
    187765249: ("A5", UPC_TENDER_2009),
    187765253: ("A6", UPC_TENDER_2009),
    1124652469: ("B3", "https://telecos.upc.edu/ca"),
    642719991: ("B6", "https://www.fib.upc.edu/en/contact"),
}
# Pavellons d'1 planta sense nom públic: posem un nom descriptiu (no és cap nom oficial)
DESCRIPTIVE_NAMES = {
    1436110226: ("Pav-A1A2", "Pavelló entre A1 i A2"),
    1436110225: ("Pav-A2A3", "Pavelló entre A2 i A3"),
    1436110224: ("Pav-A3A4", "Pavelló entre A3 i A4"),
    1436110223: ("Pav-A4A5", "Pavelló entre A4 i A5"),
}
DISPLAY_NAMES = {
    1124652469: "B3 (ETSETB)",
    642719991: "B6 (FIB)",
    642719955: "Capella Torre Girona (BSC, MareNostrum)",
}
# Generadors FV OSM -> edifici (comprovat amb punt-dins-polígon, aquí només per etiquetar)
DEFAULT_H = {"university": 12.0, "office": 12.0, "stadium": 9.0, "dormitory": 18.0,
             "yes": 7.0, "bridge": 6.0}
ROLE = {  # paper a l'escena (per a hover). Clau = nom.
    **{f"A{i}": "Aulari (aules). Coberta amb plaques FV" for i in range(1, 7)},
    **{f"B{i}": "Departaments / ETSETB" for i in range(0, 7)},
    "B6": "Facultat d'Informàtica de Barcelona (FIB)",
    **{f"C{i}": "Departaments i laboratoris" for i in range(1, 7)},
    **{f"D{i}": "Departaments i laboratoris" for i in range(1, 7)},
    "Biblioteca Rector Gabriel Ferraté": "Biblioteca",
    "Edifici Omega": "Departaments, recerca (FIB/ETSECCPB)",
    "Edifici Vèrtex": "Serveis generals i rectorat (part)",
    "Nexus 1": "Recerca / transferència",
    "Nexus 2": "Recerca / transferència",
    "Poliesportiu UPC": "Poliesportiu",
    "Edifici BSC-Repsol": "Barcelona Supercomputing Center",
    "Edifici Capella": "MareNostrum (BSC)",
    "Residencia Universitaria Torre Girona": "Residència d'estudiants",
    "Edifici Til·lers": "Oficines",
    **{k: "Pavelló d'1 planta entre aularis A (sense nom a OSM)" for k in
       ("Pav-A1A2", "Pav-A2A3", "Pav-A3A4", "Pav-A4A5")},
}
KEEP_HIGHWAY = {"primary", "secondary", "tertiary", "residential", "pedestrian",
                "service", "footway", "cycleway", "living_street", "unclassified", "path"}


# ---------------------------------------------------------------- geometria
def pip(pt, poly) -> bool:
    x, y = pt
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def area_centroid(poly):
    a = np.asarray(poly, float)
    x, y = a[:, 0], a[:, 1]
    xs, ys = np.roll(x, -1), np.roll(y, -1)
    cr = x * ys - xs * y
    A = cr.sum() / 2
    if abs(A) < 1e-12:
        return float(x.mean()), float(y.mean()), 0.0
    return float(((x + xs) * cr).sum() / (6 * A)), float(((y + ys) * cr).sum() / (6 * A)), float(A)


def dp(points, tol):
    """Douglas-Peucker sobre una polilínia (llista de (x,z))."""
    if len(points) < 3:
        return list(points)
    p = np.asarray(points, float)
    a, b = p[0], p[-1]
    ab = b - a
    L = np.hypot(*ab)
    if L < 1e-9:
        d = np.hypot(*(p - a).T)
    else:
        d = np.abs(ab[0] * (p[:, 1] - a[1]) - ab[1] * (p[:, 0] - a[0])) / L
    i = int(d.argmax())
    if d[i] > tol:
        return dp(points[: i + 1], tol)[:-1] + dp(points[i:], tol)
    return [points[0], points[-1]]


def simplify_ring(ring, tol=0.4, max_pts=MAX_PTS):
    r = list(ring)
    if r[0] == r[-1]:
        r = r[:-1]
    if len(r) <= 3:
        return r
    # trenca l'anell pel punt més llunyà del primer per fer DP en dos trams
    far = int(np.argmax([math.dist(r[0], q) for q in r]))
    while True:
        out = dp(r[: far + 1], tol)[:-1] + dp(r[far:] + [r[0]], tol)[:-1]
        if len(out) <= max_pts or tol > 20:
            return out
        tol *= 1.5


def ccw(ring):
    """Ordre antihorari en el pla (x, -z) (= nord amunt), el que espera THREE.Shape."""
    _, _, A = area_centroid([(x, -z) for x, z in ring])
    return ring if A > 0 else ring[::-1]


# ---------------------------------------------------------------- OSM
def load(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    els = d["elements"]
    nodes = {e["id"]: (e["lat"], e["lon"]) for e in els if e["type"] == "node" and "lat" in e}
    ways, rels = {}, {}
    for e in els:
        if e["type"] == "way":
            if "geometry" in e:
                e["_ll"] = [(g["lat"], g["lon"]) for g in e["geometry"] if g]
            else:
                e["_ll"] = [nodes[n] for n in e.get("nodes", []) if n in nodes]
            ways[e["id"]] = e
        elif e["type"] == "relation":
            rels[e["id"]] = e
    return d, els, nodes, ways, rels


def stitch(ways, ids):
    """Uneix ways (outer) en un anell tancat de (lat,lon)."""
    segs = [list(ways[i]["_ll"]) for i in ids if i in ways]
    if not segs:
        return []
    ring = segs.pop(0)
    while segs:
        for k, s in enumerate(segs):
            if s[0] == ring[-1]:
                ring += s[1:]
            elif s[-1] == ring[-1]:
                ring += s[::-1][1:]
            else:
                continue
            segs.pop(k)
            break
        else:  # no encaixa: concatena igualment
            ring += segs.pop(0)
    return ring


def trim(full_path, out_path):
    """Retalla un bolcat gran: límit del campus + edificis/vies/FV del voltant."""
    d, els, nodes, ways, rels = load(full_path)
    S, W, N, E = BBOX
    keep_w, keep_r = set(), set()
    camp = rels[CAMPUS_REL]
    keep_r.add(CAMPUS_REL)
    keep_w |= {m["ref"] for m in camp["members"] if m["type"] == "way"}
    for w in ways.values():
        t = w.get("tags", {})
        if not ("building" in t or "highway" in t or "power" in t or "generator:source" in t):
            continue
        if "highway" in t and t["highway"] not in KEEP_HIGHWAY:
            continue
        if any(S < la < N and W < lo < E for la, lo in w["_ll"]):
            keep_w.add(w["id"])
    for r in rels.values():
        t = r.get("tags", {})
        if "building" in t:
            outs = [m["ref"] for m in r["members"] if m["type"] == "way"]
            if any(o in ways and any(S < la < N and W < lo < E for la, lo in ways[o]["_ll"]) for o in outs):
                keep_r.add(r["id"])
                keep_w |= {o for o in outs if o in ways}
    keep_n = set()
    for i in keep_w:
        keep_n |= set(ways[i].get("nodes", []))
    out = []
    for e in els:
        if e["type"] == "node" and (e["id"] in keep_n or (
                "power" in e.get("tags", {}) and S < e["lat"] < N and W < e["lon"] < E)):
            out.append({k: e[k] for k in ("type", "id", "lat", "lon", "tags") if k in e})
        elif e["type"] == "way" and e["id"] in keep_w:
            out.append({k: e[k] for k in ("type", "id", "nodes", "tags") if k in e})
        elif e["type"] == "relation" and e["id"] in keep_r:
            out.append({k: e[k] for k in ("type", "id", "members", "tags") if k in e})
    res = {
        "version": d.get("version", "0.6"),
        "generator": d.get("generator", ""),
        "attribution": ATTRIBUTION,
        "license": "ODbL 1.0 — https://opendatacommons.org/licenses/odbl/ ; https://www.openstreetmap.org/copyright",
        "source": "OpenStreetMap API 0.6 map.json bbox=2.1075,41.3845,2.1185,41.3925 (retallat per scripts/build_campus_json.py --trim-from)",
        "retrieved": "2026-11-14",
        "elements": out,
    }
    Path(out_path).write_text(json.dumps(res, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"raw retallat: {len(out)} elements -> {out_path}")


# ---------------------------------------------------------------- construcció
def build(raw_path=RAW, out_path=OUT):
    d, els, nodes, ways, rels = load(raw_path)
    camp = rels[CAMPUS_REL]
    boundary_ll = stitch(ways, [m["ref"] for m in camp["members"] if m["role"] == "outer"])
    lat0 = sum(p[0] for p in boundary_ll) / len(boundary_ll)
    lon0 = sum(p[1] for p in boundary_ll) / len(boundary_ll)
    R = 6371008.8
    kx = math.radians(1) * R * math.cos(math.radians(lat0))
    ky = math.radians(1) * R

    def P(ll):  # (lat,lon) -> (x est, z sud) en m
        return ((ll[1] - lon0) * kx, -(ll[0] - lat0) * ky)

    # recentra a l'àrea-centroide del límit
    b0 = [P(p) for p in boundary_ll]
    cx, cz, _ = area_centroid(b0)
    lon0 += cx / kx
    lat0 -= cz / ky
    boundary = [P(p) for p in boundary_ll]
    boundary_xy = [(x, z) for x, z in boundary]

    def r1(v):
        return round(v, 1)

    def ring_out(ll_ring, tol=0.4):
        return [[r1(x), r1(z)] for x, z in ccw(simplify_ring([P(p) for p in ll_ring], tol))]

    def dist_to_boundary(pt):
        best = 1e9
        for i in range(len(boundary_xy)):
            a = np.array(boundary_xy[i - 1]); b = np.array(boundary_xy[i]); p = np.array(pt)
            ab = b - a
            t = np.clip(np.dot(p - a, ab) / max(np.dot(ab, ab), 1e-9), 0, 1)
            best = min(best, float(np.hypot(*(p - (a + t * ab)))))
        return best

    # generadors FV
    pv = []
    for w in ways.values():
        t = w.get("tags", {})
        if t.get("generator:source") == "solar" and len(w["_ll"]) >= 3:
            ring = [P(p) for p in w["_ll"]]
            cx_, cz_, A = area_centroid(ring)
            pv.append({"osm": f"way/{w['id']}", "c": (cx_, cz_), "area_m2": round(abs(A)),
                       "ring": [[r1(x), r1(z)] for x, z in ccw(simplify_ring(ring, 0.3))]})

    # edificis (ways + relacions multipolygon)
    cands = []
    in_rel = set()
    for r in rels.values():
        t = r.get("tags", {})
        if "building" not in t:
            continue
        outs = [m["ref"] for m in r["members"] if m["role"] == "outer" and m["ref"] in ways]
        inners = [m["ref"] for m in r["members"] if m["role"] == "inner" and m["ref"] in ways]
        if not outs:
            continue
        in_rel |= set(outs) | set(inners)
        cands.append(("relation", r["id"], t, stitch(ways, outs),
                      [ways[i]["_ll"] for i in inners if len(ways[i]["_ll"]) >= 4]))
    for w in ways.values():
        t = w.get("tags", {})
        if "building" in t and w["id"] not in in_rel and len(w["_ll"]) >= 4:
            cands.append(("way", w["id"], t, w["_ll"], []))

    buildings, context = [], []
    for typ, oid, t, ll, holes in cands:
        if t.get("building") in ("bridge", "roof"):
            continue
        ring_m = [P(p) for p in ll]
        cx_, cz_, A = area_centroid(ring_m)
        inside = pip((cx_, cz_), boundary_xy)
        if not inside:
            if dist_to_boundary((cx_, cz_)) > CONTEXT_BUFFER_M or abs(A) < 40:
                continue
        # alçada
        h, src, est = None, None, False
        if "height" in t:
            try:
                h, src = float(str(t["height"]).split()[0]), "osm:height"
            except ValueError:
                pass
        if h is None and "building:levels" in t:
            try:
                h, src = float(t["building:levels"]) * LEVEL_H, "osm:building:levels×3.5"
            except ValueError:
                pass
        if h is None:
            h, src, est = DEFAULT_H.get(t.get("building"), 9.0), "default_by_type", True
        if not inside:
            ring = ring_out(ll, tol=1.0)
            if len(ring) > 16:
                ring = [[r1(x), r1(z)] for x, z in ccw(simplify_ring([P(p) for p in ll], 1.5, 16))]
            context.append({"h": round(h, 1), "ring": ring})
            continue
        name, display, name_src = t.get("name"), None, f"OSM {typ}/{oid}"
        if oid in CONFIRMED_NAMES:
            name, name_src = CONFIRMED_NAMES[oid]
        elif oid in DESCRIPTIVE_NAMES:
            name, display = DESCRIPTIVE_NAMES[oid]
            name_src = "nom descriptiu (sense nom públic)"
        pv_here = [g for g in pv if pip(g["c"], ring_m)]
        b = {
            "id": name or f"{typ}/{oid}",
            "name": display or DISPLAY_NAMES.get(oid, name) if name else None,
            "osm": f"{typ}/{oid}",
            "building": t.get("building"),
            "levels": int(float(t["building:levels"])) if "building:levels" in t else None,
            "height_m": round(h, 1),
            "height_source": src,
            "estimated": est,
            "roof": t.get("roof:shape", "flat (assumit)"),
            "has_pv": True if pv_here else "unknown",
            "pv_area_m2": sum(g["area_m2"] for g in pv_here) or None,
            "role": ROLE.get(name, "Edifici universitari" if t.get("building") == "university" else "Edifici sense nom a OSM"),
            "name_inferred": False,
            "name_source": name_src,
            "centroid": [r1(cx_), r1(cz_)],
            "area_m2": round(abs(A)),
            "polygon": ring_out(ll),
            "source": f"OSM {typ}/{oid}",
        }
        if holes:
            b["holes"] = [[[r1(x), r1(z)] for x, z in simplify_ring([P(p) for p in hr], 0.5, 20)] for hr in holes]
        if t.get("building:levels") is None and t.get("height") is None:
            b["estimated"] = True
        buildings.append({k: v for k, v in b.items() if v is not None})
    # els edificis A amb FV: SIRENA 2023 confirma plaques a A1–A6
    for b in buildings:
        if b["id"] in {f"A{i}" for i in range(1, 7)}:
            b["has_pv"] = True
    buildings.sort(key=lambda b: str(b["id"]))

    # vies
    streets = []
    for w in ways.values():
        t = w.get("tags", {})
        hw = t.get("highway")
        if hw not in KEEP_HIGHWAY or len(w["_ll"]) < 2:
            continue
        pts = [P(p) for p in w["_ll"]]
        # retalla a una caixa al voltant del campus
        xs = [p[0] for p in boundary_xy]; zs = [p[1] for p in boundary_xy]
        box = (min(xs) - 60, max(xs) + 60, min(zs) - 60, max(zs) + 60)
        inb = [box[0] < x < box[1] and box[2] < z < box[3] for x, z in pts]
        if not any(inb):
            continue
        if hw in ("footway", "path", "service", "cycleway") and not any(pip(p, boundary_xy) for p in pts):
            continue  # voreres de fora: soroll
        pts = [p for p, k in zip(pts, inb) if k]
        if len(pts) < 2:
            continue
        line = dp(pts, 0.8)
        streets.append({"type": hw, **({"name": t["name"]} if "name" in t else {}),
                        "line": [[r1(x), r1(z)] for x, z in line]})

    # ---------------------------------------------- elements energètics (SUPOSICIONS)
    byid = {b["id"]: b for b in buildings}

    def roof(bid):
        b = byid[bid]
        return [b["centroid"][0], b["height_m"], b["centroid"][1]]

    def mid(a, b, f=0.5):
        return [r1(a[0] + (b[0] - a[0]) * f), r1(a[1] + (b[1] - a[1]) * f)]

    poli = byid.get("Poliesportiu UPC") or byid["A1"]
    # escomesa / CT de xarxa: vora sud del campus (C/ Jordi Girona), punt del límit
    # més proper al poliesportiu
    pc = np.array(poli["centroid"])
    gi = int(np.argmin([math.dist(pc, q) for q in boundary_xy]))
    grid_xz = [r1(boundary_xy[gi][0]), r1(boundary_xy[gi][1])]

    def clear(pt, margin=6.0):
        for b in buildings:
            poly = [tuple(q) for q in b["polygon"]]
            if pip(pt, poly) or min(math.dist(pt, q) for q in poly) < margin + 4:
                return False
        return True

    # bateria: espai obert entre l'escomesa i el poliesportiu (primer punt lliure)
    bat_xz = None
    for f in np.linspace(0.25, 0.9, 27):
        cand = mid(grid_xz, poli["centroid"], float(f))
        if clear(cand):
            bat_xz = cand
            break
    if bat_xz is None:
        bat_xz = mid(grid_xz, poli["centroid"], 0.3)
    inverters = [
        {"id": "INV1", "serves": ["A1", "A2"], "pos": [r1(x) for x in roof("A2")]},
        {"id": "INV2", "serves": ["A3", "A4"], "pos": [r1(x) for x in roof("A4")]},
        {"id": "INV3", "serves": ["A5", "A6"], "pos": [r1(x) for x in roof("A6")]},
    ]
    def free_spot(anchor, margin=3.0):
        """Punt lliure més proper a `anchor` (dins del campus i a `margin` m de tot edifici)."""
        for r in range(0, 80, 2):
            for k in range(max(1, r * 2)):
                a = 2 * math.pi * k / max(1, r * 2)
                cand = [r1(anchor[0] + r * math.cos(a)), r1(anchor[1] + r * math.sin(a))]
                if pip(cand, boundary_xy) and clear(cand, margin - 4):
                    return cand
        return [r1(anchor[0]), r1(anchor[1])]

    # Punts de connexió a la xarxa. La UPC no publica on són els seus CT: només el de BSC
    # (subestació 110/25 kV) està documentat. La resta són una proposta raonada
    # (veure docs/RECERCA_ELECTRICA_CAMPUS.md).
    aularis = ["A1", "A2", "A3", "A4", "A5", "A6", "Pav-A1A2", "Pav-A2A3", "Pav-A3A4", "Pav-A4A5",
               "Biblioteca Rector Gabriel Ferraté", "Poliesportiu UPC", "Nexus 1"]
    modules = [f"{c}{i}" for c in "BCD" for i in range(0, 7) if f"{c}{i}" in byid]
    omega = ["Edifici Omega", "Nexus 2", "way/1451552792"]
    vertex = ["Edifici Vèrtex"]
    bsc = ["Edifici BSC-Repsol", "Edifici Capella"]
    doc_url = "docs/RECERCA_ELECTRICA_CAMPUS.md"
    grid_connections = [
        {"id": "upc_main", "kind": "escomesa_mt", "main": True,
         "name": "Escomesa principal UPC (mitja tensió) + CT aularis",
         "pos": [grid_xz[0], 0.0, grid_xz[1]], "feeds": aularis,
         "confidence": "proposta", "source": doc_url,
         "note": "Posició no publicada. Vora del C/ Jordi Girona (accés principal, xarxa d'Endesa sota la vorera), al costat del poliesportiu i de les plaques FV dels aularis A."},
        {"id": "ct_modules", "kind": "ct", "name": "CT mòduls B, C i D", "near": "C3",
         "feeds": modules, "confidence": "proposta", "source": doc_url,
         "note": "24 mòduls de 3 plantes (~75.000 m²): calen 1-2 transformadors més. Posició il·lustrativa al centre de les files."},
        {"id": "ct_omega", "kind": "ct", "name": "CT Omega (CPD)", "near": "Edifici Omega",
         "feeds": omega, "confidence": "proposta", "source": doc_url,
         "note": "L'Omega té el CPD central de la UPC (6 % de l'electricitat de tota la UPC, SIRENA 2010) i SAI propi."},
        {"id": "ct_vertex", "kind": "ct", "name": "CT Vèrtex", "near": "Edifici Vèrtex",
         "feeds": vertex, "confidence": "proposta", "source": doc_url,
         "note": "Edifici de 18.574 m² construït a part (anys 2000): és habitual que tingui CT propi."},
        {"id": "bsc_substation", "kind": "subestacio_at", "name": "Subestació BSC 110/25 kV (soterrada)",
         "pos": [byid["Edifici BSC-Repsol"]["centroid"][0], 0.0, byid["Edifici BSC-Repsol"]["centroid"][1]]
         if "Edifici BSC-Repsol" in byid else None,
         "feeds": bsc, "underground": True, "upc_meter": False, "confidence": "documentada",
         "source": "https://ewebapps.bsc.es/tenders/ca/download/file/tender-file/47",
         "note": "Del BSC, no de la UPC: 2 transformadors de 20/25 MVA, 20 MW contractats, línia de 110 kV d'Endesa. Posició exacta dins de l'edifici no publicada."},
    ]
    # els CT proposats van al primer espai lliure al costat de l'edifici de referència
    for g in grid_connections:
        if g.get("pos") is None:
            xz = free_spot(byid[g.pop("near")]["centroid"])
            g["pos"] = [xz[0], 0.0, xz[1]]
    # anell intern de mitja tensió (proposta): escomesa -> CT
    mv_links = [["upc_main", "ct_modules"], ["upc_main", "ct_omega"], ["ct_omega", "ct_vertex"]]

    allx = [p[0] for b in buildings for p in b["polygon"]]
    allz = [p[1] for b in buildings for p in b["polygon"]]

    out = {
        "attribution": ATTRIBUTION,
        "license": "Dades geogràfiques: ODbL 1.0 (https://www.openstreetmap.org/copyright). Valors energètics: projecte Datathon.",
        "generated_by": "scripts/build_campus_json.py",
        "crs": {
            "origin_latlon": [round(lat0, 7), round(lon0, 7)],
            "origin": "centroide d'àrea del límit OSM 'Campus Nord' (relation/19836574)",
            "units": "metres",
            "axes": "x = est, z = sud, y = amunt (món three.js; nord = -z)",
            "projection": "equirectangular local (error < 1 cm a l'escala del campus)",
            "polygons": "anells oberts [[x,z],...], antihoraris vistos amb el nord amunt; per a THREE.Shape useu (x, -z) i rotateX(-PI/2)",
        },
        "bbox": {"buildings": [r1(min(allx)), r1(min(allz)), r1(max(allx)), r1(max(allz))],
                 "boundary": [r1(min(p[0] for p in boundary_xy)), r1(min(p[1] for p in boundary_xy)),
                              r1(max(p[0] for p in boundary_xy)), r1(max(p[1] for p in boundary_xy))],
                 "format": "[xmin, zmin, xmax, zmax]"},
        "boundary": [[r1(x), r1(z)] for x, z in ccw(simplify_ring(boundary_xy, 1.0, 60))],
        "buildings": buildings,
        "pv_arrays": [{k: v for k, v in g.items() if k != "c"} | {"centroid": [r1(g["c"][0]), r1(g["c"][1])]}
                      for g in sorted(pv, key=lambda g: g["c"][0])],
        "energy_assets": {
            "grid_connection": {"pos": [grid_xz[0], 0.0, grid_xz[1]], "assumption": True, "id": "upc_main",
                                "note": "Connexió principal (compatibilitat). Llista completa a grid_connections."},
            "grid_connections": grid_connections,
            "mv_links": mv_links,
            "battery": {"pos": [bat_xz[0], 0.0, bat_xz[1]], "size_m": [6.1, 2.6, 2.4],
                        "rotation_y_deg": 0, "capacity_kwh": 2000, "power_kw": 500, "assumption": True,
                        "connects_to": "upc_main",
                        "note": "Bateria hipotètica del repte (contenidor de 20 peus). Ubicació proposada.",
                        "rationale": ("Al costat de l'escomesa principal, on es troben la xarxa i les plaques dels aularis A "
                                      "(menys pèrdues i el mateix punt de mesura). Espai obert pavimentat, accessible "
                                      "des del C/ Jordi Girona per a un camió i per als bombers, i a més de 10 m de qualsevol edifici.")},
            "pv_inverters": [dict(i, assumption=True) for i in inverters],
            "pv_note": "Plaques FV reals a les cobertes dels aularis A1–A6 (OSM power=generator, location=roof; SIRENA 2023: 170 kWp A1–A4 + 80 kWp A5–A6). L'agrupació en 3 inversors és una suposició.",
            "campus_load_anchor": {"pos": [r1(x) for x in roof("Edifici Omega")], "note": "Punt d'ancoratge per a l'etiqueta de consum del campus."},
        },
        "streets": streets,
        "context_buildings": context,
    }
    txt = json.dumps(out, ensure_ascii=False, separators=(",", ":"))
    Path(out_path).write_text(txt, encoding="utf-8")
    print(f"{len(buildings)} edificis campus ({sum(1 for b in buildings if b.get('name'))} amb nom), "
          f"{len(context)} de context, {len(pv)} camps FV, {len(streets)} vies -> {out_path} ({len(txt)/1024:.0f} KB)")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--trim-from", help="bolcat OSM gran a retallar cap a campus_nord_osm_raw.json")
    ap.add_argument("--raw", default=str(RAW))
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    if a.trim_from:
        trim(a.trim_from, a.raw)
    build(a.raw, a.out)
