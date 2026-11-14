"""
Entrena els models de previsio de agents/dificil_lightgbm (Mode Dificil) i escriu params.json.
    python scripts/train_dificil_lightgbm.py
Cal lightgbm (ja es a requirements.txt). Tarda menys d'un minut.

Cada model aprèn a corregir l'error de la previsio senzilla de l'agent (agents/dificil_lightgbm/agent.py),
amb les mateixes variables que l'agent calcula durant la simulacio.
"""
import importlib.util
import json
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data import contiguous_blocks, load_hourly  # noqa: E402

FOLDER = ROOT / "agents" / "dificil_lightgbm"
# cada model nomes s'entrena (i es fa servir) fins a aquesta hora +j: mes lluny no millora res
NEAR_HOURS = {"price": 8, "co2": 8, "load": 2, "pv": 2}
LGB_PARAMS = {"objective": "l1", "learning_rate": 0.05, "num_leaves": 15, "min_data_in_leaf": 50,
              "feature_fraction": 0.9, "bagging_fraction": 0.8, "bagging_freq": 1, "lambda_l2": 1.0,
              "verbose": -1, "seed": 0}


def load_agent_module():
    spec = importlib.util.spec_from_file_location("dificil_lightgbm_agent", FOLDER / "agent.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_profile(d):
    g = d.groupby([d.index.dayofweek, d.index.hour]).load_kw.median()
    return [[round(float(g.get((dw, h), d.load_kw.median())), 1) for h in range(24)] for dw in range(7)]


def month_profile(d, col):
    """Perfil mitja per mes: [feiner 24 h, cap de setmana 24 h]."""
    out = {}
    for month, g in d.groupby(d.index.month):
        all_days = g.groupby(g.index.hour)[col].mean()
        rows = []
        for weekend in (False, True):
            x = g[(g.index.dayofweek >= 5) == weekend]
            s = x.groupby(x.index.hour)[col].mean()
            rows.append([round(float(s.get(h, all_days.get(h, g[col].mean()))), 5) for h in range(24)])
        out[str(month)] = rows
    return out


def clear_sky(d):
    """Solar d'un dia clar: percentil 95 per mes i hora."""
    g = d.groupby([d.index.month, d.index.hour]).pv_kw.quantile(0.95)
    return {str(m): [round(float(g.get((m, h), 0.0)), 1) for h in range(24)] for m in sorted(set(d.index.month))}


def build_dataset(d, agent, profiles):
    """Per a cada hora del train, les mateixes files que veuria l'agent i l'error de la previsio senzilla."""
    X = {k: [] for k in ("price", "co2", "load", "pv")}
    y = {k: [] for k in X}
    for b in contiguous_blocks(d):
        price, co2 = b.precio_eur_per_kwh.tolist(), b.co2_kg_per_kwh.tolist()
        load, pv = b.load_kw.tolist(), b.pv_kw.tolist()
        irr, temp = b.irr_wm2.tolist(), b.temp_c.tolist()
        n = len(b)
        for t in range(n - 2):
            ts = b.index[t]
            hour, dow, month = ts.hour, ts.dayofweek, ts.month
            irr_last = irr[t - 1] if t > 0 else float("nan")
            rows = {
                "price": agent.market_rows(price[:t], co2[:t], price[t:t + 3], co2[t:t + 3], hour, dow, month,
                                           irr_last, profiles["price_profile"].get(str(month))),
                "co2": agent.market_rows(co2[:t], price[:t], co2[t:t + 3], price[t:t + 3], hour, dow, month,
                                         irr_last, profiles["co2_profile"].get(str(month))),
                "load": agent.load_rows(load[:t], temp[:t], hour, dow, month, profiles["load_profile"]),
                "pv": agent.pv_rows(pv[:t], irr[:t], temp[:t], hour, month, profiles["pv_clear"].get(str(month))),
            }
            real = {"price": price, "co2": co2, "load": load, "pv": pv}
            for name in X:
                first = 3 if name in ("price", "co2") else 0
                for j in range(first, 24):
                    if t + j < n:
                        row = rows[name][j - first]
                        X[name].append(row)
                        y[name].append(real[name][t + j] - row[-1])
    return {k: (np.array(X[k], dtype=float), np.array(y[k], dtype=float)) for k in X}


def main():
    agent = load_agent_module()
    d = load_hourly().copy()
    d["pv_kw"] = d["pv_kw"] * 12.0          # al Mode Dificil la solar es 12 vegades mes gran
    net = (d.load_kw - d.pv_kw).clip(lower=0)
    profiles = {"load_profile": load_profile(d), "price_profile": month_profile(d, "precio_eur_per_kwh"),
                "co2_profile": month_profile(d, "co2_kg_per_kwh"), "pv_clear": clear_sky(d)}
    data = build_dataset(d, agent, profiles)
    for name, limit in NEAR_HOURS.items():
        X, y = data[name]
        near = X[:, 0] <= limit
        model = lgb.train(LGB_PARAMS, lgb.Dataset(X[near], y[near]), num_boost_round=400)
        model.save_model(str(FOLDER / f"{name}.txt"))
        print(f"{name}: {near.sum()} files, error mitja de la previsio senzilla {np.abs(y[near]).mean():.4f}")
    params = {"co2_ref": round(float((net * d.co2_kg_per_kwh).sum() / net.sum()), 5),
              "price_ref": round(float((net * d.precio_eur_per_kwh).sum() / net.sum()), 5),
              "w_co2": 0.7, "w_cost": 0.3, "safety": 0.96, "near_hours": NEAR_HOURS, **profiles}
    with open(FOLDER / "params.json", "w", encoding="utf-8") as f:
        json.dump(params, f, indent=1)
    print("Escrit", FOLDER / "params.json")


if __name__ == "__main__":
    main()
