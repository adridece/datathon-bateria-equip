"""
BatteryAgent per al Mode Dificil (6.000 kWh, +-1.500 kW, solar x12, nomes 3 h de mercat).

Mateixa idea que estandard_robust (LP de 24 h + MPC), amb dues peces noves:
  - Previsions: de preu i CO2 nomes en sabem 3 h, la resta de les 24 h les estimem amb
    els ultims dies a la mateixa hora. El consum i la solar tambe els estimem.
  - La xarxa entra al LP: xarxa >= consum - solar + bateria i xarxa >= 0. Aixi el pla
    aprofita l'excedent solar (carregar surt gratis) i no descarrega mes del que es consumeix.
"""
import json
import math
from collections import deque
from pathlib import Path

import numpy as np

try:
    from scipy.optimize import linprog
except Exception:  # sense scipy fem servir la regla de reserva
    linprog = None

ETA = 0.9 ** 0.5
EPS = 1e-3
HORIZON = 24


def to_float(x, default):
    """Converteix a float; si no es un numero valid, retorna default."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    return v if math.isfinite(v) else default


def clean_list(values, current):
    """Llista neta: els valors dolents es substitueixen per l'ultim bo."""
    out = []
    last = current
    for v in list(values or []):
        last = to_float(v, last)
        out.append(last)
    return out or [current]


def get_month(ts):
    """Mes (1-12) del timestamp, tant si es un Timestamp com un text 'AAAA-MM-DD ...'."""
    try:
        return int(ts.month)
    except AttributeError:
        try:
            return int(str(ts)[5:7])
        except ValueError:
            return 0


class HourlyMemory:
    """Guarda els ultims valors vistos a cada hora del dia (0-23)."""

    def __init__(self, days):
        self.values = [deque(maxlen=days) for _ in range(24)]

    def add(self, hour, value):
        self.values[hour % 24].append(value)

    def mean(self, hour, default):
        v = self.values[hour % 24]
        return sum(v) / len(v) if v else default


class BatteryAgent:
    def __init__(self, **override):
        params = {}
        f = Path(__file__).parent / "params.json"
        if f.exists():
            with open(f, encoding="utf-8") as fh:
                params = json.load(fh)
        params.update(override)
        self.co2_ref = params.get("co2_ref", 0.0921)
        self.price_ref = params.get("price_ref", 0.1568)
        self.w_co2 = params.get("w_co2", 0.7)
        self.w_cost = params.get("w_cost", 0.3)
        # perfil de consum del train per dia de la setmana i hora (7 x 24)
        self.load_profile = params.get("load_profile")
        # perfils de preu i CO2 del train: {mes: [feiner 24 h, cap de setmana 24 h]}
        self.price_profile = params.get("price_profile") or {}
        self.co2_profile = params.get("co2_profile") or {}
        self.mix = params.get("mix", 0.5)
        self.market_days = params.get("market_days", 2)
        self.level_fix = params.get("level_fix", 0.5)
        self.safety = params.get("safety", 1.0)
        self.price_mem = HourlyMemory(self.market_days)
        self.co2_mem = HourlyMemory(self.market_days)
        self.load_mem = HourlyMemory(params.get("load_days", 1))
        self.pv_mem = HourlyMemory(params.get("pv_days", 2))
        self.load_ratio = 1.0
        self.sky_fix = params.get("sky_fix", 0.0)
        self.sky = 1.0

    # ------------------------------------------------------------ previsions
    def forecast_market(self, known, memory, hour, dow=0, profile=None):
        """Les primeres hores son exactes; la resta, mitjana dels ultims dies a la mateixa hora."""
        n = len(known)
        guess = []
        for j in range(HORIZON):
            g = memory.mean(hour + j, known[-1])
            # perfil del train del mateix mes (feiner o cap de setmana), barrejat amb els ultims dies
            if profile is not None:
                weekend = 1 if (dow + (hour + j) // 24) % 7 >= 5 else 0
                g = self.mix * g + (1.0 - self.mix) * profile[weekend][(hour + j) % 24]
            guess.append(g)
        # si avui tot va mes car/brut que els ultims dies, ho corregim una mica
        ratio = sum(known) / max(sum(guess[:n]), 1e-9)
        ratio = 1.0 + self.level_fix * (min(max(ratio, 0.5), 2.0) - 1.0)
        return np.array(known + [g * ratio for g in guess[n:]])

    def forecast_load(self, hour, dow, last_load):
        out = []
        for j in range(HORIZON):
            h, d = (hour + j) % 24, (dow + (hour + j) // 24) % 7
            if self.load_profile:
                out.append(self.load_profile[d][h] * self.load_ratio)
            else:
                out.append(self.load_mem.mean(h, last_load))
        return np.array(out)

    def forecast_pv(self, hour, last_pv):
        """Solar d'ahir a la mateixa hora; la resta d'avui es corregeix segons com de clar esta el dia."""
        out = []
        for j in range(HORIZON):
            pv = self.pv_mem.mean(hour + j, last_pv if j == 0 else 0.0)
            if hour + j < 24:
                pv *= self.sky
            out.append(pv)
        return np.array(out)

    # ------------------------------------------------------------ pla
    def plan(self, soc0, w, net, cap, pmax):
        """LP: variables carrega, descarrega i xarxa de cada hora. Retorna la potencia d'ara."""
        H = len(w)
        L = np.tril(np.ones((H, H)))
        I, Z = np.eye(H), np.zeros((H, H))
        A = np.vstack([
            np.hstack([ETA * L, -L / ETA, Z]),     # soc <= cap
            np.hstack([-ETA * L, L / ETA, Z]),     # soc >= 0
            np.hstack([I, -I, -I]),                # xarxa >= net + carrega - descarrega
        ])
        b = np.concatenate([np.full(H, cap - EPS - soc0), np.full(H, soc0 - EPS), -net])
        cost = np.concatenate([np.zeros(2 * H), w])
        res = linprog(cost, A_ub=A, b_ub=b, bounds=[(0, pmax)] * (2 * H) + [(0, None)] * H, method="highs")
        if not res.success:
            raise RuntimeError("LP sense solucio")
        return float(res.x[0] - res.x[H])

    def backup_rule(self, w, net_now, pmax):
        """Regla de reserva: carregar amb excedent solar o a les hores netes, descarregar a les brutes."""
        if net_now < 0:
            return min(pmax, -net_now)
        if w[0] <= np.percentile(w, 25):
            return pmax
        if w[0] >= np.percentile(w, 75):
            return -min(pmax, net_now)
        return 0.0

    def act(self, obs: dict) -> float:
        cap = to_float(obs.get("cap_max_kwh"), 6000.0)
        pmax = to_float(obs.get("power_max_kw"), 1500.0)
        soc = min(max(to_float(obs.get("soc_kwh"), 0.0), 0.0), cap)
        hour = int(to_float(obs.get("hour"), 0)) % 24
        dow = int(to_float(obs.get("day_of_week"), 0)) % 7
        prices = clean_list(obs.get("preus_properes_24h"), to_float(obs.get("preu_actual"), self.price_ref))
        co2 = clean_list(obs.get("co2_properes_24h"), to_float(obs.get("co2_actual"), self.co2_ref))
        n_known = min(len(prices), len(co2))
        prices, co2 = prices[:n_known], co2[:n_known]

        # mesures de l'hora anterior
        last = obs.get("noves_dades_5min") or {}
        last_load = max(to_float(last.get("ultim_consum_kw"), 1000.0), 0.0)
        last_pv = max(to_float(last.get("ultima_solar_kw"), 0.0), 0.0)
        # si l'ultima hora ha fet mes (o menys) sol que ahir a la mateixa hora, avui continuara igual
        yesterday_pv = self.pv_mem.mean(hour - 1, 0.0)
        if hour <= 6:
            self.sky = 1.0
        elif yesterday_pv > 50.0:
            ratio = min(max(last_pv / yesterday_pv, 0.2), 3.0)
            self.sky = 1.0 + self.sky_fix * (ratio - 1.0)
        self.load_mem.add(hour - 1, last_load)
        self.pv_mem.add(hour - 1, last_pv)
        if self.load_profile and last_load > 1.0:
            ref = self.load_profile[(dow - (1 if hour == 0 else 0)) % 7][(hour - 1) % 24]
            self.load_ratio = 0.7 * self.load_ratio + 0.3 * min(max(last_load / max(ref, 1.0), 0.3), 3.0)

        # el final de la simulacio es nota perque arriben menys de 3 hores de mercat
        if n_known < 3:
            p_fc, c_fc = np.array(prices), np.array(co2)
        else:
            month = str(get_month(obs.get("timestamp")))
            p_fc = self.forecast_market(prices, self.price_mem, hour, dow, self.price_profile.get(month))
            c_fc = self.forecast_market(co2, self.co2_mem, hour, dow, self.co2_profile.get(month))
        H = len(p_fc)
        w = self.w_co2 * c_fc / self.co2_ref + self.w_cost * p_fc / self.price_ref
        net = (self.forecast_load(hour, dow, last_load) - self.forecast_pv(hour, last_pv))[:H]

        # guardem el mercat real d'aquesta hora per a les previsions dels propers dies
        self.price_mem.add(hour, prices[0])
        self.co2_mem.add(hour, co2[0])

        try:
            p = self.plan(soc, w, net, cap, pmax)
        except Exception:
            p = self.backup_rule(w, net[0], pmax)

        # no descarreguem mes del consum net que esperem ara (amb un marge)
        if p < 0:
            p = max(p, -max(net[0], 0.0) * self.safety)
        max_c = max(0.0, min(pmax, (cap - soc) / ETA - 1e-4))
        max_d = max(0.0, min(pmax, soc * ETA - 1e-4))
        p = min(max(to_float(p, 0.0), -max_d), max_c)
        return float(p)
