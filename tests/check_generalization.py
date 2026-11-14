"""
Comprova que els agents generalitzen al test privat (no nomes al public).
Des de l'arrel del projecte:
    python tests/check_generalization.py

Fa 4 comprovacions amb el simulador oficial i scores SENSE arrodonir:
  1. Validacio creuada per mesos: gap (agent - oracle) a cada bloc mensual del train.
  2. Tests simulats: setmanes de 7 dies a l'atzar de cada mes, concatenades com el test oficial.
  3. Robustesa: soroll a les previsions, talls del comptador, final de simulacio, temps.
  4. Sensibilitat de params.json (co2_ref/preu_ref i w_co2).
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy.optimize import linprog

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data import contiguous_blocks, load_hourly  # noqa: E402
from src.evaluate import BASE_COLS, CampusBatteryEnv, load_agent, valid_split  # noqa: E402

AGENTS = ["mpc_robust", "mpc_test_weights"]
WEEK = 168


def exact_score(env, data):
    """Score oficial pero sense arrodonir (els de la web s'arrodoneixen a 2 decimals)."""
    grid = np.array(env.grid)
    base = (data.load_kw - data.pv_kw).clip(lower=0).values
    co2, price = data.co2_kg_per_kwh.values, data.precio_eur_per_kwh.values
    d_co2 = 1 - (grid * co2).sum() / (base * co2).sum()
    d_cost = 1 - (grid * price).sum() / (base * price).sum()
    return 100 * (0.7 * d_co2 + 0.3 * d_cost)


def simulate(agent, data):
    env = CampusBatteryEnv(data[BASE_COLS])
    obs, done = env.reset(), False
    t0 = time.time()
    while not done:
        obs, done = env.step(agent.act(obs))
    infr = env.clipped + env.violations
    return exact_score(env, data), infr, time.time() - t0


def oracle_score(data):
    """Oracle exacte: LP de tot el periode sabent-ho tot (consum inclos).
    El de src/evaluate.py arrodoneix els % i amb mesos curts es nota. Aqui el SOC
    es una variable mes (matrius esparses), aixi tambe va rapid amb 6.000 h."""
    d = data[BASE_COLS].reset_index(drop=True)
    n = len(d)
    net = (d.load_kw - d.pv_kw).clip(lower=0).values
    co2, price = d.co2_kg_per_kwh.values, d.precio_eur_per_kwh.values
    w = n * (0.7 * co2 / (net * co2).sum() + 0.3 * price / (net * price).sum())
    eta = 0.9 ** 0.5
    eye = sp.eye(n, format="csr")
    diff = eye - sp.eye(n, k=-1, format="csr")
    # soc_t - soc_{t-1} = eta*c_t - d_t/eta
    A = sp.hstack([-eta * eye, eye / eta, diff]).tocsr()
    b = np.zeros(n)
    b[0] = 1000.0
    bounds = [(0, 500)] * n + [(0, min(500, x)) for x in net] + [(0, 2000)] * n
    res = linprog(np.concatenate([w, -w, np.zeros(n)]), A_eq=A, b_eq=b, bounds=bounds, method="highs")
    p = res.x[:n] - res.x[n:2 * n]
    grid = np.maximum(net + p, 0)
    d_co2 = 1 - (grid * co2).sum() / (net * co2).sum()
    d_cost = 1 - (grid * price).sum() / (net * price).sum()
    return 100 * (0.7 * d_co2 + 0.3 * d_cost)


def agent_with_params(name, **changes):
    agent = load_agent(ROOT / "agents" / name)
    for k, v in changes.items():
        setattr(agent, k, v)
    return agent


class NoisyForecast:
    """Embolcall: afegeix error a les previsions (mes error com mes lluny)."""
    def __init__(self, agent, error, seed=0):
        self.agent, self.error = agent, error
        self.rng = np.random.default_rng(seed)

    def act(self, obs):
        obs = dict(obs)
        for key in ("preus_properes_24h", "co2_properes_24h"):
            vals = np.array(obs[key], dtype=float)
            k = np.arange(len(vals))
            noise = self.rng.normal(0, self.error * np.sqrt(k / 23), len(vals))
            noise[0] = 0  # l'hora actual es coneix
            obs[key] = list(vals * np.exp(noise))
        return self.agent.act(obs)


def random_test(blocks, rng):
    """Una setmana de 7 dies a l'atzar de cada mes, concatenades (com el test oficial)."""
    parts = []
    for b in blocks:
        start = rng.integers(0, len(b) - WEEK + 1)
        parts.append(b.iloc[start:start + WEEK])
    return pd.concat(parts)


def main():
    df = load_hourly()
    blocks = [b for b in contiguous_blocks(df) if len(b) >= WEEK + 24]
    rows = []

    # 1. validacio creuada per mesos
    print("1) Gap amb l'oracle per mes")
    table = []
    for b in blocks:
        row = {"mes": b.index[0].strftime("%Y-%m"), "hores": len(b), "oracle": oracle_score(b)}
        for name in AGENTS:
            s, infr, _ = simulate(load_agent(ROOT / "agents" / name), b)
            row[name] = s
            row[f"gap_{name}"] = s - row["oracle"]
            row[f"infr_{name}"] = infr
        table.append(row)
    t1 = pd.DataFrame(table)
    print(t1.round(4).to_string(index=False))
    rows.append(("gap maxim per mes", {n: t1[f"gap_{n}"].min() for n in AGENTS}))

    # 2. tests simulats
    print("\n2) Tests simulats (12 setmanes a l'atzar, 10 repeticions)")
    rng = np.random.default_rng(42)
    sims = []
    for rep in range(10):
        data = random_test(blocks, rng)
        row = {"rep": rep, "oracle": oracle_score(data)}
        for name in AGENTS:
            s, infr, secs = simulate(load_agent(ROOT / "agents" / name), data)
            row[name], row[f"infr_{name}"], row[f"s_{name}"] = s, infr, secs
        sims.append(row)
    t2 = pd.DataFrame(sims)
    print(t2.round(4).to_string(index=False))
    for name in AGENTS:
        gap = t2[name] - t2.oracle
        print(f"  {name}: score {t2[name].mean():.4f} ± {t2[name].std():.4f} | "
              f"gap mitja {gap.mean():.4f}, pitjor {gap.min():.4f}")
    print(f"  diferencia mitjana test_weights - robust: {(t2.mpc_test_weights - t2.mpc_robust).mean():+.4f}")

    # 3. robustesa (sobre el primer test simulat)
    print("\n3) Robustesa")
    data = random_test(blocks, np.random.default_rng(7))
    for err in (0.0, 0.1, 0.2, 0.3):
        out = []
        for name in AGENTS:
            s, infr, secs = simulate(NoisyForecast(load_agent(ROOT / "agents" / name), err), data)
            out.append(f"{name} {s:.4f} ({infr} infr, {secs:.1f} s)")
        print(f"  error previsions {int(err * 100):>2d} %: " + " | ".join(out))

    # talls del comptador: posem consum 0 durant 6 h en 5 llocs a l'atzar
    cut = data.copy()
    pos = np.random.default_rng(3).choice(len(cut) - 6, 5, replace=False)
    for p in pos:
        cut.iloc[p:p + 6, cut.columns.get_loc("load_kw")] = 0.0
    o = oracle_score(cut)
    s_lp, _, _ = simulate(load_agent(ROOT / "agents" / "mpc_lp"), cut)
    out = [f"mpc_lp {s_lp:.4f}"]
    for name in AGENTS:
        s, infr, _ = simulate(load_agent(ROOT / "agents" / name), cut)
        out.append(f"{name} {s:.4f} ({infr} infr)")
    print(f"  talls del comptador (oracle {o:.4f}): " + " | ".join(out))

    # final de simulacio i SOC als limits: ho cobreix tests/test_agent.py,
    # aqui nomes mirem que l'ultima hora buidi la bateria si val la pena
    print("  final de simulacio, NaN, SOC als limits: veure python tests/test_agent.py")

    # 4. sensibilitat de params.json (sobre la validacio oficial de 7 dies/mes)
    print("\n4) Sensibilitat de params.json")
    valid = valid_split(df)
    base = load_agent(ROOT / "agents" / "mpc_robust")
    sens = []
    for label, changes in [
        ("base", {}),
        ("co2_ref -20 %", {"co2_ref": base.co2_ref * 0.8}),
        ("co2_ref +20 %", {"co2_ref": base.co2_ref * 1.2}),
        ("preu_ref -20 %", {"price_ref": base.price_ref * 0.8}),
        ("preu_ref +20 %", {"price_ref": base.price_ref * 1.2}),
        ("w_co2 0.65", {"w_co2": 0.65, "w_cost": 0.35}),
        ("w_co2 0.75", {"w_co2": 0.75, "w_cost": 0.25}),
    ]:
        s, infr, _ = simulate(agent_with_params("mpc_robust", **changes), valid)
        sens.append({"variant": label, "score": s, "infr": infr})
    t4 = pd.DataFrame(sens)
    t4["diferencia"] = t4.score - t4.score[0]
    print(t4.round(4).to_string(index=False))

    with open(ROOT / "tests" / "generalization_results.json", "w", encoding="utf-8") as f:
        json.dump({"per_month": t1.round(5).to_dict("records"), "random_tests": t2.round(5).to_dict("records"),
                   "sensitivity": t4.round(5).to_dict("records")}, f, indent=1, ensure_ascii=False)
    print("\nResultats desats a tests/generalization_results.json")


if __name__ == "__main__":
    main()
