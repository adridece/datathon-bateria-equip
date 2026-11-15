"""
Descarrega dades publiques de REE d'ABANS del periode del repte (mai cap dia de test) per entrenar les previsions:
  - PVPC hora a hora (apidatos.ree.es): els mateixos valors que data/raw/train/precio_pvpc.csv.
  - Generacio per tecnologia cada 5 minuts (demanda.ree.es) i, amb ella, el CO2 de la xarxa calibrat amb dies del train.
Els organitzadors ens han confirmat que es poden fer servir dades publiques d'altres periodes.

    python scripts/download_ree.py        (tarda uns 20 minuts)
"""
import json
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import nnls

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "external"
END = "2025-08-31"            # l'ultim dia abans del repte (el train comenca l'1/9/2025)
TECH = ["eol", "nuc", "gf", "car", "cc", "hid", "sol", "solFot", "solTer", "bio", "cogenResto", "aut", "turb", "vap",
        "gnhd", "die", "icb", "inter", "conb", "bat"]


def get_json(url):
    for _ in range(4):
        try:
            raw = urllib.request.urlopen(url, timeout=60).read().decode()
            return json.loads(raw[raw.index("(") + 1:raw.rindex(")")] if raw.startswith("x(") else raw)
        except Exception:
            time.sleep(3)
    return None


def pvpc(start, end):
    rows = []
    for month in pd.date_range(start, end, freq="MS"):
        stop = (month + pd.offsets.MonthEnd(1)).strftime("%Y-%m-%dT23:59")
        j = get_json(f"https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real"
                     f"?start_date={month:%Y-%m-%dT00:00}&end_date={stop}&time_trunc=hour") or {}
        for inc in j.get("included", []):
            if inc["attributes"]["title"] == "PVPC":
                v = pd.DataFrame(inc["attributes"]["values"])
                v["Fecha"] = pd.to_datetime(v.datetime, utc=True).dt.tz_convert("Europe/Madrid").dt.tz_localize(None)
                v["precio_eur_per_kwh"] = v.value / 1000
                rows.append(v[["Fecha", "precio_eur_per_kwh"]])
    p = pd.concat(rows).drop_duplicates("Fecha").sort_values("Fecha")
    return p[p.Fecha <= f"{end} 23:00"]


def generation_day(day):
    j = get_json("https://demanda.ree.es/WSvisionaMovilesPeninsulaRest/resources/demandaGeneracionPeninsula"
                 f"?callback=x&curva=DEMANDAAU&fecha={day}")
    return pd.DataFrame(j["valoresHorariosGeneracion"]) if j else None


def generation(days):
    with ThreadPoolExecutor(6) as ex:
        parts = [p for p in ex.map(generation_day, days) if p is not None]
    df = pd.concat(parts).drop_duplicates("ts")
    df["ts"] = pd.to_datetime(df.ts, format="%Y-%m-%d %H:%M", errors="coerce")   # les hores 2A/2B del canvi d'hora fora
    df = df.dropna(subset=["ts"]).set_index("ts").sort_index()
    return df.clip(lower=0).resample("1h", label="left", closed="left").mean().dropna(how="all").fillna(0)


def calibrate(gen_train):
    """Quant compta cada tecnologia com a generacio amb i sense emissions perque surti el nostre CO2.
    Es calibra amb la meitat dels dies del train i es comprova amb l'altra meitat."""
    ref = pd.read_csv(ROOT / "data" / "raw" / "train" / "co2_red.csv", parse_dates=["Fecha"]).set_index("Fecha")
    both = gen_train.join(ref, how="inner").dropna(subset=["co2_kg_per_kwh"])
    tech = [c for c in TECH if c in gen_train.columns]
    days = both.index.normalize().unique()
    fit, check = both[both.index.normalize().isin(days[::2])], both[both.index.normalize().isin(days[1::2])]
    w_e, _ = nnls(fit[tech].values, fit.gen_con_emisiones_mw.values)
    w_s, _ = nnls(fit[tech].values, fit.gen_sin_emisiones_mw.values)
    if "car" in tech:
        w_e[tech.index("car")] = 1.0     # el 2025 gairebe no hi ha carbo: amb la formula oficial compta com el gas
    co2 = lambda g: 0.37 * (g[tech].values @ w_e) / (g[tech].values @ w_e + g[tech].values @ w_s)
    err = np.abs(co2(check) - check.co2_kg_per_kwh.values) / check.co2_kg_per_kwh.values
    print(f"CO2 calibrat: error relatiu als dies del train no usats {100 * err.mean():.2f} %")
    return co2


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pvpc("2024-01-01", END).to_csv(OUT / "pvpc_2024_2025.csv", index=False)
    pvpc("2021-06-01", "2023-12-31").to_csv(OUT / "pvpc_2021_2023.csv", index=False)   # nomes per les variables del CO2
    train_days = pd.read_csv(ROOT / "data" / "raw" / "train" / "co2_red.csv", parse_dates=["Fecha"]).Fecha.dt.normalize().unique()
    co2 = calibrate(generation([pd.Timestamp(d).strftime("%Y-%m-%d") for d in train_days[::4]]))
    gen = generation([d.strftime("%Y-%m-%d") for d in pd.date_range("2019-01-01", END)])
    out = pd.Series(co2(gen), index=gen.index, name="co2_kg_per_kwh").rename_axis("Fecha")
    out[out.index <= f"{END} 23:00"].to_csv(OUT / "co2_ree_2019_2025.csv")
    print("Escrit a", OUT)


if __name__ == "__main__":
    sys.exit(main())
