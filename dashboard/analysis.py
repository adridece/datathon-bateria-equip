"""
Calculs que fa servir el dashboard. Tot passa pel simulador oficial (src/replay.py),
aixi les xifres de totes les pagines quadren entre elles.
Els calculs lents es guarden a data/processed/ i nomes es fan el primer cop.
"""
import numpy as np
import pandas as pd

from src.data import PROCESSED, load_hourly
from src.evaluate import oracle, valid_split
from src.replay import make_agent, replay

HOURS_PER_YEAR = 8760
CAPACITIES = [500, 1000, 2000, 3000, 4000, 6000, 8000]
POWERS = [250, 500, 1000]


def valid_data() -> pd.DataFrame:
    return valid_split(load_hourly())


def _cached(name, build):
    path = PROCESSED / f"dash_{name}.csv"
    if path.exists():
        return pd.read_csv(path)
    df = build()
    df.to_csv(path, index=False)
    return df


def run(agent="mpc_lp", cap=2000.0, power=500.0, data=None) -> pd.DataFrame:
    data = valid_data() if data is None else data
    return replay(make_agent(agent, cap, power), data, cap, power)


def strategies() -> pd.DataFrame:
    def build():
        rows = []
        for label, agent in [("Sense bateria", "sense_bateria"), ("Regles per hores", "plantilla"),
                             ("MPC + programació lineal", "mpc_lp")]:
            r = run(agent).attrs["resultat"]
            rows.append({"strategy": label, "score": r["score"], "co2_pct": r["co2_estalviat_pct"],
                         "cost_pct": r["cost_estalviat_pct"], "violations": r["infraccions"]})
        o = oracle(valid_data())
        rows.append({"strategy": "Òptim teòric", "score": float(o["score"]),
                     "co2_pct": float(o["co2_estalviat_pct"]), "cost_pct": float(o["cost_estalviat_pct"]),
                     "violations": 0})
        return pd.DataFrame(rows)
    return _cached("strategies", build)


def sizing() -> pd.DataFrame:
    def build():
        hours = len(valid_data())
        rows = []
        for p in POWERS:
            for c in CAPACITIES:
                r = run("mpc_lp", float(c), float(p)).attrs["resultat"]
                rows.append({"capacity_kwh": c, "power_kw": p, "score": r["score"],
                             "co2_pct": r["co2_estalviat_pct"], "cost_pct": r["cost_estalviat_pct"],
                             "co2_t_year": r["co2_estalviat_kg"] / 1000 * HOURS_PER_YEAR / hours,
                             "eur_year": r["cost_estalviat_eur"] * HOURS_PER_YEAR / hours})
        return pd.DataFrame(rows)
    return _cached("sizing", build)


class NoisyForecast:
    """Dona a l'agent previsions de preu i CO2 amb error, per veure si aguanta."""

    def __init__(self, agent, error, seed=0):
        self.agent, self.error = agent, error
        self.rng = np.random.default_rng(seed)

    def act(self, obs):
        obs = dict(obs)
        for key in ("preus_properes_24h", "co2_properes_24h"):
            x = np.asarray(obs[key], dtype=float)
            # l'hora actual es coneix be; l'error creix com mes lluny mirem
            sigma = self.error * np.sqrt(np.arange(len(x)) / 23.0)
            obs[key] = list(x * (1 + sigma * self.rng.standard_normal(len(x))))
        return self.agent.act(obs)


def robustness() -> pd.DataFrame:
    def build():
        rows = []
        for e in [0.0, 0.05, 0.10, 0.20, 0.30, 0.50]:
            d = replay(NoisyForecast(make_agent("mpc_lp"), e), valid_data())
            rows.append({"error_pct": int(100 * e), "score": d.attrs["resultat"]["score"],
                         "violations": d.attrs["resultat"]["infraccions"]})
        return pd.DataFrame(rows)
    return _cached("robustness", build)


def hourly_profile(d: pd.DataFrame) -> pd.DataFrame:
    g = d.groupby(d.index.hour)
    return pd.DataFrame({"hour": range(24), "battery_kw": g.bat_kw.mean().values,
                         "co2_g": 1000 * g.co2_kg_per_kwh.mean().values,
                         "price_eur_mwh": 1000 * g.precio_eur_per_kwh.mean().values})


def monthly(d: pd.DataFrame) -> pd.DataFrame:
    g = d.groupby(d.index.to_period("M"))
    return pd.DataFrame({
        "month": [p.strftime("%b %y") for p in g.size().index],
        "order": range(len(g.size())),
        "co2_pct": (100 * (g.co2_base_kg.sum() - g.co2_kg.sum()) / g.co2_base_kg.sum()).values,
        "cost_pct": (100 * (g.cost_base_eur.sum() - g.cost_eur.sum()) / g.cost_base_eur.sum()).values,
    })


def yearly(d: pd.DataFrame) -> dict:
    r = d.attrs["resultat"]
    f = HOURS_PER_YEAR / len(d)
    return {"co2_t_year": r["co2_estalviat_kg"] / 1000 * f, "eur_year": r["cost_estalviat_eur"] * f,
            "co2_pct": r["co2_estalviat_pct"], "cost_pct": r["cost_estalviat_pct"], "score": r["score"],
            "violations": r["infraccions"], "hours": len(d)}


def energy_balance(d: pd.DataFrame) -> dict:
    """Energia total del periode (MWh) per explicar on va cada kWh."""
    charged = d.bat_kw.clip(lower=0).sum() / 1000
    discharged = -d.bat_kw.clip(upper=0).sum() / 1000
    stored_change = (d.soc_kwh.iloc[-1] - 1000) / 1000   # la bateria comenca al 50 %
    return {"charged": charged, "discharged": discharged, "losses": charged - discharged - stored_change,
            "grid_base": d.base_grid_kw.sum() / 1000,
            "grid": d.grid_kw.sum() / 1000, "solar": d.pv_kw.sum() / 1000, "load": d.load_kw.sum() / 1000}
