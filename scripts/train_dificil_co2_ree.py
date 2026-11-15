"""
Entrena el model directe de CO2 de agents/dificil_co2_ree (hores +3..+12).

La resta de models de l'agent son els de dificil_marges (no es reentrenen aqui).
Dades: el train del repte i l'historic public de REE de gener 2023 a agost 2025
(data/external/ree_generacio_2023_2025.csv, abans que comenci el repte; mai dies de test).

Del REE fem servir les emissions de la generacio (generacio x factor d'emissio de cada tecnologia)
dividides per la generacio total. Ajustat amb dies del train: co2 = 1,114 x emissions/generacio - 0,0055
(correlacio 0,988, error mitja 5 g/kWh).

    python scripts/train_dificil_co2_ree.py
"""
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data import contiguous_blocks, load_hourly  # noqa: E402

FOLDER = ROOT / "agents" / "dificil_co2_ree"
LAGS, STEPS = 48, range(3, 13)
SCALE, OFFSET = 1.114, -0.0055
OWN_WEIGHT = 3.0   # les nostres dades pesen mes que les de REE


def rows_at(values, n, hour, dow, month):
    # mateixes variables que direct_rows de l'agent
    last = values[n + 2]
    past = [values[n + 2 - k] - last if n + 2 - k >= 0 else np.nan for k in range(1, LAGS)]
    return [[j, (hour + j) % 24, (dow + (hour + j) // 24) % 7, int((dow + (hour + j) // 24) % 7 >= 5), month, last] + past
            for j in STEPS]


def build(values, times):
    X, y = [], []
    for n in range(LAGS, len(values) - 13):
        t = times[n]
        for j, r in zip(STEPS, rows_at(values, n, t.hour, t.dayofweek, t.month)):
            target = values[n + j] - values[n + 2]
            if target == target and r[5] == r[5]:
                X.append(r)
                y.append(target)
    return np.array(X, dtype=float), np.array(y, dtype=float)


def ree_series():
    r = pd.read_csv(ROOT / "data" / "external" / "ree_generacio_2023_2025.csv", parse_dates=["Fecha"]).set_index("Fecha")
    r = r[r.index < "2025-09-01"]
    hours = pd.date_range(r.index.min(), r.index.max(), freq="h")
    co2 = (SCALE * r.emis / r.gen + OFFSET).reindex(hours)
    return co2.values.astype(float), hours


def train(d, out, seed=0):
    parts = [build(b.co2_kg_per_kwh.values.astype(float), pd.to_datetime(b.index)) for b in contiguous_blocks(d)]
    Xo, yo = np.vstack([p[0] for p in parts]), np.concatenate([p[1] for p in parts])
    Xr, yr = build(*ree_series())
    X, y = np.vstack([Xo, Xr]), np.concatenate([yo, yr])
    w = np.concatenate([np.full(len(yo), OWN_WEIGHT), np.ones(len(yr))])
    params = {"objective": "l1", "learning_rate": 0.05, "num_leaves": 63, "min_data_in_leaf": 50, "feature_fraction": 0.8,
              "bagging_fraction": 0.8, "bagging_freq": 1, "seed": seed, "verbose": -1}
    lgb.train(params, lgb.Dataset(X, y, weight=w), 800).save_model(str(out))


if __name__ == "__main__":
    train(load_hourly(), FOLDER / "co2_direct.txt")
    print("Model directe de CO2 desat a", FOLDER / "co2_direct.txt")
