"""
Calculs per a la pestanya de decisions del dashboard.
Tot surt del simulador oficial (via src/replay.py), aixi les xifres son coherents entre elles.
Els resultats lents es guarden a data/processed/ per no recalcular-los cada cop.
"""
import numpy as np
import pandas as pd

from src.data import PROCESSED, load_hourly
from src.evaluate import oracle, valid_split
from src.replay import make_agent, replay

HORES_ANY = 8760


def dades_valid() -> pd.DataFrame:
    return valid_split(load_hourly())


def _cache(nom: str, fn):
    f = PROCESSED / f"dash_{nom}.csv"
    if f.exists():
        return pd.read_csv(f)
    df = fn()
    df.to_csv(f, index=False)
    return df


# ---------------------------------------------------------------- Q1 estrategia
def comparativa_estrategies() -> pd.DataFrame:
    def fn():
        v = dades_valid()
        files = []
        for nom, ag in [("Sense bateria", "sense_bateria"), ("Regles per hores (plantilla)", "plantilla"),
                        ("MPC + programació lineal (nostre)", "mpc_lp")]:
            r = replay(make_agent(ag), v).attrs["resultat"]
            files.append({"estrategia": nom, "score": r["score"], "co2_pct": r["co2_estalviat_pct"],
                          "cost_pct": r["cost_estalviat_pct"], "infraccions": r["infraccions"]})
        o = oracle(v)
        files.append({"estrategia": "Òptim teòric (sap el futur)", "score": float(o["score"]),
                      "co2_pct": float(o["co2_estalviat_pct"]), "cost_pct": float(o["cost_estalviat_pct"]),
                      "infraccions": 0})
        return pd.DataFrame(files)
    return _cache("estrategies", fn)


# ---------------------------------------------------------------- Q2 quan carregar
def perfil_horari() -> pd.DataFrame:
    d = replay(make_agent("mpc_lp"), dades_valid())
    g = d.groupby(d.index.hour)
    return pd.DataFrame({"hora": range(24),
                         "bateria_kw": g.bat_kw.mean().values,
                         "co2_g": 1000 * g.co2_kg_per_kwh.mean().values,
                         "preu_eur_mwh": 1000 * g.precio_eur_per_kwh.mean().values})


def perfil_mensual() -> pd.DataFrame:
    d = replay(make_agent("mpc_lp"), dades_valid())
    g = d.groupby(d.index.to_period("M"))
    out = pd.DataFrame({
        "mes": [str(p) for p in g.size().index],
        "co2_pct": (100 * (g.co2_base_kg.sum() - g.co2_kg.sum()) / g.co2_base_kg.sum()).values,
        "cost_pct": (100 * (g.cost_base_eur.sum() - g.cost_eur.sum()) / g.cost_base_eur.sum()).values,
    })
    return out


# ---------------------------------------------------------------- Q3 mida bateria
CAPS = [500, 1000, 2000, 3000, 4000, 6000, 8000]
POTS = [250, 500, 1000]


def sensibilitat() -> pd.DataFrame:
    def fn():
        v = dades_valid()
        h = len(v)
        files = []
        for p in POTS:
            for c in CAPS:
                r = replay(make_agent("mpc_lp", float(c), float(p)), v, float(c), float(p)).attrs["resultat"]
                files.append({"capacitat_kwh": c, "potencia_kw": p, "score": r["score"],
                              "co2_pct": r["co2_estalviat_pct"], "cost_pct": r["cost_estalviat_pct"],
                              "t_co2_any": r["co2_estalviat_kg"] / 1000 * HORES_ANY / h,
                              "eur_any": r["cost_estalviat_eur"] * HORES_ANY / h})
        return pd.DataFrame(files)
    return _cache("sensibilitat", fn)


# ---------------------------------------------------------------- Q5 robustesa
class AgentAmbSoroll:
    """Embolcalla l'agent i li dona previsions de preu/CO2 amb error (per provar la robustesa)."""
    def __init__(self, agent, error, seed=0):
        self.agent, self.error = agent, error
        self.rng = np.random.default_rng(seed)

    def act(self, obs):
        o = dict(obs)
        for k in ("preus_properes_24h", "co2_properes_24h"):
            x = np.asarray(o[k], dtype=float)
            # l'hora actual es coneix be; l'error creix amb l'horitzo
            factor = self.error * np.sqrt(np.arange(len(x)) / 23.0)
            o[k] = list(x * (1 + factor * self.rng.standard_normal(len(x))))
        return self.agent.act(o)


def robustesa() -> pd.DataFrame:
    def fn():
        v = dades_valid()
        files = []
        for e in [0.0, 0.05, 0.10, 0.20, 0.30, 0.50]:
            r = replay(AgentAmbSoroll(make_agent("mpc_lp"), e), v).attrs["resultat"]
            files.append({"error_pct": int(100 * e), "score": r["score"], "infraccions": r["infraccions"]})
        return pd.DataFrame(files)
    return _cache("robustesa", fn)


def anualitzat() -> dict:
    v = dades_valid()
    r = replay(make_agent("mpc_lp"), v).attrs["resultat"]
    f = HORES_ANY / len(v)
    return {"t_co2_any": r["co2_estalviat_kg"] / 1000 * f, "eur_any": r["cost_estalviat_eur"] * f,
            "co2_pct": r["co2_estalviat_pct"], "cost_pct": r["cost_estalviat_pct"], "score": r["score"]}
