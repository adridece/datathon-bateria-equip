"""
Repeteix una simulacio amb el simulador oficial i en guarda TOT hora a hora
(el que fa servir el dashboard per animar-ho).

    from src.replay import replay
    df = replay("agents/mpc_lp", dades)      # DataFrame amb una fila per hora
"""
import numpy as np
import pandas as pd

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
