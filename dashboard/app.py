"""
Dashboard del nostre agent de bateria.
Executar des de l'arrel del projecte:
    streamlit run dashboard/app.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data import load_hourly, contiguous_blocks  # noqa: E402
from src.evaluate import valid_split  # noqa: E402
from src.replay import make_agent, replay  # noqa: E402

st.set_page_config(page_title="Bateria del Campus", page_icon="🔋", layout="wide")

AGENTS = {"El nostre agent (MPC + LP)": "mpc_lp", "Plantilla oficial": "plantilla",
          "Sense bateria": "sense_bateria"}
CO2_REF, PREU_REF = 0.0921, 0.1568
DIES = ["dl", "dt", "dc", "dj", "dv", "ds", "dg"]


# ------------------------------------------------------------------ dades
@st.cache_data
def periodes():
    df = load_hourly()
    out = {"Totes les setmanes de validació (12 setm.)": valid_split(df)}
    for b in contiguous_blocks(valid_split(df)):
        if len(b) >= 24 * 5:
            out[f"Setmana del {b.index[0]:%d/%m/%Y}"] = b
    return out


@st.cache_data
def simula(periode: str, agent: str, cap=2000.0, pmax=500.0, w_co2=0.7):
    return replay(make_agent(agent, cap, pmax, w_co2), periodes()[periode], cap, pmax)


def explicacio(d: pd.DataFrame) -> list:
    """Frase curta que explica la decisio de cada hora."""
    w = (0.7 * d.co2_kg_per_kwh / CO2_REF + 0.3 * d.precio_eur_per_kwh / PREU_REF).values
    out = []
    for k in range(len(d)):
        fin = w[k:k + 24]
        pos = int((fin < w[k]).sum()) + 1
        b, soc = d.bat_kw.iloc[k], d.soc_pct.iloc[k]
        if b > 1:
            out.append(f"⚡ <b>Carrega</b>: ara l'electricitat és de les més <b>netes i barates</b> de les properes "
                       f"24 h (posició {pos} de {len(fin)}). La guardem per a les hores brutes.")
        elif b < -1:
            out.append(f"🔋 <b>Descarrega</b>: aquesta hora és de les més <b>contaminants i cares</b> "
                       f"(posició {pos} de {len(fin)}). El campus compra {abs(b):.0f} kW menys a la xarxa.")
        elif soc > 0.99:
            out.append("🔋 <b>Espera plena</b>: la bateria ja és plena i guarda l'energia per a una hora pitjor.")
        elif soc < 0.01:
            out.append("😴 <b>Espera buida</b>: ja ho ha descarregat tot a les hores dolentes; carregarà a la propera hora neta.")
        else:
            out.append("😴 <b>Espera</b>: no compensa moure energia ara (es perd un 10 % en cada cicle); "
                       "espera una hora més extrema.")
    return out


def dades_animacio(d: pd.DataFrame, pmax: float) -> str:
    j = {
        "ts": [f"{t:%d/%m %H}:00 ({DIES[t.dayofweek]})" for t in d.index],
        "h": [int(t.hour) for t in d.index],
        "load": d.load_kw.round(1).tolist(), "pv": d.pv_kw.round(1).tolist(),
        "preu": d.precio_eur_per_kwh.round(4).tolist(), "co2": d.co2_kg_per_kwh.round(4).tolist(),
        "bat": d.bat_kw.round(1).tolist(), "soc": d.soc_pct.round(4).tolist(),
        "grid": d.grid_kw.round(1).tolist(),
        "sco2": d.co2_estalviat_acum.round(1).tolist(), "seur": d.eur_estalviat_acum.round(1).tolist(),
        "why": explicacio(d), "pmax": pmax,
    }
    return json.dumps(j, ensure_ascii=False)


# ------------------------------------------------------------------ interficie
st.title("🔋 Bateria del Campus Nord — en temps real")
st.caption("Simulació hora a hora amb el simulador oficial del repte i dades reals del campus.")

with st.sidebar:
    st.header("Configuració")
    per = st.selectbox("Període", list(periodes().keys()), index=1)
    nom_agent = st.selectbox("Agent", list(AGENTS.keys()))

tab1, tab2, tab3, tab4 = st.tabs(["🔴 En directe", "📊 Comparativa", "🧪 Què passaria si...", "ℹ️ Com funciona"])

with tab1:
    d = simula(per, AGENTS[nom_agent])
    r = d.attrs["resultat"]
    c = st.columns(4)
    c[0].metric("Puntuació", f"{r['score']:.2f}")
    c[1].metric("CO₂ estalviat", f"{r['co2_estalviat_pct']:.2f} %", f"{r['co2_estalviat_kg']:,.0f} kg")
    c[2].metric("Factura estalviada", f"{r['cost_estalviat_pct']:.2f} %", f"{r['cost_estalviat_eur']:,.0f} €")
    c[3].metric("Infraccions", r["infraccions"])
    html = (Path(__file__).parent / "animacio.html").read_text(encoding="utf-8")
    components.html(html.replace("__DADES__", dades_animacio(d, 500.0)), height=900, scrolling=False)

with tab2:
    st.subheader("Els tres escenaris sobre el mateix període")
    files, acum = [], {}
    for nom, ag in AGENTS.items():
        dd = simula(per, ag)
        rr = dd.attrs["resultat"]
        files.append({"Escenari": nom, "Puntuació": rr["score"], "CO₂ estalviat (%)": rr["co2_estalviat_pct"],
                      "Cost estalviat (%)": rr["cost_estalviat_pct"], "CO₂ estalviat (kg)": rr["co2_estalviat_kg"],
                      "Diners estalviats (€)": rr["cost_estalviat_eur"], "Infraccions": rr["infraccions"]})
        acum[nom] = dd.co2_estalviat_acum.values
    st.dataframe(pd.DataFrame(files).set_index("Escenari"), use_container_width=True)
    st.markdown("**CO₂ estalviat acumulat (kg)** al llarg del període")
    st.line_chart(pd.DataFrame(acum))
    st.markdown("**Quan carrega i quan descarrega** el nostre agent (mitjana per hora del dia, kW)")
    dd = simula(per, "mpc_lp")
    perfil = dd.groupby(dd.index.hour)[["bat_kw"]].mean().rename(columns={"bat_kw": "bateria (kW)"})
    perfil["CO₂ (g/kWh)"] = dd.groupby(dd.index.hour).co2_kg_per_kwh.mean() * 1000
    perfil["preu (€/MWh)"] = dd.groupby(dd.index.hour).precio_eur_per_kwh.mean() * 1000
    st.bar_chart(perfil[["bateria (kW)"]])
    st.line_chart(perfil[["CO₂ (g/kWh)", "preu (€/MWh)"]])

with tab3:
    st.subheader("Què passaria si la UPC instal·lés una bateria diferent?")
    st.caption("Mateix agent (MPC + LP), canviant la mida de la bateria i la importància del CO₂.")
    a, b, c3 = st.columns(3)
    cap = a.slider("Capacitat (kWh)", 500, 8000, 2000, 500)
    pmax = b.slider("Potència màxima (kW)", 100, 2000, 500, 100)
    wc = c3.slider("Pes del CO₂ (la resta és cost)", 0.0, 1.0, 0.7, 0.1)
    base = simula(per, "mpc_lp").attrs["resultat"]
    nou = simula(per, "mpc_lp", float(cap), float(pmax), float(wc)).attrs["resultat"]
    m = st.columns(3)
    m[0].metric("Puntuació", f"{nou['score']:.2f}", f"{nou['score'] - base['score']:+.2f}")
    m[1].metric("CO₂ estalviat", f"{nou['co2_estalviat_pct']:.2f} %", f"{nou['co2_estalviat_pct'] - base['co2_estalviat_pct']:+.2f} pp")
    m[2].metric("Cost estalviat", f"{nou['cost_estalviat_pct']:.2f} %", f"{nou['cost_estalviat_pct'] - base['cost_estalviat_pct']:+.2f} pp")
    if st.checkbox("Mostrar la corba completa (tarda uns segons)"):
        caps = [500, 1000, 2000, 4000, 8000]
        sc = {f"{p} kW": [simula(per, "mpc_lp", float(cp), float(p)).attrs["resultat"]["co2_estalviat_pct"] for cp in caps]
              for p in (250, 500, 1000)}
        st.markdown("**CO₂ estalviat (%) segons la capacitat (kWh)**")
        st.line_chart(pd.DataFrame(sc, index=caps))

with tab4:
    st.markdown("""
### Com pren les decisions el nostre agent
1. **Sabem el futur del preu i del CO₂.** Cada hora la web ens dona els valors exactes de les properes 24 h.
2. **El campus sempre consumeix més del que descarreguem** (≥ 500 kW el 99,5 % de les hores), així que
   cada kWh que traiem de la bateria és un kWh que no comprem a la xarxa.
3. Això ens permet donar un **"preu" a cada hora**: `0,7·CO₂/CO₂ mitjà + 0,3·preu/preu mitjà`.
4. Cada hora resolem un **problema de programació lineal**: quina és la millor manera de carregar i descarregar
   les properes 24 h respectant la bateria (2.000 kWh, ±500 kW, 90 % de rendiment)?
5. Fem **només la primera hora** del pla i tornem a planificar a l'hora següent (*control predictiu, MPC*).

**Resultat:** obtenim el mateix que un "oracle" que coneix tot el futur → la nostra estratègia és pràcticament **òptima**.
""")
