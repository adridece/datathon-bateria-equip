"""
Genera dashboard/data/data.js amb totes les dades que fa servir la web del dashboard.
Tot surt del simulador oficial, aixi les xifres quadren amb el leaderboard i entre elles.

    python scripts/build_dashboard_data.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dashboard import analysis as an  # noqa: E402
from src.data import contiguous_blocks  # noqa: E402

OUT = ROOT / "dashboard" / "data" / "data.js"


def why_text(d):
    # frase curta que explica la decisio de cada hora
    w = (0.7 * d.co2_kg_per_kwh / 0.0921 + 0.3 * d.precio_eur_per_kwh / 0.1568).values
    out = []
    for k in range(len(d)):
        ahead = w[k:k + 24]
        rank = int((ahead < w[k]).sum()) + 1
        b, soc = d.bat_kw.iloc[k], d.soc_pct.iloc[k]
        if b > 1:
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


def main():
    d = an.run()
    base = an.run("sense_bateria")
    rules = an.run("plantilla")
    weeks = []
    pos = 0
    for b in contiguous_blocks(an.valid_data()):
        weeks.append({"start": pos, "end": pos + len(b), "label": b.index[0].strftime("%d/%m/%Y")})
        pos += len(b)

    hours = {
        "t": [t.strftime("%Y-%m-%d %H:00") for t in d.index],
        "load": d.load_kw.round(1).tolist(), "pv": d.pv_kw.round(1).tolist(),
        "price": d.precio_eur_per_kwh.round(4).tolist(), "co2": d.co2_kg_per_kwh.round(4).tolist(),
        "bat": d.bat_kw.round(1).tolist(), "soc": d.soc_pct.round(4).tolist(),
        "grid": d.grid_kw.round(1).tolist(), "base": d.base_grid_kw.round(1).tolist(),
        "rules_soc": rules.soc_pct.round(4).tolist(),
        "why": why_text(d),
    }
    data = {
        "hours": hours,
        "weeks": weeks,
        "result": d.attrs["resultat"],
        "rules_result": rules.attrs["resultat"],
        "base_result": base.attrs["resultat"],
        "yearly": an.yearly(d),
        "strategies": an.strategies().to_dict("records"),
        "sizing": an.sizing().to_dict("records"),
        "robustness": an.robustness().to_dict("records"),
        "monthly": an.monthly(d).to_dict("records"),
        "profile": an.hourly_profile(d).to_dict("records"),
        "official": {"score": 6.43, "co2_pct": 5.97, "cost_pct": 7.50, "co2_kg": 4289.4, "eur": 8907.86,
                     "violations": 0},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n",
                   encoding="utf-8")
    campus = (ROOT / "dashboard" / "static" / "campus_nord.json").read_text(encoding="utf-8")
    (OUT.parent / "campus.js").write_text("window.CAMPUS = " + campus + ";\n", encoding="utf-8")
    print("Escrit", OUT, f"({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
