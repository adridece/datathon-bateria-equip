"""
Proves de l'agent robust. Des de l'arrel del projecte:
    python tests/test_agent.py          (no cal instal·lar res mes)
    python -m pytest tests              (si teniu pytest)
"""
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.evaluate import load_agent, run, valid_split  # noqa: E402
from src.data import load_hourly  # noqa: E402

AGENT_DIR = ROOT / "agents" / "mpc_robust"
ETA = 0.9 ** 0.5


def base_obs(**changes):
    obs = {
        "timestamp": pd.Timestamp("2026-01-25 10:00"), "hour": 10, "day_of_week": 6,
        "soc_kwh": 1000.0, "soc_pct": 0.5, "soc_percent": 50.0,
        "preu_actual": 0.10, "co2_actual": 0.08,
        "preus_properes_24h": list(np.linspace(0.05, 0.25, 24)),
        "co2_properes_24h": list(np.linspace(0.04, 0.12, 24)),
        "noves_dades_5min": {"ultim_consum_kw": 1000.0, "ultima_solar_kw": 20.0},
    }
    obs.update(changes)
    return obs


def check_ok(obs):
    """L'agent no peta i retorna una potencia valida per al SOC que li donem."""
    p = load_agent(AGENT_DIR).act(obs)
    soc = obs["soc_kwh"] if isinstance(obs["soc_kwh"], float) and math.isfinite(obs["soc_kwh"]) else 0.0
    assert isinstance(p, float) and math.isfinite(p)
    assert -500 <= p <= 500
    assert p <= (2000 - soc) / ETA + 1e-9 and -p <= soc * ETA + 1e-9
    return p


def test_normal():
    check_ok(base_obs())


def test_nan_and_none():
    prices = list(np.linspace(0.05, 0.25, 24))
    prices[3], prices[7] = float("nan"), None
    co2 = list(np.linspace(0.04, 0.12, 24))
    co2[0] = float("inf")
    check_ok(base_obs(preus_properes_24h=prices, co2_properes_24h=co2))


def test_empty_and_short_lists():
    check_ok(base_obs(preus_properes_24h=[], co2_properes_24h=[]))
    check_ok(base_obs(preus_properes_24h=[0.2], co2_properes_24h=[0.1]))
    check_ok(base_obs(co2_properes_24h=list(np.linspace(0.04, 0.12, 20))))  # mides diferents


def test_soc_limits():
    check_ok(base_obs(soc_kwh=0.0))
    check_ok(base_obs(soc_kwh=2000.0))
    check_ok(base_obs(soc_kwh=float("nan")))


def test_no_discharge_when_campus_off():
    # tall del comptador: el campus no consumeix, no hem de descarregar
    obs = base_obs(soc_kwh=2000.0, preus_properes_24h=[0.30] * 24,
                   noves_dades_5min={"ultim_consum_kw": 0.0, "ultima_solar_kw": 0.0})
    assert check_ok(obs) >= 0.0


def test_backup_rule_if_lp_fails():
    agent = load_agent(AGENT_DIR)

    def broken(*args, **kwargs):
        raise ValueError("solver no disponible")

    type(agent).plan.__globals__["linprog"] = broken
    p = agent.act(base_obs())
    assert math.isfinite(p) and -500 <= p <= 500


def test_full_simulation():
    # 2.016 h seguides (amb salts entre setmanes), 0 infraccions i rapid
    data = valid_split(load_hourly())
    data = pd.concat([data, data.iloc[:2016 - len(data)]]) if len(data) < 2016 else data.iloc[:2016]
    t0 = time.time()
    r = run(load_agent(AGENT_DIR), data)
    secs = time.time() - t0
    print(f"  simulacio de {len(data)} h: score {r['score']}, infraccions {r['infraccions']}, {secs:.1f} s")
    assert r["infraccions"] == 0
    assert secs < 30


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print("OK   ", t.__name__)
        except Exception as e:
            failed += 1
            print("FALLA", t.__name__, "->", type(e).__name__, e)
    print(f"\n{len(tests) - failed}/{len(tests)} proves superades")
    sys.exit(1 if failed else 0)
