"""
Carrega i neteja de les dades del campus.

Fem exactament el mateix que el tutorial oficial (starter_kit/tutorial.ipynb) per
construir la taula horaria, perque el simulador de la web segurament fa servir aquest
mateix pipeline per al test. Si canviem alguna cosa aqui, el nostre "local score"
deixaria de ser comparable amb el del leaderboard.

Us:
    from src.data import load_hourly
    df = load_hourly()          # DataFrame horari amb load_kw, pv_kw, preu, co2
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "train"
PROCESSED = ROOT / "data" / "processed"

COL_CONTADOR = "Contador - POTENCIA ACTIVA EXPORTADA (kW)"


def _read(name: str) -> pd.DataFrame:
    return pd.read_csv(RAW / name, parse_dates=["Fecha"], low_memory=False).set_index("Fecha")


def build_hourly(extra_meteo: bool = True) -> pd.DataFrame:
    """Construeix la taula horaria oficial (+ variables meteo opcionals)."""
    cont = _read("contador.csv")
    load = (-cont[COL_CONTADOR]).clip(lower=0, upper=5000).resample("1h").mean().dropna()

    inv = _read("inversor.csv")
    cols = []
    for i in (1, 2, 3):
        c = [c for c in inv.columns
             if f"INVERSOR {i}" in c.upper() and "POTENCIA ACTIVA" in c.upper() and "FASE" not in c.upper()]
        cols.append(c[0])
    pv = sum(inv[c].fillna(0) for c in cols).clip(lower=0).resample("1h").mean().dropna()

    pvpc = pd.read_csv(RAW / "precio_pvpc.csv", parse_dates=["Fecha"]).set_index("Fecha")
    co2 = pd.read_csv(RAW / "co2_red.csv", parse_dates=["Fecha"]).set_index("Fecha")

    df = pd.DataFrame({
        "load_kw": load,
        "pv_kw": pv,
        "precio_eur_per_kwh": pvpc["precio_eur_per_kwh"],
        "co2_kg_per_kwh": co2["co2_kg_per_kwh"],
    }).dropna()

    if extra_meteo:
        met = _read("meteo.csv")
        irr = [c for c in met.columns if c.endswith("IRRADIANCIA (W/m2)")]
        tamb = [c for c in met.columns if "TEMPERATURA AMBIENTE" in c]
        tpanel = [c for c in met.columns if "TEMPERATURA PANEL" in c]
        wind = [c for c in met.columns if "VELOCIDAD VIENTO" in c]
        m = pd.DataFrame({
            "irr_wm2": met[irr[0]] if irr else np.nan,
            "temp_c": met[tamb[0]] if tamb else np.nan,
            "panel_c": met[tpanel[0]] if tpanel else np.nan,
            "wind_ms": met[wind[0]] if wind else np.nan,
        }).resample("1h").mean()
        df = df.join(m, how="left")
    df.index.name = "Fecha"
    return df


def load_hourly(force: bool = False) -> pd.DataFrame:
    """Llegeix la taula horaria de cache (data/processed) o la construeix."""
    PROCESSED.mkdir(parents=True, exist_ok=True)
    f = PROCESSED / "hourly.csv"
    if f.exists() and not force:
        return pd.read_csv(f, parse_dates=["Fecha"]).set_index("Fecha")
    df = build_hourly()
    df.to_csv(f)
    return df


def contiguous_blocks(df: pd.DataFrame, max_gap_h: int = 2) -> list:
    """Retorna una llista de trossos continus (els 'forats' son les setmanes de test)."""
    gaps = df.index.to_series().diff() > pd.Timedelta(hours=max_gap_h)
    block_id = gaps.cumsum()
    return [g for _, g in df.groupby(block_id)]


if __name__ == "__main__":
    d = load_hourly(force=True)
    print(d.shape, d.index.min(), d.index.max())
    print(d.describe().T)
