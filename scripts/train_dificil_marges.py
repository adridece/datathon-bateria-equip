"""
Entrena els models de previsio de agents/dificil_marges (Mode Dificil) i escriu params.json.
    python scripts/train_dificil_marges.py
Cal lightgbm (ja es a requirements.txt). Tarda menys d'un minut.

Cada model aprèn a corregir l'error de la previsio senzilla de l agent (agents/dificil_marges/agent.py),
amb les mateixes variables que l'agent calcula durant la simulacio.
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
from src.data import contiguous_blocks, load_hourly  # noqa: E402

FOLDER = ROOT / "agents" / "dificil_marges"
# cada model nomes s'entrena (i es fa servir) fins a aquesta hora +j: mes lluny no millora res
NEAR_HOURS = {"price": 23, "co2": 8, "load": 2, "pv": 2}
LGB_PARAMS = {"objective": "l1", "learning_rate": 0.05, "num_leaves": 15, "min_data_in_leaf": 50,
              "feature_fraction": 0.9, "bagging_fraction": 0.8, "bagging_freq": 1, "lambda_l2": 1.0,
              "verbose": -1, "seed": 0}


def load_agent_module():
    spec = importlib.util.spec_from_file_location("dificil_marges_agent", FOLDER / "agent.py")
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


def pv_mean(d):
    """Solar mitjana per mes i hora (per al primer dia de cada setmana, quan no hi ha historial)."""
    g = d.groupby([d.index.month, d.index.hour]).pv_kw.mean()
    return {str(m): [round(float(g.get((m, h), 0.0)), 1) for h in range(24)] for m in sorted(set(d.index.month))}


def build_dataset(d, agent, profiles):
    """Per a cada hora del train, les mateixes files que veuria l'agent i l'error de la previsio senzilla."""
    X = {k: [] for k in ("price", "co2", "load", "pv")}
    y = {k: [] for k in X}
    for b in contiguous_blocks(d):
        price, co2 = b.precio_eur_per_kwh.tolist(), b.co2_kg_per_kwh.tolist()
        load, pv = b.load_kw.tolist(), b.pv_kw.tolist()
        irr, temp, panel = b.irr_wm2.tolist(), b.temp_c.tolist(), b.panel_c.tolist()
        n = len(b)
        for t in range(n - 2):
            ts = b.index[t]
            hour, dow, month = ts.hour, ts.dayofweek, ts.month
            irr_last = irr[t - 1] if t > 0 else float("nan")
            pv_args = (pv[:t], irr[:t], temp[:t])
            if "panel" in agent.pv_rows.__code__.co_varnames:
                pv_rows = agent.pv_rows(*pv_args, panel[:t], hour, month,
                                        profiles["pv_clear"].get(str(month)),
                                        profiles["pv_mean"].get(str(month)))
            else:
                pv_rows = agent.pv_rows(*pv_args, hour, month,
                                        profiles["pv_clear"].get(str(month)),
                                        profiles["pv_mean"].get(str(month)))
            rows = {
                "price": agent.market_rows(price[:t], co2[:t], price[t:t + 3], co2[t:t + 3], hour, dow, month,
                                           irr_last, profiles["price_profile"].get(str(month))),
                "co2": agent.market_rows(co2[:t], price[:t], co2[t:t + 3], price[t:t + 3], hour, dow, month,
                                         irr_last, profiles["co2_profile"].get(str(month))),
                "load": agent.load_rows(load[:t], temp[:t], hour, dow, month, profiles["load_profile"]),
                "pv": pv_rows,
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


def net_errors(d, agent, profiles, near_hours, params_lgb, rounds):
    """Error de la previsio del consum net de l'hora actual, mesurat fora de mostra:
    entrenem amb la meitat dels mesos i mirem l'error a l'altra meitat (i al reves)."""
    blocks = contiguous_blocks(d)
    errors = {h: [] for h in range(24)}
    for part in (0, 1):
        train_d = pd.concat([b for i, b in enumerate(blocks) if i % 2 != part])
        test_d = pd.concat([b for i, b in enumerate(blocks) if i % 2 == part])
        tr, te = build_dataset(train_d, agent, profiles), build_dataset(test_d, agent, profiles)
        pred = {}
        for name in ("load", "pv"):
            X, y = tr[name]
            near = X[:, 0] <= near_hours.get(name, 0)
            model = lgb.train(params_lgb, lgb.Dataset(X[near], y[near]), num_boost_round=rounds)
            Xt, yt = te[name]
            now = Xt[:, 0] == 0
            pred[name] = (Xt[now, -1] + model.predict(Xt[now]), Xt[now, -1] + yt[now])
            hours = Xt[now, 1]
        err = (pred["load"][1] - pred["pv"][1]) - (pred["load"][0] - np.maximum(pred["pv"][0], 0.0))
        for h, e in zip(hours, err):
            errors[int(h)].append(e)
    # quantils 5 %, 10 %, ..., 50 % de l'error (real - previst) a cada hora
    levels = np.arange(1, 11) * 0.05
    return {str(h): [round(float(q), 1) for q in np.quantile(v, levels)] for h, v in errors.items()}


def last_days(d, hours=72):
    """Ultimes hores de cada tros continu del train. El test (ultima setmana del mes) sol comencar
    just l'hora seguent, aixi l'agent ja te 'ahir' el primer dia de cada setmana."""
    out = {}
    for b in contiguous_blocks(d):
        tail = b.iloc[-hours:]
        end = tail.index[-1].strftime("%Y-%m-%d %H")
        out[end] = {"price": [round(float(x), 5) for x in tail.precio_eur_per_kwh],
                    "co2": [round(float(x), 5) for x in tail.co2_kg_per_kwh],
                    "load": [round(float(x), 1) for x in tail.load_kw],
                    "pv": [round(float(x), 1) for x in tail.pv_kw],
                    "irr": [round(float(x), 1) if x == x else None for x in tail.irr_wm2],
                    "temp": [round(float(x), 2) if x == x else None for x in tail.temp_c],
                    "panel": [round(float(x), 2) if x == x else None for x in tail.panel_c]}
    return out


def train(d, folder, near_hours=None, lgb_params=None, rounds=400, safety=0.94, seeds=3, by_model=None, **extra):
    folder = Path(folder)
    agent = load_agent_module()
    near_hours = near_hours or NEAR_HOURS
    net = (d.load_kw - d.pv_kw).clip(lower=0)
    profiles = {"load_profile": load_profile(d), "price_profile": month_profile(d, "precio_eur_per_kwh"),
                "co2_profile": month_profile(d, "co2_kg_per_kwh"), "pv_clear": clear_sky(d), "pv_mean": pv_mean(d)}
    data = build_dataset(d, agent, profiles)
    params_lgb = {**LGB_PARAMS, **(lgb_params or {})}
    for name, limit in near_hours.items():
        X, y = data[name]
        near = X[:, 0] <= limit
        if near.sum() == 0:
            continue
        p_model = {**params_lgb, **(by_model or {}).get(name, {})}
        # uns quants models iguals amb llavors diferents: la mitjana es mes estable
        for k in range(seeds):
            model = lgb.train({**p_model, "seed": k}, lgb.Dataset(X[near], y[near]), num_boost_round=rounds)
            model.save_model(str(folder / f"{name}_{k}.txt"))
    errs = net_errors(d, agent, profiles, near_hours, params_lgb, rounds)
    params = {"history": last_days(d), "net_errors": errs, "co2_ref": round(float((net * d.co2_kg_per_kwh).sum() / net.sum()), 5),
              "price_ref": round(float((net * d.precio_eur_per_kwh).sum() / net.sum()), 5),
              "w_co2": 0.7, "w_cost": 0.3, "safety": safety, "safety_night": 0.98, "quantile": 3, "near_hours": near_hours, "seeds": seeds, **profiles, **extra}
    with open(folder / "params.json", "w", encoding="utf-8") as f:
        json.dump(params, f, indent=1)


def main():
    d = load_hourly().copy()
    d["pv_kw"] = d["pv_kw"] * 12.0          # al Mode Dificil la solar es 12 vegades mes gran
    # final: tot el train, 5 llavors i models de mercat una mica mes grans (veure docs/DIARI.md)
    market = {"num_leaves": 31, "min_data_in_leaf": 30}
    train(d, FOLDER, seeds=5, by_model={"price": market, "co2": market})
    print("Escrit", FOLDER)


if __name__ == "__main__":
    main()
