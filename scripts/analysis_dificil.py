"""
Analisi de dades del Mode Dificil: genera les figures de docs/figures/dificil_*.png que expliquen el disseny de l'agent.
    python scripts/analysis_dificil.py
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data import load_hourly  # noqa: E402

OUT = ROOT / "docs" / "figures"
ACCENT, GREY, CHARGE, DISCHARGE, CO2 = "#47908B", "#A19C93", "#0072B2", "#D55E00", "#A9824F"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 130})


def net_by_hour(d):
    """Consum net (consum - solar x12) per hora del dia: al migdia hi ha excedent i la descarrega queda limitada."""
    net = d.load_kw - d.pv_kw
    g = net.groupby(d.index.hour)
    q10, q50, q90 = g.quantile(0.1), g.median(), g.quantile(0.9)
    fig, ax = plt.subplots(figsize=(7, 3.6))
    ax.fill_between(q50.index, q10, q90, color=ACCENT, alpha=0.18, label="10-90 % dels dies")
    ax.plot(q50.index, q50, color=ACCENT, lw=2, label="mediana")
    ax.axhline(0, color="#1F2326", lw=0.8)
    ax.axhline(1500, color=DISCHARGE, ls="--", lw=1, label="potència màxima de la bateria")
    ax.set_xlabel("hora del dia"); ax.set_ylabel("kW")
    ax.set_title("Consum net del campus amb 12 vegades més solar")
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    fig.tight_layout(); fig.savefig(OUT / "dificil_01_consum_net.png"); plt.close(fig)
    return float((net < 0).mean() * 100), float(-net.min())


def solar_vs_irradiance(d):
    """La solar d'una hora s'explica gairebe del tot amb la irradiancia de la mateixa hora, no amb la de l'anterior."""
    day = d[d.irr_wm2 > 20].dropna(subset=["irr_wm2"])
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.4), sharey=True)
    out = {}
    for ax, lag, title in [(axes[0], 0, "irradiància de la mateixa hora"), (axes[1], 1, "irradiància de l'hora anterior")]:
        irr = d.irr_wm2.shift(lag).reindex(day.index)
        ok = irr.notna()
        x, y = irr[ok].values, day.pv_kw[ok].values
        k = (x * y).sum() / (x * x).sum()
        r, mae = np.corrcoef(x, y)[0, 1], np.abs(y - k * x).mean()
        out[lag] = (r, mae, k)
        ax.scatter(x, y, s=3, alpha=0.25, color=ACCENT if lag == 0 else GREY)
        ax.plot([0, x.max()], [0, k * x.max()], color="#1F2326", lw=1)
        ax.set_title(f"{title}\ncorrelació {r:.3f}, error mitjà {mae:.0f} kW", fontsize=9)
        ax.set_xlabel("W/m²")
    axes[0].set_ylabel("solar de l'hora (kW)")
    fig.tight_layout(); fig.savefig(OUT / "dificil_02_solar_irradiancia.png"); plt.close(fig)
    return out


def co2_by_hour(d):
    """CO2 de la xarxa per hora i estacio: la forma del dia es repeteix, el nivell canvia molt d'un dia a l'altre."""
    fig, ax = plt.subplots(figsize=(7, 3.6))
    for months, label, color in [((12, 1, 2), "hivern", CHARGE), ((6, 7, 8), "estiu", DISCHARGE), ((3, 4, 5, 9, 10, 11), "primavera i tardor", GREY)]:
        s = d[d.index.month.isin(months)]
        g = (s.co2_kg_per_kwh * 1000).groupby(s.index.hour)
        ax.fill_between(range(24), g.quantile(0.25), g.quantile(0.75), color=color, alpha=0.12)
        ax.plot(range(24), g.median(), color=color, lw=2, label=label)
    ax.set_xlabel("hora del dia"); ax.set_ylabel("g CO₂/kWh")
    ax.set_title("CO₂ de la xarxa: mediana i 50 % central dels dies")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(OUT / "dificil_03_co2_hores.png"); plt.close(fig)
    day = (d.co2_kg_per_kwh * 1000).groupby(d.index.date)
    return float((day.max() - day.min()).median())


def where_points_go():
    """Escala de puntuacio a F0 (tests/bench_dificil.py i l'experiment de previsions perfectes de docs/ANALISI_MODE_DIFICIL.md)."""
    steps = [("dificil_marges", 18.80), ("dificil_co2_irradiancia", 18.88), ("+ irradiància\nde l'hora actual*", 19.02),
             ("previsió de\nmercat perfecta", 19.54), ("totes les previsions\nperfectes", 20.18), ("òptim teòric", 20.28)]
    # punts i no barres: l'eix no comenca a zero i una barra exageraria les diferencies
    fig, ax = plt.subplots(figsize=(8, 3.4))
    colors = [GREY, ACCENT, ACCENT, GREY, GREY, "#1F2326"]
    ax.plot(range(len(steps)), [s[1] for s in steps], color="#E6E2DA", lw=1, zorder=1)
    ax.scatter(range(len(steps)), [s[1] for s in steps], color=colors, s=70, zorder=2)
    for i, (_, v) in enumerate(steps):
        ax.text(i, v + 0.08, f"{v:.2f}", ha="center", fontsize=9)
    ax.set_xticks(range(len(steps)), [s[0] for s in steps], fontsize=8)
    ax.set_ylim(18.5, 20.6); ax.set_ylabel("puntuació (validació F0)")
    ax.set_title("On són els punts: el mètode ja és bo, el que falta és previsió")
    fig.tight_layout(); fig.savefig(OUT / "dificil_04_on_son_els_punts.png"); plt.close(fig)


def main():
    d = load_hourly().copy()
    d["pv_kw"] = d["pv_kw"] * 12.0
    surplus_pct, max_surplus = net_by_hour(d)
    irr = solar_vs_irradiance(d)
    spread = co2_by_hour(d)
    where_points_go()
    print(f"Hores amb excedent solar: {surplus_pct:.1f} % (fins a {max_surplus:.0f} kW)")
    print(f"Solar vs irradiància mateixa hora: r={irr[0][0]:.3f}, error {irr[0][1]:.0f} kW, {irr[0][2]:.3f} kW per W/m²")
    print(f"Solar vs irradiància hora anterior: r={irr[1][0]:.3f}, error {irr[1][1]:.0f} kW")
    print(f"Diferència mediana entre l'hora més bruta i la més neta del dia: {spread:.0f} g/kWh")
    print("Figures a", OUT)


if __name__ == "__main__":
    main()
