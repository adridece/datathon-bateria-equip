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
MONTHS_SHORT = ["gen", "feb", "març", "abr", "maig", "juny", "jul", "ag", "set", "oct", "nov", "des"]

# els dos modes del repte: el Difícil té una bateria 3 vegades més gran, 12 vegades més solar i només 3 h de mercat
MODES = {
    "estandard": {"label": "Mode estàndard", "agent": "estandard_robust", "cap_kwh": 2000.0, "power_kw": 500.0,
                  "pv_scale": 1.0, "market_hours": 24,
                  "capacities": [500, 1000, 2000, 3000, 4000, 6000, 8000], "powers": [250, 500, 1000]},
    "dificil": {"label": "Mode difícil", "agent": "dificil_marges", "cap_kwh": 6000.0, "power_kw": 1500.0,
                "pv_scale": 12.0, "market_hours": 3,
                "capacities": [2000, 4000, 6000, 8000, 12000], "powers": [750, 1500, 3000]},
}


def valid_data(mode="estandard") -> pd.DataFrame:
    d = valid_split(load_hourly()).copy()
    d["pv_kw"] = d["pv_kw"] * MODES[mode]["pv_scale"]
    return d


def _cached(name, build, mode="estandard"):
    path = PROCESSED / f"dash_{name}_{mode}_v5.csv"   # v5: un fitxer per mode
    if path.exists():
        return pd.read_csv(path)
    df = build()
    df.to_csv(path, index=False)
    return df


def run(agent=None, cap=None, power=None, data=None, mode="estandard") -> pd.DataFrame:
    m = MODES[mode]
    agent = agent or m["agent"]
    cap, power = cap or m["cap_kwh"], power or m["power_kw"]
    data = valid_data(mode) if data is None else data
    return replay(make_agent(agent, cap, power), data, cap, power, m["market_hours"])


def oracle_continuous(data: pd.DataFrame, cap=2000.0, power=500.0) -> dict:
    """Òptim teòric de tot el conjunt seguit, com el simulador oficial (la bateria comença al 50 % un sol cop i no es
    reinicia), i què estalvia a cada setmana. La xarxa és dins del problema: l'excedent solar es pot guardar gratis."""
    from scipy.optimize import linprog
    from scipy.sparse import eye, hstack, tril, vstack
    from src.data import contiguous_blocks
    raw = (data.load_kw - data.pv_kw).values
    net = np.clip(raw, 0, None)
    co2, price = data.co2_kg_per_kwh.values, data.precio_eur_per_kwh.values
    C, K = (net * co2).sum(), (net * price).sum()
    n, eta = len(net), 0.9 ** 0.5
    w = n * (0.7 * co2 / C + 0.3 * price / K)
    L = tril(np.ones((n, n)), format="csr")
    soc = hstack([eta * L, -L / eta, eye(n) * 0])
    A = vstack([soc, -soc, hstack([eye(n), -eye(n), -eye(n)])])   # xarxa >= consum net + carrega - descarrega
    b = np.concatenate([np.full(n, cap / 2 - 1e-3), np.full(n, cap / 2 - 1e-3), -raw])
    res = linprog(np.concatenate([np.zeros(2 * n), w]), A_ub=A.tocsr(), b_ub=b,
                  bounds=[(0, power)] * (2 * n) + [(0, None)] * n, method="highs")
    grid = res.x[2 * n:]
    weeks, pos = [], 0
    for blk in contiguous_blocks(data):
        sl = slice(pos, pos + len(blk))
        weeks.append({"co2_saved_kg": float(((net - grid) * co2)[sl].sum()), "eur_saved": float(((net - grid) * price)[sl].sum())})
        pos += len(blk)
    dco2, dcost = 1 - (grid * co2).sum() / C, 1 - (grid * price).sum() / K
    return {"score": round(100 * (0.7 * dco2 + 0.3 * dcost), 2),
            "co2_estalviat_pct": round(100 * dco2, 2), "cost_estalviat_pct": round(100 * dcost, 2), "weeks": weeks}


def strategies(mode="estandard") -> pd.DataFrame:
    m = MODES[mode]

    def build():
        rows = []
        for label, agent in [("Sense bateria", "sense_bateria"), ("Regles per hores", "plantilla"),
                             ("MPC + programació lineal", m["agent"])]:
            r = run(agent, mode=mode).attrs["resultat"]
            rows.append({"strategy": label, "score": r["score"], "co2_pct": r["co2_estalviat_pct"],
                         "cost_pct": r["cost_estalviat_pct"], "violations": r["infraccions"]})
        o = oracle_continuous(valid_data(mode), m["cap_kwh"], m["power_kw"])
        rows.append({"strategy": "Òptim teòric", "score": float(o["score"]),
                     "co2_pct": float(o["co2_estalviat_pct"]), "cost_pct": float(o["cost_estalviat_pct"]),
                     "violations": 0})
        return pd.DataFrame(rows)
    return _cached("strategies", build, mode)


def sizing(mode="estandard") -> pd.DataFrame:
    m = MODES[mode]

    def build():
        hours = len(valid_data(mode))
        rows = []
        for p in m["powers"]:
            for c in m["capacities"]:
                r = run(None, float(c), float(p), mode=mode).attrs["resultat"]
                rows.append({"capacity_kwh": c, "power_kw": p, "score": r["score"],
                             "co2_pct": r["co2_estalviat_pct"], "cost_pct": r["cost_estalviat_pct"],
                             "co2_t_year": r["co2_estalviat_kg"] / 1000 * HOURS_PER_YEAR / hours,
                             "eur_year": r["cost_estalviat_eur"] * HOURS_PER_YEAR / hours})
        return pd.DataFrame(rows)
    return _cached("sizing", build, mode)


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


def robustness(mode="estandard") -> pd.DataFrame:
    m = MODES[mode]

    def build():
        rows = []
        for e in [0.0, 0.05, 0.10, 0.20, 0.30, 0.50]:
            agent = NoisyForecast(make_agent(m["agent"], m["cap_kwh"], m["power_kw"]), e)
            d = replay(agent, valid_data(mode), m["cap_kwh"], m["power_kw"], m["market_hours"])
            rows.append({"error_pct": int(100 * e), "score": d.attrs["resultat"]["score"],
                         "violations": d.attrs["resultat"]["infraccions"]})
        return pd.DataFrame(rows)
    return _cached("robustness", build, mode)


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


def energy_balance(d: pd.DataFrame, cap=2000.0) -> dict:
    """Energia total del periode (MWh) per explicar on va cada kWh."""
    charged = d.bat_kw.clip(lower=0).sum() / 1000
    discharged = -d.bat_kw.clip(upper=0).sum() / 1000
    stored_change = (d.soc_kwh.iloc[-1] - cap / 2) / 1000   # la bateria comenca al 50 %
    return {"charged": charged, "discharged": discharged, "losses": charged - discharged - stored_change,
            "grid_base": d.base_grid_kw.sum() / 1000,
            "grid": d.grid_kw.sum() / 1000, "solar": d.pv_kw.sum() / 1000, "load": d.load_kw.sum() / 1000}
