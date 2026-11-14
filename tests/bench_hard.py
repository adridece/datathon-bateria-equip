"""
Banc de proves honest del Mode Dificil.
Per a cada validacio (F0 = ultima setmana de cada mes del train, F1 = la d'abans, F2 = la d'abans encara)
entrena els models SENSE aquelles setmanes, avalua l'agent i calcula l'optim teoric (sabent tot el futur).

    python tests/bench_hard.py                 (agents/hard_v3, F0 i F1)
    python tests/bench_hard.py 0,1,2           (tambe F2, la que reservem per comprovar al final)

Un canvi nomes es queda si millora totes les validacions: aixi evitem ajustar-nos a unes setmanes concretes.
"""
import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.sparse import csr_matrix, eye, hstack, tril, vstack

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data import contiguous_blocks, load_hourly  # noqa: E402
from src.evaluate import load_agent  # noqa: E402
from tests.evaluate_hard import run_hard  # noqa: E402


def split(d, k):
    """Setmana k (comptant des del final) de cada mes com a test; el train acaba just abans."""
    train, test = [], []
    for b in contiguous_blocks(d):
        if len(b) < 24 * 17:
            train.append(b)
            continue
        lo, hi = len(b) - 24 * 7 * (k + 1), len(b) - 24 * 7 * k
        test.append(b.iloc[lo:hi])
        train.append(b.iloc[:lo])
    return pd.concat(train), pd.concat(test)


def oracle(test, cap=6000.0, pmax=1500.0):
    """Optim teoric: LP sobre totes les hores sabent consum, solar, preu i CO2 exactes."""
    net = (test.load_kw - test.pv_kw).values
    co2, price = test.co2_kg_per_kwh.values, test.precio_eur_per_kwh.values
    base = np.clip(net, 0, None)
    C, K = (base * co2).sum(), (base * price).sum()
    n, eta = len(net), 0.9 ** 0.5
    L = tril(np.ones((n, n)), format="csr")
    soc = hstack([eta * L, -L / eta, csr_matrix((n, n))])
    A = vstack([soc, -soc, hstack([eye(n), -eye(n), -eye(n)])])     # xarxa >= consum net + carrega - descarrega
    b = np.concatenate([np.full(n, cap / 2), np.full(n, cap / 2), -net])
    w = 0.7 * co2 / C + 0.3 * price / K
    res = linprog(np.concatenate([np.zeros(2 * n), w * n]), A_ub=A, b_ub=b,
                  bounds=[(0, pmax)] * (2 * n) + [(0, None)] * n, method="highs")
    grid = res.x[2 * n:]
    return round(70 * (1 - (grid * co2).sum() / C) + 30 * (1 - (grid * price).sum() / K), 3)


def train_module():
    spec = importlib.util.spec_from_file_location("train_hard_v3", ROOT / "scripts" / "train_hard_v3.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    folds = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 else [0, 1]
    d = load_hourly().copy()
    d["pv_kw"] = d["pv_kw"] * 12.0
    trainer = train_module()
    for k in folds:
        train, test = split(d, k)
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "agent"
            shutil.copytree(ROOT / "agents" / "hard_v3", work)
            trainer.train(train, work, seeds_base=2)
            res = run_hard(load_agent(work), test)
        best = oracle(test)
        print(f"F{k}: agent {res['score']:.3f}  òptim {best:.3f}  ({100 * res['score'] / best:.1f} % de l'òptim), "
              f"infraccions {res['infraccions']}", flush=True)


if __name__ == "__main__":
    main()
