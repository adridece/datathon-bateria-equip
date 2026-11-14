"""
BatteryAgent per al Mode Dificil amb models de previsio (LightGBM).

Mateix esquema que dificil_previsio_simple (LP de 24 h + MPC amb la xarxa dins del LP), pero les previsions
les corregeixen models entrenats amb el train (scripts/train_dificil_lightgbm.py):
  - preu i CO2 de les hores +3..+23 (les 3 primeres ja les dona el mercat),
  - consum i solar de les hores +0..+23, sobretot la de l'hora actual: saber quant consumeix
    el campus ARA diu quant podem descarregar sense llencar energia.
Cada model corregeix una previsio senzilla (ultims dies a la mateixa hora + perfils del train).
Si algun model no es pot carregar, es fa servir la previsio senzilla tal qual.
"""
import json
import math
from datetime import datetime
from pathlib import Path

import numpy as np

try:
    from scipy.optimize import linprog
except Exception:  # sense scipy fem servir la regla de reserva
    linprog = None

try:
    import lightgbm as lgb
except Exception:
    lgb = None

ETA = 0.9 ** 0.5
EPS = 1e-3
HORIZON = 24
KNOWN = 3
LOAD_WINDOW = 2
NAN = float("nan")
FOLDER = Path(__file__).parent


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


def at(values, i):
    """values[i] si existeix; si no, NaN (els models saben treballar amb forats)."""
    return values[i] if 0 <= i < len(values) else NAN


def mean_last(values, k=24):
    v = [x for x in values[-k:] if x == x]
    return sum(v) / len(v) if v else NAN


def parse_time(ts):
    try:
        return datetime.strptime(str(ts)[:13], "%Y-%m-%d %H")
    except ValueError:
        return None


# ---------------------------------------------------------------- previsions senzilles
# Son la base: els models nomes aprenen a corregir-ne l'error.
def mean_lags(values, i, days=3):
    """Mitjana dels ultims dies a la mateixa hora (posicio i-24, i-48, i-72)."""
    v = [at(values, i - 24 * k) for k in range(1, days + 1)]
    v = [x for x in v if x == x]
    return sum(v) / len(v) if v else NAN


def market_base(hist, known, hour, dow, profile):
    """Preu o CO2 de les 24 h: ultims dies a la mateixa hora + perfil del mes, ajustat amb les 3 h conegudes."""
    full = hist + known
    n = len(hist)
    guess = []
    for j in range(HORIZON):
        g = mean_lags(full, n + j)
        if profile:
            prof = profile[int((dow + (hour + j) // 24) % 7 >= 5)][(hour + j) % 24]
            g = 0.5 * g + 0.5 * prof if g == g else prof
        guess.append(g if g == g else known[-1])
    ratio = sum(known) / max(sum(guess[:len(known)]), 1e-9)
    ratio = 1.0 + 0.75 * (min(max(ratio, 0.5), 2.0) - 1.0)
    return [g * ratio for g in guess]


def load_base(load, hour, dow, profile):
    """Consum de les 24 h: perfil del train per dia i hora, escalat amb les ultimes hores mesurades."""
    ratios = []
    for k in range(1, LOAD_WINDOW + 1):
        v = at(load, len(load) - k)
        if v == v and v > 1.0:
            h, d = (hour - k) % 24, (dow + (hour - k) // 24) % 7
            ratios.append(min(max(v / max(profile[d][h], 1.0), 0.3), 3.0))
    ratio = sum(ratios) / len(ratios) if ratios else 1.0
    return [profile[(dow + (hour + j) // 24) % 7][(hour + j) % 24] * ratio for j in range(HORIZON)]


def pv_base(pv, hour):
    """Solar de les 24 h: ultims dies a la mateixa hora; la resta d'avui, segons com de clar esta el dia."""
    n = len(pv)
    sky = 1.0
    last, yesterday = at(pv, n - 1), mean_lags(pv, n - 1)
    if hour > 6 and last == last and yesterday == yesterday and yesterday > 50.0:
        sky = 1.0 + 0.8 * (min(max(last / yesterday, 0.2), 3.0) - 1.0)
    out = []
    for j in range(HORIZON):
        g = mean_lags(pv, n + j)
        g = g if g == g else 0.0
        out.append(g * sky if hour + j < 24 else g)
    return out


# ---------------------------------------------------------------- variables dels models
# Les fan servir igual l'agent i scripts/train_dificil_lightgbm.py: no canviar l'una sense l'altre.
# L'ultima columna es la previsio senzilla; el model prediu (valor real - previsio senzilla).
def market_rows(hist, other_hist, known, other_known, hour, dow, month, irr_last, profile):
    """Una fila per hora futura (+3..+23) per predir preu o CO2."""
    full, other_full = hist + known, other_hist + other_known
    n = len(hist)
    base = market_base(hist, known, hour, dow, profile)
    rows = []
    for j in range(KNOWN, HORIZON):
        h, d = (hour + j) % 24, (dow + (hour + j) // 24) % 7
        rows.append([j, h, d, int(d >= 5), month, known[0], known[1], known[2],
                     other_known[0], other_known[1], other_known[2],
                     at(full, n + j - 24), at(full, n + j - 48), at(full, n - 24), at(full, n - 23), at(full, n - 22),
                     mean_last(hist), irr_last, at(other_full, n + j - 24), base[j]])
    return rows


def load_rows(load, temp, hour, dow, month, profile):
    """Una fila per hora (+0..+23) per predir el consum."""
    n = len(load)
    base = load_base(load, hour, dow, profile)
    last, last2, last3 = at(load, n - 1), at(load, n - 2), at(load, n - 3)
    prof_last = profile[(dow + (hour - 1) // 24) % 7][(hour - 1) % 24]
    night = min([x for x in load[-24:] if x == x], default=NAN)
    rows = []
    for j in range(HORIZON):
        h, d = (hour + j) % 24, (dow + (hour + j) // 24) % 7
        # dues maneres de continuar l'ultima mesura: com va canviar ahir i com canvia el perfil
        like_yesterday = last + at(load, n + j - 24) - at(load, n - 25)
        like_profile = last * profile[d][h] / max(prof_last, 1.0)
        rows.append([j, h, d, int(d >= 5), month, last, last2, last3, at(load, n + j - 24), at(load, n - 25),
                     mean_last(load), night, profile[d][h], like_yesterday, like_profile,
                     at(temp, len(temp) - 1), base[j]])
    return rows


def pv_rows(pv, irr, temp, hour, month, clear):
    """Una fila per hora (+0..+23) per predir la solar. clear = solar maxima del mes per hora (dia clar)."""
    n = len(pv)
    day_max = max([x for x in pv[-24:] if x == x], default=NAN)
    base = pv_base(pv, hour)
    last, irr_last = at(pv, n - 1), at(irr, len(irr) - 1)
    clear_last = clear[(hour - 1) % 24] if clear else NAN
    rows = []
    for j in range(HORIZON):
        h = (hour + j) % 24
        clear_h = clear[h] if clear else NAN
        # si l'ultima hora ha fet el 60 % d'un dia clar, suposem que la seguent tambe
        like_clear = last * clear_h / clear_last if clear_last == clear_last and clear_last > 20.0 else NAN
        rows.append([j, h, month, last, at(pv, n - 2), irr_last, at(irr, len(irr) - 2), at(pv, n + j - 24),
                     at(pv, n - 25), day_max, clear_h, clear_last, like_clear, at(temp, len(temp) - 1), base[j]])
    return rows


def load_model(name):
    try:
        return lgb.Booster(model_file=str(FOLDER / f"{name}.txt"))
    except Exception:
        return None


class BatteryAgent:
    def __init__(self):
        params = {}
        f = FOLDER / "params.json"
        if f.exists():
            with open(f, encoding="utf-8") as fh:
                params = json.load(fh)
        self.co2_ref = params.get("co2_ref", 0.0945)
        self.price_ref = params.get("price_ref", 0.1521)
        self.w_co2 = params.get("w_co2", 0.7)
        self.w_cost = params.get("w_cost", 0.3)
        self.safety = params.get("safety", 0.92)
        self.load_profile = params.get("load_profile")
        self.price_profile = params.get("price_profile") or {}
        self.co2_profile = params.get("co2_profile") or {}
        self.pv_clear = params.get("pv_clear") or {}
        self.models = {name: load_model(name) for name in ("price", "co2", "load", "pv")}
        # fins a quina hora (+j) corregim amb cada model; mes enlla, previsio senzilla
        self.near_hours = params.get("near_hours", {"price": 8, "co2": 8, "load": 2, "pv": 2})
        # historic de la simulacio (un valor per hora)
        self.price, self.co2, self.load, self.pv, self.irr, self.temp = [], [], [], [], [], []
        self.prev_time = None
        self.started = False

    def reset_history(self):
        self.price, self.co2, self.load, self.pv, self.irr, self.temp = [], [], [], [], [], []

    # ------------------------------------------------------------ previsions
    def predict(self, name, rows):
        """Previsio senzilla (ultima columna) + la correccio del model a les hores mes properes,
        que es on el model encerta mes i on mes importa (sobretot l'hora actual)."""
        rows = np.array(rows, dtype=float)
        out = rows[:, -1].copy()
        model = self.models.get(name)
        if model is not None:
            try:
                close = rows[:, 0] <= self.near_hours.get(name, 0)
                if close.any():
                    out[close] += model.predict(rows[close])
            except Exception:
                out = rows[:, -1].copy()
        return np.maximum(out, 0.0)

    def forecast_market(self, name, hist, other_hist, known, other_known, hour, dow, month, irr_last):
        profile = (self.price_profile if name == "price" else self.co2_profile).get(str(month))
        rows = market_rows(hist, other_hist, known, other_known, hour, dow, month, irr_last, profile)
        return np.concatenate([known, self.predict(name, rows)])

    def forecast_net(self, hour, dow, month):
        load = self.predict("load", load_rows(self.load, self.temp, hour, dow, month, self.load_profile))
        pv = self.predict("pv", pv_rows(self.pv, self.irr, self.temp, hour, month, self.pv_clear.get(str(month))))
        return load - pv

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
        now = parse_time(obs.get("timestamp"))
        month = now.month if now else 0
        prices = clean_list(obs.get("preus_properes_24h"), to_float(obs.get("preu_actual"), self.price_ref))
        co2 = clean_list(obs.get("co2_properes_24h"), to_float(obs.get("co2_actual"), self.co2_ref))
        n_known = min(len(prices), len(co2))
        prices, co2 = prices[:n_known], co2[:n_known]

        # entre setmanes de test hi ha un salt d'un mes: l'historic vell ja no serveix
        jump = now is not None and self.prev_time is not None and abs((now - self.prev_time).total_seconds()) > 5400
        if jump:
            self.reset_history()
        if self.started and not jump:
            last = obs.get("noves_dades_5min") or {}
            self.load.append(max(to_float(last.get("ultim_consum_kw"), NAN), 0.0))
            self.pv.append(max(to_float(last.get("ultima_solar_kw"), NAN), 0.0))
            self.irr.append(to_float(last.get("irradiancia_wm2"), NAN))
            self.temp.append(to_float(last.get("temp_ambient_c"), NAN))
        self.started, self.prev_time = True, now
        irr_last = at(self.irr, len(self.irr) - 1)

        if n_known < KNOWN:
            # final de la simulacio: nomes queden aquestes hores
            p_fc, c_fc = np.array(prices), np.array(co2)
        else:
            p_fc = self.forecast_market("price", self.price, self.co2, prices, co2, hour, dow, month, irr_last)
            c_fc = self.forecast_market("co2", self.co2, self.price, co2, prices, hour, dow, month, irr_last)
        H = len(p_fc)
        w = self.w_co2 * c_fc / self.co2_ref + self.w_cost * p_fc / self.price_ref
        net = self.forecast_net(hour, dow, month)[:H]
        self.price.append(prices[0])
        self.co2.append(co2[0])

        try:
            p = self.plan(soc, w, net, cap, pmax)
        except Exception:
            p = self.backup_rule(w, net[0], pmax)

        # no descarreguem mes del consum net que esperem ara (amb un marge per l'error de previsio)
        if p < 0:
            p = max(p, -max(net[0], 0.0) * self.safety)
        max_c = max(0.0, min(pmax, (cap - soc) / ETA - 1e-4))
        max_d = max(0.0, min(pmax, soc * ETA - 1e-4))
        p = min(max(to_float(p, 0.0), -max_d), max_c)
        return float(p)
