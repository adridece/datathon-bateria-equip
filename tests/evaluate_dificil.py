"""
Avaluacio local del Mode Dificil (solar x12, bateria 6.000 kWh / 1.500 kW, 3 h de mercat).
Des de l'arrel del projecte:
    python tests/evaluate_dificil.py                 (avalua agents/dificil_previsio_simple)
    python tests/evaluate_dificil.py agents/altre    (avalua una altra carpeta)

Fa servir el simulador oficial i nomes hi afegeix el que diu la pestanya Mode Dificil de la web:
retalla les previsions a 3 h i afegeix la meteo i la mida de la bateria a obs.
Compte: els perfils de params.json surten de tot el train, aixi que aquest score es una mica
optimista. El valor honest (perfils sense les setmanes de validacio) es a docs/DIARI.md.
"""
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data import load_hourly  # noqa: E402
from src.evaluate import BASE_COLS, CampusBatteryEnv, load_agent, valid_split  # noqa: E402

SPEC = {"capacity_kwh": 6000.0, "power_kw": 1500.0, "efficiency": 0.9, "soc_init": 0.5,
        "soc_min": 0.0, "soc_max": 1.0, "dt_hours": 1.0}
MARKET_HOURS = 3


class HardEnv(CampusBatteryEnv):
    def __init__(self, data):
        self.meteo = data[["irr_wm2", "temp_c", "panel_c", "wind_ms"]].fillna(0.0).reset_index(drop=True)
        super().__init__(data[BASE_COLS], spec=SPEC)

    def _get_obs(self):
        obs = super()._get_obs()
        if obs is None:
            return None
        obs["preus_properes_24h"] = obs["preus_properes_24h"][:MARKET_HOURS]
        obs["co2_properes_24h"] = obs["co2_properes_24h"][:MARKET_HOURS]
        k = max(self.t - 1, 0)
        obs["noves_dades_5min"]["irradiancia_wm2"] = float(self.meteo.irr_wm2.iloc[k])
        obs["noves_dades_5min"]["temp_ambient_c"] = float(self.meteo.temp_c.iloc[k])
        obs["noves_dades_5min"]["temp_panel_c"] = float(self.meteo.panel_c.iloc[k])
        obs["noves_dades_5min"]["vent_ms"] = float(self.meteo.wind_ms.iloc[k])
        obs["cap_max_kwh"], obs["power_max_kw"] = SPEC["capacity_kwh"], SPEC["power_kw"]
        return obs


def hard_data():
    data = valid_split(load_hourly()).copy()
    data["pv_kw"] = data["pv_kw"] * 12.0
    return data


def run_hard(agent, data):
    env = HardEnv(data)
    obs, done = env.reset(), False
    t0 = time.time()
    while not done:
        obs, done = env.step(agent.act(obs))
    grid = np.array(env.grid)
    base = (data.load_kw - data.pv_kw).clip(lower=0).values
    co2, price = data.co2_kg_per_kwh.values, data.precio_eur_per_kwh.values
    d_co2 = 100 * (1 - (grid * co2).sum() / (base * co2).sum())
    d_cost = 100 * (1 - (grid * price).sum() / (base * price).sum())
    return {"score": round(0.7 * d_co2 + 0.3 * d_cost, 3), "co2_pct": round(d_co2, 2), "cost_pct": round(d_cost, 2),
            "infraccions": env.clipped + env.violations, "segons": round(time.time() - t0, 1)}


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "agents/dificil_previsio_simple"
    data = hard_data()
    print(f"Mode Dificil, validacio ({len(data)} h): {run_hard(load_agent(ROOT / folder), data)}")
