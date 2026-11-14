"""
BatteryAgent - MPC (control predictiu) amb programacio lineal.

Idea (veure docs/DECISIONS.md, D-003):
  - El preu i el CO2 de les properes 24h ens els donen EXACTES a obs.
  - La demanda neta del campus gairebe sempre es > 500 kW, aixi que tota l'energia
    que descarreguem es consumeix al campus (no es perd).
  - Aleshores la puntuacio es lineal en la potencia de la bateria:
        cada kWh importat a l'hora t "costa"  w_t = 0.7*co2_t/CO2_REF + 0.3*preu_t/PREU_REF
    i podem resoldre un LP sobre l'horitzo de 24h, aplicar nomes la primera hora
    i tornar-ho a resoldre a la seguent (rolling horizon / MPC).
"""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

CAP = 2000.0
PMAX = 500.0
ETA = 0.9 ** 0.5
EPS = 1e-3


class BatteryAgent:
    def __init__(self):
        params = {}
        f = Path(__file__).parent / "params.json"
        if f.exists():
            with open(f, encoding="utf-8") as fh:
                params = json.load(fh)
        # mitjanes ponderades del baseline al train (per normalitzar CO2 i preu)
        self.co2_ref = params.get("co2_ref", 0.0921)
        self.preu_ref = params.get("preu_ref", 0.1568)
        self.w_co2 = params.get("w_co2", 0.7)
        self.w_cost = params.get("w_cost", 0.3)
        # valor de l'energia que queda a la bateria al final de l'horitzo
        self.terminal = params.get("terminal", 0.0)

    # ------------------------------------------------------------------
    def _plan(self, soc0, w, terminal_value):
        H = len(w)
        # variables: c_0..c_{H-1}, d_0..d_{H-1}
        cost = np.concatenate([w, -w])
        # valor terminal: soc_H = soc0 + ETA*sum(c) - sum(d)/ETA  -> restem V*soc_H
        cost[:H] -= terminal_value * ETA
        cost[H:] += terminal_value / ETA
        # restriccions de SOC acumulat: 0 <= soc0 + ETA*cumsum(c) - cumsum(d)/ETA <= CAP
        L = np.tril(np.ones((H, H)))
        A_up = np.hstack([ETA * L, -L / ETA])            # soc_t <= CAP
        b_up = np.full(H, CAP - EPS - soc0)
        A_lo = np.hstack([-ETA * L, L / ETA])            # soc_t >= 0
        b_lo = np.full(H, soc0 - EPS)
        res = linprog(cost, A_ub=np.vstack([A_up, A_lo]), b_ub=np.concatenate([b_up, b_lo]),
                      bounds=[(0, PMAX)] * (2 * H), method="highs")
        if not res.success:
            return 0.0
        return float(res.x[0] - res.x[H])

    def act(self, obs: dict) -> float:
        preus = np.asarray(obs["preus_properes_24h"], dtype=float)
        co2 = np.asarray(obs["co2_properes_24h"], dtype=float)
        w = self.w_co2 * co2 / self.co2_ref + self.w_cost * preus / self.preu_ref
        # si l'horitzo es mes curt de 24h vol dir que s'acaba la simulacio: l'energia
        # que quedi a la bateria no val res
        if len(w) < 24:
            V = 0.0
        else:
            V = self.terminal * float(np.mean(w))
        soc = float(obs["soc_kwh"])
        p = self._plan(soc, w, V)

        # safety clamp (0 infraccions)
        max_c = max(0.0, min(PMAX, (CAP - soc) / ETA - 1e-4))
        max_d = max(0.0, min(PMAX, soc * ETA - 1e-4))
        return float(np.clip(p, -max_d, max_c))
