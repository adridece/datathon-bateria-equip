"""
Repeteix una simulacio amb el simulador oficial i en guarda TOT hora a hora
(el que fa servir el dashboard per animar-ho).

    from src.replay import replay
    df = replay("agents/estandard_robust", dades)      # DataFrame amb una fila per hora
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


class HardEnv(CampusBatteryEnv):
    """Com la web al Mode Dificil (igual que tests/evaluate_dificil.py): nomes unes hores de mercat,
    la meteo de l'ultima hora i la mida de la bateria dins d'obs."""

    def __init__(self, data, spec, market_hours=3):
        self.market_hours = market_hours
        cols = ["irr_wm2", "temp_c", "panel_c", "wind_ms"]
        self.meteo = data.reindex(columns=cols).fillna(0.0).reset_index(drop=True)
        super().__init__(data[BASE_COLS], spec=spec)

    def _get_obs(self):
        obs = super()._get_obs()
        if obs is None:
            return None
        obs["preus_properes_24h"] = obs["preus_properes_24h"][:self.market_hours]
        obs["co2_properes_24h"] = obs["co2_properes_24h"][:self.market_hours]
        m = self.meteo.iloc[max(self.t - 1, 0)]
        obs["noves_dades_5min"].update({"irradiancia_wm2": float(m.irr_wm2), "temp_ambient_c": float(m.temp_c),
                                        "temp_panel_c": float(m.panel_c), "vent_ms": float(m.wind_ms)})
        obs["cap_max_kwh"], obs["power_max_kw"] = self.cap, self.power
        return obs


def replay(agent, data: pd.DataFrame, cap: float = 2000.0, pmax: float = 500.0, market_hours: int = 24) -> pd.DataFrame:
    spec = {"capacity_kwh": cap, "power_kw": pmax, "efficiency": 0.9, "soc_init": 0.5,
            "soc_min": 0.0, "soc_max": 1.0, "dt_hours": 1}
    if market_hours < 24:
        env = HardEnv(data, spec, market_hours)
    else:
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

