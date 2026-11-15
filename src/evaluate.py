"""
Avaluacio local d'agents amb el simulador OFICIAL (starter_kit/environment.py).

Com que el test de debo son "els ultims 7 dies de cada mes" (12 setmanes seguides
una darrere l'altra), aqui fem un pseudo-test semblant amb el train:
  - VALID: els ultims 7 dies de cada bloc mensual del train, concatenats.
  - FULL : tot el train seguit.

Us (des de l'arrel del projecte):
    python -m src.evaluate agents/estandard_robust            # avalua un agent
    python -m src.evaluate starter_kit              # plantilla oficial
    python -m src.evaluate --oracle                 # cota superior (info perfecta)
"""
import argparse
import importlib.util
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linprog

from src.data import ROOT, load_hourly, contiguous_blocks

sys.path.insert(0, str(ROOT / "starter_kit"))
from environment import CampusBatteryEnv  # noqa: E402

BASE_COLS = ["load_kw", "pv_kw", "precio_eur_per_kwh", "co2_kg_per_kwh"]


def valid_split(df: pd.DataFrame, days: int = 7) -> pd.DataFrame:
    """Ultims `days` dies de cada bloc continu de mes ~ imita el test ocult."""
    parts = []
    for b in contiguous_blocks(df):
        if len(b) < 24 * (days + 3):   # trossos massa curts (forats de sensors)
            continue
        parts.append(b.iloc[-24 * days:])
    return pd.concat(parts)


def load_agent(folder: str):
    path = Path(folder) / "agent.py"
    spec = importlib.util.spec_from_file_location(f"agent_{abs(hash(str(path)))}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.BatteryAgent()


def run(agent, data: pd.DataFrame) -> dict:
    env = CampusBatteryEnv(data[BASE_COLS])
    obs, done = env.reset(), False
    t0 = time.time()
    while not done:
        obs, done = env.step(agent.act(obs))
    r = env.evaluate_results()
    r["segons"] = round(time.time() - t0, 1)
    return r


def oracle(data: pd.DataFrame) -> dict:
    """LP sobre tot el periode coneixent-ho TOT (consum inclos). Cota superior teorica."""
    from scipy.sparse import tril, hstack, vstack
    d = data[BASE_COLS].reset_index(drop=True)
    n = len(d)
    net = (d.load_kw - d.pv_kw).clip(lower=0).values
    C = (net * d.co2_kg_per_kwh).sum()
    K = (net * d.precio_eur_per_kwh).sum()
    w = n * (0.7 * d.co2_kg_per_kwh.values / C + 0.3 * d.precio_eur_per_kwh.values / K)  # reescalat (HiGHS)
    eta = 0.9 ** 0.5
    L = tril(np.ones((n, n)), format="csr")
    A = vstack([hstack([eta * L, -L / eta]), hstack([-eta * L, L / eta])])
    b = np.full(2 * n, 1000.0 - 1e-3)
    bounds = [(0, 500)] * n + [(0, min(500, x)) for x in net]
    res = linprog(np.concatenate([w, -w]), A_ub=A, b_ub=b, bounds=bounds, method="highs")
    p = res.x[:n] - res.x[n:]
    grid = np.maximum(net + p, 0)
    dco2 = 1 - (grid * d.co2_kg_per_kwh).sum() / C
    dcost = 1 - (grid * d.precio_eur_per_kwh).sum() / K
    return {"score": round(100 * (0.7 * dco2 + 0.3 * dcost), 2),
            "co2_estalviat_pct": round(100 * dco2, 2), "cost_estalviat_pct": round(100 * dcost, 2)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("agent", nargs="?", default=None)
    ap.add_argument("--oracle", action="store_true")
    a = ap.parse_args()
    df = load_hourly()
    sets = {"VALID (7d/mes)": valid_split(df), "FULL train": df}
    for name, data in sets.items():
        r = oracle(data) if a.oracle else run(load_agent(a.agent), data)
        print(f"{name:16s} ({len(data)} h): {r}")


if __name__ == "__main__":
    main()
