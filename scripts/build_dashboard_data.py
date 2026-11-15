"""
Genera dashboard/data/data.js amb totes les dades que fa servir la web del dashboard, una clau per mode
(estandard: estandard_robust; dificil: dificil_marges amb 6.000 kWh, +-1.500 kW i la solar x12).
Tot surt del simulador oficial, aixi les xifres quadren amb el leaderboard i entre elles.

    python scripts/build_dashboard_data.py
"""
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dashboard import analysis as an  # noqa: E402
from src.data import contiguous_blocks, load_hourly  # noqa: E402

OUT = ROOT / "dashboard" / "data" / "data.js"


def refs(agent):
    """CO2 i preu de referencia de l'agent (normalitzen els pesos 70/30), els mateixos que fa servir per decidir."""
    p = json.loads((ROOT / "agents" / agent / "params.json").read_text(encoding="utf-8"))
    return float(p["co2_ref"]), float(p.get("price_ref", p.get("preu_ref")))


def why_text(d, agent):
    # frase curta que explica la decisio de cada hora
    co2_ref, price_ref = refs(agent)
    w = (0.7 * d.co2_kg_per_kwh / co2_ref + 0.3 * d.precio_eur_per_kwh / price_ref).values
    surplus = (d.pv_kw - d.load_kw).values
    out = []
    for k in range(len(d)):
        ahead = w[k:k + 24]
        rank = int((ahead < w[k]).sum()) + 1
        b, soc = d.bat_kw.iloc[k], d.soc_pct.iloc[k]
        if b > 1 and surplus[k] > 1:
            out.append(f"Carrega {b:.0f} kW amb l'excedent solar: és energia gratis i sense CO₂.")
        elif b > 1:
            out.append(f"Carrega {b:.0f} kW: és la {rank}a hora més neta de les properes {len(ahead)}.")
        elif b < -1:
            out.append(f"Descarrega {-b:.0f} kW: hora bruta i cara, el campus compra {-b:.0f} kW menys a la xarxa.")
        elif soc > 0.99:
            out.append("Espera plena: guarda l'energia per a una hora més bruta.")
        elif soc < 0.01:
            out.append("Espera buida: ja ho ha descarregat tot a les hores dolentes.")
        else:
            out.append("Espera: moure energia ara perdria més (10 % per cicle) del que estalviaria.")
    return out


def weekly(d, rules, weeks, oracle_weeks, cap):
    """Rendiment de cada setmana: el que estalvia, el que treu respecte de l'òptim i el desgast de la bateria."""
    rows = []
    for w, o in zip(weeks, oracle_weeks):
        p, r = d.iloc[w["start"]:w["end"]], rules.iloc[w["start"]:w["end"]]
        co2_base, eur_base = p.co2_base_kg.sum(), p.cost_base_eur.sum()
        co2_s, eur_s = co2_base - p.co2_kg.sum(), eur_base - p.cost_eur.sum()
        mix = lambda c, e: 0.7 * c / co2_base + 0.3 * e / eur_base   # mateixa ponderació 70/30
        rows.append({
            "label": w["label"], "co2_kg": round(co2_s, 1), "eur": round(eur_s, 1),
            "co2_pct": round(100 * co2_s / co2_base, 2), "cost_pct": round(100 * eur_s / eur_base, 2),
            "of_best_pct": round(100 * mix(co2_s, eur_s) / mix(o["co2_saved_kg"], o["eur_saved"]), 1),
            "rules_co2_kg": round(co2_base - r.co2_kg.sum(), 1),
            "cycles": round(float(p.bat_kw.clip(upper=0).abs().sum()) / cap, 2),
            "min_net_kw": round(float(p.grid_kw.min()), 0),
        })
    return rows


def save_history(data, agent):
    """Guarda una línia per cada versió de les dades, per seguir el rendiment al llarg del temps."""
    path = ROOT / "dashboard" / "data" / "history.json"
    hist = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    y, wk = data["yearly"], data["weekly"]
    row = {"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "agent": agent,
           "co2_t_year": round(y["co2_t_year"], 1), "eur_year": round(y["eur_year"]),
           "co2_pct": y["co2_pct"], "cost_pct": y["cost_pct"],
           "of_best_pct": round(sum(w["of_best_pct"] for w in wk) / len(wk), 1),
           "worst_week_co2_pct": min(w["co2_pct"] for w in wk), "violations": y["violations"]}
    same = lambda a, b: all(a.get(k) == b[k] for k in row if k != "date")
    mine = [h for h in hist if h.get("agent") == agent]
    if not mine or not same(mine[-1], row):   # només si ha canviat alguna cosa
        hist.append(row)
        path.write_text(json.dumps(hist, ensure_ascii=False, indent=1), encoding="utf-8")
    return [h for h in hist if h.get("agent") == agent]


def build_mode(mode):
    """Totes les dades d'un mode: la simulació hora a hora, les setmanes i els resums de cada vista."""
    m = an.MODES[mode]
    d = an.run(mode=mode)
    base = an.run("sense_bateria", mode=mode)
    rules = an.run("plantilla", mode=mode)
    valid = an.valid_data(mode)
    weeks = []
    pos = 0
    for b in contiguous_blocks(valid):
        weeks.append({"start": pos, "end": pos + len(b), "label": b.index[0].strftime("%d/%m/%Y")})
        pos += len(b)

    hours = {
        "t": [t.strftime("%Y-%m-%d %H:00") for t in d.index],
        "load": d.load_kw.round(1).tolist(), "pv": d.pv_kw.round(1).tolist(),
        "price": d.precio_eur_per_kwh.round(4).tolist(), "co2": d.co2_kg_per_kwh.round(4).tolist(),
        "bat": d.bat_kw.round(1).tolist(), "soc": d.soc_pct.round(4).tolist(),
        "grid": d.grid_kw.round(1).tolist(), "base": d.base_grid_kw.round(1).tolist(),
        "rules_soc": rules.soc_pct.round(4).tolist(),
        "why": why_text(d, m["agent"]),
    }
    co2_ref, price_ref = refs(m["agent"])
    data = {
        "mode": {"key": mode, "label": m["label"], "agent": m["agent"], "cap_kwh": m["cap_kwh"], "power_kw": m["power_kw"],
                 "pv_scale": m["pv_scale"], "market_hours": m["market_hours"],
                 "co2_ref": round(co2_ref, 5), "price_ref": round(price_ref, 5)},
        "hours": hours,
        "weeks": weeks,
        "result": d.attrs["resultat"],
        "rules_result": rules.attrs["resultat"],
        "base_result": base.attrs["resultat"],
        "yearly": an.yearly(d),
        "strategies": an.strategies(mode).to_dict("records"),
        "sizing": an.sizing(mode).to_dict("records"),
        "robustness": an.robustness(mode).to_dict("records"),
        "monthly": an.monthly(d).to_dict("records"),
        "profile": an.hourly_profile(d).to_dict("records"),
    }
    oracle = an.oracle_continuous(valid, m["cap_kwh"], m["power_kw"])
    data["weekly"] = weekly(d, rules, weeks, oracle["weeks"], m["cap_kwh"])
    data["history"] = save_history(data, m["agent"])
    return data


def main():
    modes = {mode: build_mode(mode) for mode in an.MODES}
    # les dades amb que s'han fet els models (tot el train), per poder-les analitzar al dashboard;
    # es guarden un sol cop i al Mode Dificil la web multiplica la solar per 12
    tr = load_hourly()
    train = {"t": [x.strftime("%Y-%m-%d %H:00") for x in tr.index],
             "load": tr.load_kw.round(1).tolist(), "pv": tr.pv_kw.round(1).tolist(),
             "price": tr.precio_eur_per_kwh.round(4).tolist(), "co2": tr.co2_kg_per_kwh.round(4).tolist(),
             "irr": tr.irr_wm2.round(1).tolist(), "temp": tr.temp_c.round(1).tolist()}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    js = lambda x: json.dumps(x, ensure_ascii=False, separators=(",", ":"))
    OUT.write_text(f"window.DATA_MODES = {js(modes)};\nwindow.TRAIN = {js(train)};\n", encoding="utf-8")
    campus = (ROOT / "dashboard" / "static" / "campus_nord.json").read_text(encoding="utf-8")
    (OUT.parent / "campus.js").write_text("window.CAMPUS = " + campus + ";\n", encoding="utf-8")
    print("Escrit", OUT, f"({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
