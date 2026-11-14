"""
Calculs que fa servir el dashboard. Tot passa pel simulador oficial (src/replay.py),
aixi les xifres de totes les pagines quadren entre elles.
Els calculs lents es guarden a data/processed/ i nomes es fan el primer cop.
"""
import numpy as np
import pandas as pd

from src.data import PROCESSED, load_hourly
from src.evaluate import oracle, valid_split
from src.replay import make_agent, replay, replay_weeks

HOURS_PER_YEAR = 8760
MONTHS_SHORT = ["gen", "feb", "març", "abr", "maig", "juny", "jul", "ag", "set", "oct", "nov", "des"]
CAPACITIES = [500, 1000, 2000, 3000, 4000, 6000, 8000]
POWERS = [250, 500, 1000]


def valid_data() -> pd.DataFrame:
    return valid_split(load_hourly())


def _cached(name, build):
    path = PROCESSED / f"dash_{name}_v3.csv"   # v3: cada setmana comença al 50 %
    if path.exists():
        return pd.read_csv(path)
    df = build()
    df.to_csv(path, index=False)
    return df


def run(agent="mpc_robust", cap=2000.0, power=500.0, data=None) -> pd.DataFrame:
    data = valid_data() if data is None else data
    return replay_weeks(lambda: make_agent(agent, cap, power), data, cap, power)


def oracle_weeks(data: pd.DataFrame) -> dict:
    """Òptim teòric setmana a setmana (cada una comença al 50 %), amb els pesos de tot el conjunt."""
    from scipy.optimize import linprog
    from scipy.sparse import hstack, tril, vstack
    from src.data import contiguous_blocks
    net_all = (data.load_kw - data.pv_kw).clip(lower=0)
    C, K = (net_all * data.co2_kg_per_kwh).sum(), (net_all * data.precio_eur_per_kwh).sum()
    eta, co2, cost = 0.9 ** 0.5, 0.0, 0.0
    for b in contiguous_blocks(data):
        n, net = len(b), (b.load_kw - b.pv_kw).clip(lower=0).values
        w = len(data) * (0.7 * b.co2_kg_per_kwh.values / C + 0.3 * b.precio_eur_per_kwh.values / K)
        L = tril(np.ones((n, n)), format="csr")
        A = vstack([hstack([eta * L, -L / eta]), hstack([-eta * L, L / eta])])
        res = linprog(np.concatenate([w, -w]), A_ub=A, b_ub=np.full(2 * n, 1000.0 - 1e-3),
                      bounds=[(0, 500)] * n + [(0, min(500, x)) for x in net], method="highs")
        grid = np.maximum(net + res.x[:n] - res.x[n:], 0)
        co2 += (grid * b.co2_kg_per_kwh.values).sum()
        cost += (grid * b.precio_eur_per_kwh.values).sum()
    dco2, dcost = 1 - co2 / C, 1 - cost / K
    return {"score": round(100 * (0.7 * dco2 + 0.3 * dcost), 2),
            "co2_estalviat_pct": round(100 * dco2, 2), "cost_estalviat_pct": round(100 * dcost, 2)}


def strategies() -> pd.DataFrame:
    def build():
        rows = []
        for label, agent in [("Sense bateria", "sense_bateria"), ("Regles per hores", "plantilla"),
                             ("MPC + programació lineal", "mpc_robust")]:
            r = run(agent).attrs["resultat"]
            rows.append({"strategy": label, "score": r["score"], "co2_pct": r["co2_estalviat_pct"],
                         "cost_pct": r["cost_estalviat_pct"], "violations": r["infraccions"]})
        o = oracle_weeks(valid_data())
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
                r = run("mpc_robust", float(c), float(p)).attrs["resultat"]
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
            d = replay_weeks(lambda: NoisyForecast(make_agent("mpc_robust"), e), valid_data())
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
        "month": [f"{MONTHS_SHORT[p.month - 1]} {p.year % 100}" for p in g.size().index],
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
