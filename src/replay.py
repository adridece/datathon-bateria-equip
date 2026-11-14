"""
Repeteix una simulacio amb el simulador oficial i en guarda TOT hora a hora
(el que fa servir el dashboard per animar-ho).

    from src.replay import replay
    df = replay("agents/mpc_lp", dades)      # DataFrame amb una fila per hora
"""
import numpy as np
import pandas as pd

from src.data import contiguous_blocks
from src.evaluate import BASE_COLS, CampusBatteryEnv, load_agent


class AgentZero:
    """Campus sense bateria (no fa res)."""
    def act(self, obs):
        return 0.0


def make_agent(name: str, cap: float = 2000.0, pmax: float = 500.0, w_co2: float = None):
    """Crea un agent. Per al 'que passaria si' canviem la mida de la bateria de l'MPC."""
    if name == "sense_bateria":
        return AgentZero()
    agent = load_agent("starter_kit" if name == "plantilla" else f"agents/{name}")
    g = type(agent).act.__globals__          # variables globals del fitxer agent.py
    if "CAP" in g:
        g["CAP"], g["PMAX"] = cap, pmax
    if w_co2 is not None and hasattr(agent, "w_co2"):
        agent.w_co2, agent.w_cost = w_co2, 1.0 - w_co2
    return agent


def replay(agent, data: pd.DataFrame, cap: float = 2000.0, pmax: float = 500.0) -> pd.DataFrame:
    spec = {"capacity_kwh": cap, "power_kw": pmax, "efficiency": 0.9, "soc_init": 0.5,
            "soc_min": 0.0, "soc_max": 1.0, "dt_hours": 1}
    env = CampusBatteryEnv(data[BASE_COLS], spec=spec)
    obs, done = env.reset(), False
    soc_before = []
    while not done:
        soc_before.append(env.soc)
        obs, done = env.step(agent.act(obs))

    d = data[BASE_COLS].copy()
    d["soc_kwh"] = np.array(env.soc_series)
    d["soc_pct"] = d["soc_kwh"] / cap
    # potencia real de la bateria (+ carrega / - descarrega) a partir del canvi de SOC
    delta = d["soc_kwh"].values - np.array(soc_before)
    eta = 0.9 ** 0.5
    d["bat_kw"] = np.where(delta >= 0, delta / eta, delta * eta)
    d["grid_kw"] = np.array(env.grid)
    d["base_grid_kw"] = (d.load_kw - d.pv_kw).clip(lower=0)
    d["co2_kg"] = d.grid_kw * d.co2_kg_per_kwh
    d["cost_eur"] = d.grid_kw * d.precio_eur_per_kwh
    d["co2_base_kg"] = d.base_grid_kw * d.co2_kg_per_kwh
    d["cost_base_eur"] = d.base_grid_kw * d.precio_eur_per_kwh
    d["co2_estalviat_acum"] = (d.co2_base_kg - d.co2_kg).cumsum()
    d["eur_estalviat_acum"] = (d.cost_base_eur - d.cost_eur).cumsum()
    d.attrs["resultat"] = env.evaluate_results()
    return d


def replay_weeks(new_agent, data: pd.DataFrame, cap: float = 2000.0, pmax: float = 500.0) -> pd.DataFrame:
    """Cada setmana es una simulacio a part que comenca al 50 %, com al simulador oficial.
    Les setmanes de validacio estan separades per mesos: no te sentit que la bateria passi la carrega d'una a l'altra."""
    parts = [replay(new_agent(), b, cap, pmax) for b in contiguous_blocks(data)]
    d = pd.concat(parts)
    d["co2_estalviat_acum"] = (d.co2_base_kg - d.co2_kg).cumsum()
    d["eur_estalviat_acum"] = (d.cost_base_eur - d.cost_eur).cumsum()
    # resultat de tot el conjunt amb la mateixa formula del simulador oficial
    res = [p.attrs["resultat"] for p in parts]
    s = lambda key: sum(x[key] for x in res)
    co2_base, co2_p, cost_base, cost_p, infr = (s("co2_baseline_kg"), s("co2_participant_kg"),
                                                s("cost_baseline_eur"), s("cost_participant_eur"), s("infraccions"))
    d_co2, d_cost = (co2_base - co2_p) / co2_base, (cost_base - cost_p) / cost_base
    d.attrs["resultat"] = {
        "score": round(max(0.0, (0.7 * d_co2 + 0.3 * d_cost - 0.002 * infr) * 100), 2),
        "co2_estalviat_pct": round(d_co2 * 100, 2), "cost_estalviat_pct": round(d_cost * 100, 2),
        "co2_estalviat_kg": round(co2_base - co2_p, 1), "cost_estalviat_eur": round(cost_base - cost_p, 2),
        "co2_participant_kg": round(co2_p, 1), "cost_participant_eur": round(cost_p, 2),
        "co2_baseline_kg": round(co2_base, 1), "cost_baseline_eur": round(cost_base, 2), "infraccions": infr,
    }
    return d
