"""
BatteryAgent final per al Mode Dificil (6.000 kWh, +-1.500 kW, solar x12, 3 h de mercat).

LP de 24 h + MPC amb la xarxa dins del LP (aprofita l'excedent solar i no descarrega mes del que es
consumeix). Les previsions son senzilles (ultims dies a la mateixa hora + perfils del train) i uns models
LightGBM (scripts/train_hard_final.py, 5 llavors) les corregeixen:
  - consum i solar de l'hora actual i les 2 seguents,
  - CO2 de les hores +3..+8 i preu de totes les hores; a +3/+4 h hi barregem la forma d'ahir ancorada
    a l'ultima hora coneguda.
Decisions amb incertesa (errors de previsio mesurats fora de mostra, per hora del dia):
  - el pla compta amb una mica menys de consum a les hores on la previsio falla mes,
  - a l'hora actual no descarreguem mes del que el campus segur que consumira,
  - amb excedent solar carreguem pensant en el cas de mes sol (carregar de menys perd energia gratis).
El primer dia de cada setmana fem servir els ultims dies del train com a historial.
v3: el CO2 de les hores +3..+12 es barreja meitat i meitat amb un model directe que mira la corba sencera de les
ultimes 48 h (scripts/train_hard_v3.py). Millora les tres validacions independents (docs/DIARI.md).
A mes, l'agent comprova sol si la irradiancia que rep es de l'hora actual o de la passada (compara-la amb la solar
de l'hora passada). Si es de l'hora actual, la solar d'ara surt gairebe exacta de la irradiancia (correlacio 0,995).
Si algun model no es pot carregar, es fa servir la previsio senzilla.
"""
import json
import math
from datetime import datetime, timedelta
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


def pv_base(pv, hour, typical=None):
    """Solar de les 24 h: ultims dies a la mateixa hora (o el perfil tipic del mes si encara no en tenim);
    la resta d'avui, segons com de clar esta el dia."""
    n = len(pv)
    sky = 1.0
    last, yesterday = at(pv, n - 1), mean_lags(pv, n - 1)
    if yesterday != yesterday and typical:
        yesterday = typical[(hour - 1) % 24]
    if hour > 6 and last == last and yesterday == yesterday and yesterday > 50.0:
        sky = 1.0 + 0.8 * (min(max(last / yesterday, 0.2), 3.0) - 1.0)
    out = []
    for j in range(HORIZON):
        g = mean_lags(pv, n + j)
        if g != g:
            g = typical[(hour + j) % 24] if typical else 0.0
        out.append(g * sky if hour + j < 24 else g)
    return out


# ---------------------------------------------------------------- variables dels models
# Les fan servir igual l'agent i scripts/train_hard.py: no canviar l'una sense l'altre.
# L'ultima columna es la previsio senzilla; el model prediu (valor real - previsio senzilla).
def anchored(full, n, j):
    """La forma d'ahir i d'abans d'ahir enganxada a l'ultima hora de mercat coneguda (posicio n+2)."""
    last = full[n + 2]
    out = []
    for k in (24, 48):
        ref, then = at(full, n + 2 - k), at(full, n + j - k)
        out.append(last * then / ref if ref == ref and then == then and ref > 1e-6 else NAN)
        out.append(last + then - ref if ref == ref and then == then else NAN)
    return out


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
                     mean_last(hist), irr_last, at(other_full, n + j - 24)] + anchored(full, n, j) + [base[j]])
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


def pv_rows(pv, irr, temp, hour, month, clear, typical=None):
    """Una fila per hora (+0..+23) per predir la solar. clear = solar maxima del mes per hora (dia clar)."""
    n = len(pv)
    day_max = max([x for x in pv[-24:] if x == x], default=NAN)
    base = pv_base(pv, hour, typical)
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


def co2_direct_rows(co2_past, price_past, co2_known, price_known, hour, dow, month, irr1, irr25, hours):
    """Variables del model directe de CO2: les ultimes 48 h de CO2 i 24 h de preu i les 3 hores conegudes,
    tot relatiu a l'ultima hora coneguda (aixi el model apren la forma, no el nivell)."""
    lvl, pl = co2_known[2], price_known[2]
    base = [x / lvl for x in co2_past] + [x / lvl for x in co2_known[:3]] + [x / pl for x in price_past] + \
           [x / pl for x in price_known[:3]] + [hour, dow, month, irr1, irr25, lvl, sum(co2_past[-24:]) / 24 / lvl]
    return [base + [j] for j in hours]


def load_model(name, seeds=1):
    """Carrega els models d'una serie (un per llavor). Si no n'hi ha cap, None."""
    models = []
    for k in range(seeds):
        try:
            models.append(lgb.Booster(model_file=str(FOLDER / f"{name}_{k}.txt")))
        except Exception:
            pass
    return models or None


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
        self.pv_mean = params.get("pv_mean") or {}
        self.safety_night = params.get("safety_night", self.safety)
        self.pv_now = 0.0
        self.history = params.get("history") or {}
        self.surplus_boost = params.get("surplus_boost", True)
        self.surplus_q = params.get("surplus_q", 4)
        self.plan_surplus = params.get("plan_surplus", False)
        self.plan_margin = params.get("plan_margin", True)
        self.anchor_weight = params.get("anchor_weight", {"co2": [1.0, 0.5], "price": [0.5]})
        # errors passats del consum net de l'hora actual, per hora del dia (quantils 5..50 %)
        self.net_errors = params.get("net_errors") or {}
        self.quantile = params.get("quantile")
        self.models = {name: load_model(name, params.get("seeds", 1)) for name in ("price", "co2", "load", "pv")}
        direct = params.get("co2_direct") or {}
        self.co2_direct_hours = list(range(direct.get("first", 3), direct.get("last", 12) + 1))
        self.co2_direct_weight = direct.get("weight", 0.5)
        self.co2_direct = load_model("co2d", direct.get("seeds", 1)) if direct else None
        # irradiancia de l'hora actual: es detecta durant la simulacio (veure check_irradiance)
        self.pv_per_irr = params.get("pv_per_irr", 1.63)
        self.margin_irr_now = params.get("margin_irr_now", 0.7)
        self.base_errors = dict(self.net_errors)
        self.irr_prev, self.err_if_past, self.err_if_now, self.irr_checks = None, 0.0, 0.0, 0
        self.irr_now = None
        # fins a quina hora (+j) corregim amb cada model; mes enlla, previsio senzilla
        self.near_hours = params.get("near_hours", {"price": 8, "co2": 8, "load": 2, "pv": 2})
        # historic de la simulacio (un valor per hora)
        self.price, self.co2, self.load, self.pv, self.irr, self.temp = [], [], [], [], [], []
        self.prev_time = None
        self.started = False

    def seed_history(self, now):
        """Omple l'historic amb les ultimes hores del train si acaben just abans d'ara."""
        if now is None:
            return False
        h = self.history.get((now - timedelta(hours=1)).strftime("%Y-%m-%d %H"))
        if not h:
            return False
        clean = lambda v: [to_float(x, NAN) for x in v]
        self.price, self.co2 = clean(h["price"]), clean(h["co2"])
        self.load, self.pv = clean(h["load"]), clean(h["pv"])
        self.irr, self.temp = clean(h["irr"]), clean(h["temp"])
        return True

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
                    out[close] += np.mean([m.predict(rows[close]) for m in model], axis=0)
            except Exception:
                out = rows[:, -1].copy()
        return np.maximum(out, 0.0)

    def forecast_market(self, name, hist, other_hist, known, other_known, hour, dow, month, irr_last):
        profile = (self.price_profile if name == "price" else self.co2_profile).get(str(month))
        rows = market_rows(hist, other_hist, known, other_known, hour, dow, month, irr_last, profile)
        pred = self.predict(name, rows)
        # a les primeres hores, la forma d'ahir/abans d'ahir ancorada a l'ultima hora coneguda encerta
        # mes que el model: les barregem (pes de la formula per hora +3, +4, ...)
        for i, wgt in enumerate(self.anchor_weight.get(name, [])):
            if i < len(pred):
                a24, a48 = rows[i][-5], rows[i][-3]
                anc = a24 if a48 != a48 else (a48 if a24 != a24 else 0.5 * (a24 + a48))
                if anc == anc:
                    pred[i] = wgt * anc + (1.0 - wgt) * pred[i]
        out = np.concatenate([known, pred])
        if name == "co2":
            out = self.blend_co2_direct(out, hist, other_hist, known, other_known, hour, dow, month)
        return out

    def blend_co2_direct(self, out, co2_hist, price_hist, co2_known, price_known, hour, dow, month):
        """Barreja el CO2 de les hores +3..+12 amb el model directe (si hi ha prou historial i el model)."""
        if not self.co2_direct or len(co2_hist) < 48 or len(price_hist) < 24 or len(co2_known) < 3 or len(self.irr) < 25:
            return out
        c, p = list(co2_hist[-48:]), list(price_hist[-24:])
        if any(x != x for x in c + p) or co2_known[2] <= 0 or price_known[2] <= 0:
            return out
        irr1 = self.irr[-1] if self.irr[-1] == self.irr[-1] else 0.0
        irr25 = self.irr[-25] if self.irr[-25] == self.irr[-25] else 0.0
        try:
            rows = np.array(co2_direct_rows(c, p, list(co2_known), list(price_known), hour, dow, month, irr1, irr25,
                                            self.co2_direct_hours), dtype=float)
            pred = np.mean([m.predict(rows) for m in self.co2_direct], axis=0) * co2_known[2]
        except Exception:
            return out
        out = np.array(out, dtype=float)
        for j, v in zip(self.co2_direct_hours, pred):
            if j < len(out) and v > 0:
                out[j] = self.co2_direct_weight * v + (1.0 - self.co2_direct_weight) * out[j]
        return out

    def forecast_net(self, hour, dow, month):
        load = self.predict("load", load_rows(self.load, self.temp, hour, dow, month, self.load_profile))
        pv = self.predict("pv", pv_rows(self.pv, self.irr, self.temp, hour, month, self.pv_clear.get(str(month)),
                                         self.pv_mean.get(str(month))))
        if self.irr_now is not None:
            pv[0] = self.pv_per_irr * self.irr_now      # la irradiancia d'ara diu quanta solar hi ha ara
        self.pv_now = float(pv[0])
        return load - pv

    def check_irradiance(self, last, jump):
        """Mira si la irradiancia que arriba es de l'hora actual: si ho es, la de l'hora anterior s'assembla molt
        mes a la solar de l'hora passada que no pas la d'ara. Funciona igual si la web la dona d'una manera o d'una altra."""
        if jump:
            self.irr_prev = None
        irr, pv_last = to_float(last.get("irradiancia_wm2"), NAN), to_float(last.get("ultima_solar_kw"), NAN)
        if irr != irr or pv_last != pv_last:
            self.irr_now = None
            return
        if self.irr_prev is not None and (pv_last > 50 or irr > 30 or self.irr_prev > 30):
            self.err_if_past += abs(pv_last - self.pv_per_irr * irr)
            self.err_if_now += abs(pv_last - self.pv_per_irr * self.irr_prev)
            self.irr_checks += 1
        self.irr_prev = irr
        now = self.irr_checks >= 6 and self.err_if_now < 0.6 * self.err_if_past
        self.irr_now = irr if now else None
        # sabent la solar d'ara la previsio falla menys: el marge de seguretat pot ser mes petit
        scale = self.margin_irr_now if now else 1.0
        self.net_errors = {h: [x * scale for x in v] for h, v in self.base_errors.items()}

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
        if jump or not self.started:
            self.reset_history()
            # si el train acaba just l'hora abans, en recuperem els ultims dies
            seeded = self.seed_history(now)
        else:
            seeded = False
        if self.started and not jump and not seeded:
            last = obs.get("noves_dades_5min") or {}
            self.load.append(max(to_float(last.get("ultim_consum_kw"), NAN), 0.0))
            self.pv.append(max(to_float(last.get("ultima_solar_kw"), NAN), 0.0))
            self.irr.append(to_float(last.get("irradiancia_wm2"), NAN))
            self.temp.append(to_float(last.get("temp_ambient_c"), NAN))
        self.started, self.prev_time = True, now
        self.check_irradiance(obs.get("noves_dades_5min") or {}, jump)
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

        # el pla sap que a algunes hores el consum net es preveu pitjor: alla compta amb menys consum
        # (nomes per a descarregar; l'excedent solar es queda igual)
        net_plan = np.array(net, dtype=float)
        if self.plan_margin and self.net_errors and self.quantile is not None:
            for j in range(len(net_plan)):
                errors = self.net_errors.get(str((hour + j) % 24))
                if errors and net_plan[j] > 0:
                    net_plan[j] = net_plan[j] + errors[self.quantile]
                    if not self.plan_surplus:
                        net_plan[j] = max(net_plan[j], 0.0)
        try:
            p = self.plan(soc, w, net_plan, cap, pmax)
        except Exception:
            p = self.backup_rule(w, net[0], pmax)

        # excedent solar: carregar de menys perd energia gratis, carregar de mes nomes compra una mica de
        # xarxa a l'hora mes barata. Per aixo carreguem pensant en el cas de mes excedent (mateix quantil).
        errors_now = self.net_errors.get(str(hour))
        if self.surplus_boost and errors_now and self.quantile is not None and p >= 0:
            p = max(p, -(net[0] + errors_now[self.surplus_q]))

        # no descarreguem mes del consum net que esperem ara, amb un marge per l'error de previsio:
        # de nit (sense sol) el consum es preveu molt millor que de dia
        if p < 0:
            errors = self.net_errors.get(str(hour))
            if errors and self.quantile is not None:
                # error que nomes se supera per sota en un tant per cent dels casos a aquesta hora
                limit = net[0] + errors[self.quantile]
            else:
                limit = net[0] * (self.safety_night if self.pv_now < 20.0 else self.safety)
            p = max(p, -max(limit, 0.0))
        max_c = max(0.0, min(pmax, (cap - soc) / ETA - 1e-4))
        max_d = max(0.0, min(pmax, soc * ETA - 1e-4))
        p = min(max(to_float(p, 0.0), -max_d), max_c)
        return float(p)
