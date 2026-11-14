"""
BatteryAgent - versio robusta de estandard_lp.

Mateixa idea que estandard_lp (LP de 24 h + MPC, veure docs/DECISIONS.md D-003), pero:
  - No descarreguem mes del que ha consumit el campus l'hora anterior (si hi ha un
    tall del comptador, el que descarreguem es perdria).
  - Netegem l'obs (NaN, llistes buides o de mida diferent).
  - Si el LP falla per qualsevol motiu, fem servir una regla senzilla de reserva.
"""
import json
import math
from pathlib import Path

import numpy as np

try:
    from scipy.optimize import linprog
except Exception:  # si scipy no hi es, farem servir la regla de reserva
    linprog = None

CAP = 2000.0
PMAX = 500.0
ETA = 0.9 ** 0.5
EPS = 1e-3


def to_float(x, default):
    """Converteix a float; si no es un numero valid, retorna default."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    return v if math.isfinite(v) else default


def clean_list(values, current):
    """Llista de 24 h neta: els valors dolents es substitueixen per l'ultim bo."""
    out = []
    last = current
    for v in list(values or []):
        last = to_float(v, last)
        out.append(last)
    if not out:
        out = [current]
    return np.array(out, dtype=float)


class BatteryAgent:
    def __init__(self):
        params = {}
        f = Path(__file__).parent / "params.json"
        if f.exists():
            with open(f, encoding="utf-8") as fh:
                params = json.load(fh)
        self.co2_ref = params.get("co2_ref", 0.0921)
        self.price_ref = params.get("preu_ref", 0.1568)
        self.w_co2 = params.get("w_co2", 0.7)
        self.w_cost = params.get("w_cost", 0.3)

    def plan(self, soc0, w, max_dis_now):
        """LP sobre l'horitzo. Retorna la potencia de la primera hora."""
        H = len(w)
        cost = np.concatenate([w, -w])
        # SOC acumulat: 0 <= soc0 + ETA*cumsum(c) - cumsum(d)/ETA <= CAP
        L = np.tril(np.ones((H, H)))
        A = np.vstack([np.hstack([ETA * L, -L / ETA]), np.hstack([-ETA * L, L / ETA])])
        b = np.concatenate([np.full(H, CAP - EPS - soc0), np.full(H, soc0 - EPS)])
        # la primera hora no pot descarregar mes del consum net que esperem
        bounds = [(0, PMAX)] * H + [(0, max_dis_now)] + [(0, PMAX)] * (H - 1)
        res = linprog(cost, A_ub=A, b_ub=b, bounds=bounds, method="highs")
        if not res.success:
            raise RuntimeError("LP sense solucio")
        return float(res.x[0] - res.x[H])

    def backup_rule(self, w, soc):
        """Regla de reserva: carregar a les hores netes i descarregar a les brutes."""
        if len(w) < 2:
            return -PMAX  # final de la simulacio: buidem la bateria
        if w[0] <= np.percentile(w, 25):
            return PMAX
        if w[0] >= np.percentile(w, 75):
            return -PMAX
        return 0.0

    def act(self, obs: dict) -> float:
        soc = min(max(to_float(obs.get("soc_kwh"), 0.0), 0.0), CAP)
        price_now = to_float(obs.get("preu_actual"), self.price_ref)
        co2_now = to_float(obs.get("co2_actual"), self.co2_ref)
        prices = clean_list(obs.get("preus_properes_24h"), price_now)
        co2 = clean_list(obs.get("co2_properes_24h"), co2_now)
        n = min(len(prices), len(co2))
        w = self.w_co2 * co2[:n] / self.co2_ref + self.w_cost * prices[:n] / self.price_ref

        # consum net de l'hora anterior (si no el sabem, suposem que no limita)
        last = obs.get("noves_dades_5min") or {}
        net = to_float(last.get("ultim_consum_kw"), PMAX) - to_float(last.get("ultima_solar_kw"), 0.0)
        max_dis_now = min(PMAX, max(net, 0.0))

        try:
            p = self.plan(soc, w, max_dis_now)
        except Exception:
            p = self.backup_rule(w, soc)

        # mai descarreguem mes del que consumeix el campus
        p = max(p, -max_dis_now)
        # safety clamp (0 infraccions)
        max_c = max(0.0, min(PMAX, (CAP - soc) / ETA - 1e-4))
        max_d = max(0.0, min(PMAX, soc * ETA - 1e-4))
        p = min(max(to_float(p, 0.0), -max_d), max_c)
        return float(p)
