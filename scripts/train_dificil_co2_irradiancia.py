"""
Entrena agents/dificil_co2_irradiancia (Mode Dificil): els models de dificil_marges i, a mes, el model directe de CO2 (+3..+12 h).
    python scripts/train_dificil_co2_irradiancia.py
"""
import importlib.util
import json
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from src.data import contiguous_blocks, load_hourly  # noqa: E402
import train_dificil_marges as base  # noqa: E402

FOLDER = ROOT / "agents" / "dificil_co2_irradiancia"
DIRECT = {"first": 3, "last": 12, "weight": 0.5, "seeds": 3}
PRICE_DIRECT = {"first": 3, "last": 12, "weight": 0.5, "seeds": 3}
# PVPC public de REE (gener 2024 - agost 2025), abans del periode del repte: mateixa font que precio_pvpc.csv
EXTERNAL_PRICE = ROOT / "data" / "external" / "pvpc_2024_2025.csv"
PARAMS = {"objective": "l1", "learning_rate": 0.05, "num_leaves": 31, "min_data_in_leaf": 50, "feature_fraction": 0.8,
          "bagging_fraction": 0.8, "bagging_freq": 1, "verbose": -1}


def load_agent_module(folder):
    spec = importlib.util.spec_from_file_location("dificil_co2_irradiancia_agent", Path(folder) / "agent.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def direct_dataset(d, agent):
    """Les mateixes variables que l'agent calcula a cada hora i el CO2 real a +j, relatiu a l'ultima hora coneguda."""
    hours = list(range(DIRECT["first"], DIRECT["last"] + 1))
    X, y = [], []
    for b in contiguous_blocks(d):
        c, p = b.co2_kg_per_kwh.tolist(), b.precio_eur_per_kwh.tolist()
        irr = b.irr_wm2.fillna(0.0).tolist()
        for t in range(48, len(b) - hours[-1] - 1):
            ts = b.index[t]
            rows = agent.co2_direct_rows(c[t - 48:t], p[t - 24:t], c[t:t + 3], p[t:t + 3], ts.hour, ts.dayofweek,
                                         ts.month, irr[t - 1], irr[t - 25], hours)
            for row, j in zip(rows, hours):
                X.append(row)
                y.append(c[t + j] / c[t + 2])
    return np.array(X, dtype=float), np.array(y, dtype=float)


def pv_per_irr(d):
    """kW de solar per cada W/m2 d'irradiancia a la mateixa hora (minims quadrats, nomes hores de dia)."""
    day = d[(d.irr_wm2 > 20) & d.pv_kw.notna()]
    return round(float((day.pv_kw * day.irr_wm2).sum() / (day.irr_wm2 ** 2).sum()), 4)


def price_series(d):
    """Trams continus de preu: els del train i, si hi es, el PVPC public d'abans del repte."""
    series = [b.precio_eur_per_kwh for b in contiguous_blocks(d)]
    if EXTERNAL_PRICE.exists():
        ext = pd.read_csv(EXTERNAL_PRICE, parse_dates=["Fecha"]).set_index("Fecha").precio_eur_per_kwh
        ext = ext[ext.index < d.index.min()]          # mai res del periode del repte
        cut = ext.index.to_series().diff() > pd.Timedelta("2h")
        series += [g for _, g in ext.groupby(cut.cumsum()) if len(g) > 72]
    return series


def price_dataset(d, agent):
    hours = list(range(PRICE_DIRECT["first"], PRICE_DIRECT["last"] + 1))
    X, y = [], []
    for s in price_series(d):
        p, idx = s.tolist(), s.index
        for t in range(48, len(p) - hours[-1] - 1):
            if p[t + 2] <= 0:
                continue
            ts = idx[t]
            for row, j in zip(agent.price_direct_rows(p[t - 48:t], p[t:t + 3], ts.hour, ts.dayofweek, ts.month, hours), hours):
                X.append(row)
                y.append(p[t + j] / p[t + 2])
    return np.array(X, dtype=float), np.array(y, dtype=float)


def train(d, folder, seeds_base=5, **kw):
    """Primer els models de dificil_marges i despres el model directe de CO2 a la mateixa carpeta."""
    folder = Path(folder)
    base.FOLDER = folder
    base.load_agent_module = lambda: load_agent_module(folder)
    market = {"num_leaves": 31, "min_data_in_leaf": 30}
    base.train(d, folder, seeds=seeds_base, by_model={"price": market, "co2": market}, co2_direct=DIRECT,
               price_direct=PRICE_DIRECT, pv_per_irr=pv_per_irr(d), margin_irr_now=0.7, **kw)
    X, y = direct_dataset(d, load_agent_module(folder))
    for k in range(DIRECT["seeds"]):
        model = lgb.train({**PARAMS, "seed": k}, lgb.Dataset(X, y), num_boost_round=500)
        model.save_model(str(folder / f"co2d_{k}.txt"))
    X, y = price_dataset(d, load_agent_module(folder))
    for k in range(PRICE_DIRECT["seeds"]):
        model = lgb.train({**PARAMS, "seed": k}, lgb.Dataset(X, y), num_boost_round=500)
        model.save_model(str(folder / f"priced_{k}.txt"))


def main():
    d = load_hourly().copy()
    d["pv_kw"] = d["pv_kw"] * 12.0
    train(d, FOLDER)
    print("Escrit", FOLDER)


if __name__ == "__main__":
    main()
