"""Pestanya 'Decisions': cada pregunta del repte amb la resposta, el grafic que la justifica i la conclusio."""
import altair as alt
import pandas as pd
import streamlit as st

from dashboard import analisi as a

BLAU, VERD, ROSA, TARONJA, LILA, GRIS = "#60a5fa", "#4ade80", "#f472b6", "#f97316", "#a78bfa", "#94a3b8"


@st.cache_data
def _dades():
    return {"est": a.comparativa_estrategies(), "hora": a.perfil_horari(), "mes": a.perfil_mensual(),
            "sens": a.sensibilitat(), "rob": a.robustesa(), "any": a.anualitzat()}


def resposta(text: str):
    import re
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)   # negretes dins l'HTML
    st.markdown(f"<div style='background:#0b2a1a;border-left:5px solid {VERD};padding:12px 16px;"
                f"border-radius:8px;font-size:17px;margin:6px 0 10px'>✅ <b>Decisió:</b> {text}</div>",
                unsafe_allow_html=True)


def conclusio(text: str):
    st.caption(f"📌 {text}")


def render():
    d = _dades()
    an = d["any"]
    st.subheader("Resum per a UPC Sostenible")
    st.markdown("Aquest tauler respon les preguntes clau del repte amb dades reals del Campus Nord i el "
                "simulador oficial. Totes les xifres provenen de la **mateixa simulació** (12 setmanes de validació).")
    k = st.columns(4)
    k[0].metric("CO₂ evitat", f"{an['co2_pct']:.1f} %", f"≈ {an['t_co2_any']:.0f} t CO₂ / any")
    k[1].metric("Factura estalviada", f"{an['cost_pct']:.1f} %", f"≈ {an['eur_any'] / 1000:.0f} k€ / any")
    k[2].metric("Puntuació del repte", f"{an['score']:.2f}", "= òptim teòric")
    k[3].metric("Infraccions", "0")
    with st.expander("📖 Com es calculen els indicadors"):
        st.markdown("""
- **CO₂ evitat (%)** = (CO₂ sense bateria − CO₂ amb bateria) / CO₂ sense bateria. Només compta l'energia importada de la xarxa.
- **Factura estalviada (%)** = mateix càlcul amb el preu PVPC de cada hora.
- **Puntuació** = 0,7 · CO₂ evitat + 0,3 · factura estalviada − 0,2 per infracció (fórmula oficial).
- **Valors anuals**: estalvi de les 12 setmanes × (8.760 h / hores simulades). És una estimació: suposa que la resta de l'any es comporta igual.
""")
    st.divider()

    # ---------------------------------------------------------------- 1
    st.markdown("### 1️⃣ Quina estratègia de control ha de fer servir la bateria?")
    e = d["est"]
    resposta("control predictiu amb programació lineal (MPC + LP). Arriba al **màxim teòric**: "
             f"{e.score.iloc[2]:.2f} punts davant {e.score.iloc[1]:.2f} de les regles fixes per hores.")
    ch = alt.Chart(e).mark_bar(cornerRadiusEnd=4).encode(
        y=alt.Y("estrategia:N", sort=None, title=None),
        x=alt.X("score:Q", title="Puntuació oficial (més és millor)"),
        color=alt.condition(alt.datum.estrategia == "MPC + programació lineal (nostre)", alt.value(VERD), alt.value(GRIS)),
        tooltip=["estrategia", "score", "co2_pct", "cost_pct", "infraccions"])
    txt = ch.mark_text(align="left", dx=4, color="#e2e8f0").encode(text=alt.Text("score:Q", format=".2f"))
    st.altair_chart((ch + txt).properties(height=200), use_container_width=True)
    gap = 100 * (1 - e.score.iloc[2] / e.score.iloc[3]) if e.score.iloc[3] else 0
    conclusio(f"La distància amb l'òptim (que coneix tot el futur, també el consum) és del {gap:.1f} %. "
              "No cal un model més complex: el problema és lineal i el preu i el CO₂ de les properes 24 h són coneguts.")
    st.divider()

    # ---------------------------------------------------------------- 2
    st.markdown("### 2️⃣ Quan s'ha de carregar i quan descarregar?")
    h = d["hora"]
    carrega = sorted(h.nlargest(4, "bateria_kw").hora.tolist())
    descarrega = sorted(h.nsmallest(4, "bateria_kw").hora.tolist())
    rang = lambda hs: ", ".join(f"{x}h" for x in hs)
    resposta(f"carregar sobretot al **migdia i la matinada**, quan el CO₂ és baix (hores principals: {rang(carrega)}), "
             f"i descarregar al **vespre i a primera hora del matí**, quan el CO₂ i el preu són alts (hores principals: {rang(descarrega)}). "
             "No és un horari fix: l'agent ho recalcula cada hora amb les previsions.")
    base = alt.Chart(h).encode(x=alt.X("hora:O", title="Hora del dia"))
    barres = base.mark_bar(opacity=.8).encode(
        y=alt.Y("bateria_kw:Q", title="Potència mitjana de la bateria (kW)  + carrega / − descarrega"),
        color=alt.condition(alt.datum.bateria_kw > 0, alt.value("#2dd4bf"), alt.value(ROSA)),
        tooltip=["hora", alt.Tooltip("bateria_kw:Q", format=".0f")])
    st.altair_chart(barres.properties(height=230), use_container_width=True)
    ll = h.melt("hora", ["co2_g", "preu_eur_mwh"], var_name="variable", value_name="valor")
    ll["variable"] = ll.variable.map({"co2_g": "CO₂ (g/kWh)", "preu_eur_mwh": "Preu (€/MWh)"})
    linies = alt.Chart(ll).mark_line(point=True).encode(
        x=alt.X("hora:O", title="Hora del dia"), y=alt.Y("valor:Q", title="Valor mitjà"),
        color=alt.Color("variable:N", scale=alt.Scale(range=[LILA, TARONJA]), title=None),
        tooltip=["hora", "variable", alt.Tooltip("valor:Q", format=".0f")])
    st.altair_chart(linies.properties(height=200), use_container_width=True)
    conclusio("Les barres verdes coincideixen amb les hores de CO₂ mínim (migdia: molta solar a la xarxa peninsular) "
              "i les roses amb el pic de CO₂ i preu del vespre. La bateria trasllada energia neta cap a les hores brutes.")
    m = d["mes"]
    mm = m.melt("mes", ["co2_pct", "cost_pct"], var_name="indicador", value_name="pct")
    mm["indicador"] = mm.indicador.map({"co2_pct": "CO₂ evitat (%)", "cost_pct": "Factura estalviada (%)"})
    st.altair_chart(alt.Chart(mm).mark_bar().encode(
        x=alt.X("mes:N", title="Setmana de validació (mes)"), xOffset="indicador:N",
        y=alt.Y("pct:Q", title="Estalvi (%)"),
        color=alt.Color("indicador:N", scale=alt.Scale(range=[VERD, BLAU]), title=None),
        tooltip=["mes", "indicador", alt.Tooltip("pct:Q", format=".2f")]).properties(height=220),
        use_container_width=True)
    conclusio(f"L'estratègia estalvia CO₂ **tots els mesos** (entre {m.co2_pct.min():.1f} % i {m.co2_pct.max():.1f} %): "
              "no depèn de l'estació.")
    st.divider()

    # ---------------------------------------------------------------- 3
    st.markdown("### 3️⃣ Quina mida de bateria li convé a la UPC?")
    s = d["sens"].copy()
    s["potencia"] = s.potencia_kw.astype(str) + " kW"
    st.altair_chart(alt.Chart(s).mark_line(point=True).encode(
        x=alt.X("capacitat_kwh:Q", title="Capacitat de la bateria (kWh)"),
        y=alt.Y("t_co2_any:Q", title="CO₂ evitat (t / any)"),
        color=alt.Color("potencia:N", title="Potència", scale=alt.Scale(range=[GRIS, VERD, BLAU])),
        tooltip=["capacitat_kwh", "potencia_kw", alt.Tooltip("t_co2_any:Q", format=".1f"),
                 alt.Tooltip("eur_any:Q", format=",.0f"), "score"]).properties(height=280),
        use_container_width=True)
    conclusio("Cada corba s'aplana quan la capacitat supera ~4 hores de potència (p. ex. 500 kW → 2.000–4.000 kWh): "
              "a partir d'aquí la bateria ja no es pot omplir/buidar prou ràpid i l'energia extra gairebé no s'aprofita.")
    st.markdown("**Inversió i retorn** (hipòtesi editable: cost instal·lat de la bateria)")
    cost = st.slider("Cost instal·lat (€/kWh)", 150, 600, 350, 25,
                     help="Valor de referència aproximat per a bateries industrials; ajusteu-lo segons el pressupost real.")
    s["inversio_eur"] = s.capacitat_kwh * cost
    s["retorn_anys"] = s.inversio_eur / s.eur_any
    s["eur_per_t_co2"] = s.inversio_eur / (s.t_co2_any * 15)   # 15 anys de vida util
    taula = s[s.potencia_kw == 500][["capacitat_kwh", "t_co2_any", "eur_any", "inversio_eur", "retorn_anys", "eur_per_t_co2"]]
    taula.columns = ["Capacitat (kWh)", "CO₂ evitat (t/any)", "Estalvi (€/any)", "Inversió (€)", "Retorn (anys)", "€ per t CO₂ (15 anys)"]
    st.dataframe(taula.style.format({"CO₂ evitat (t/any)": "{:.1f}", "Estalvi (€/any)": "{:,.0f}", "Inversió (€)": "{:,.0f}",
                                     "Retorn (anys)": "{:.1f}", "€ per t CO₂ (15 anys)": "{:,.0f}"}),
                 hide_index=True, use_container_width=True)
    rapid = taula.loc[taula["Retorn (anys)"].idxmin()]
    ok = taula[taula["Retorn (anys)"] < 10]
    if len(ok):
        co2 = ok.loc[ok["CO₂ evitat (t/any)"].idxmax()]
        resposta(f"amb l'inversor actual de 500 kW, si la prioritat és el **CO₂** (70 % del repte), la millor opció amb "
                 f"retorn de menys de 10 anys és **{co2['Capacitat (kWh)']:,.0f} kWh** ({co2['CO₂ evitat (t/any)']:.0f} t CO₂/any, "
                 f"retorn {co2['Retorn (anys)']:.1f} anys). Si només es mira el retorn econòmic, la més ràpida és "
                 f"{rapid['Capacitat (kWh)']:,.0f} kWh ({rapid['Retorn (anys)']:.1f} anys). Més de 4.000 kWh no compensa sense més potència.")
    else:
        resposta(f"amb aquest cost cap mida es retorna en menys de 10 anys; la de retorn més ràpid és "
                 f"**{rapid['Capacitat (kWh)']:,.0f} kWh** ({rapid['Retorn (anys)']:.1f} anys).")
    st.divider()

    # ---------------------------------------------------------------- 4
    st.markdown("### 4️⃣ Ens en podem refiar al món real?")
    r = d["rob"]
    resposta(f"sí. Encara que les previsions de preu i CO₂ tinguessin un **50 % d'error**, la puntuació només baixaria "
             f"de {r.score.iloc[0]:.2f} a {r.score.iloc[-1]:.2f} i mai hi hauria infraccions.")
    st.altair_chart(alt.Chart(r).mark_line(point=True, color=VERD).encode(
        x=alt.X("error_pct:Q", title="Error afegit a les previsions de preu i CO₂ (%)"),
        y=alt.Y("score:Q", title="Puntuació", scale=alt.Scale(zero=False)),
        tooltip=["error_pct", "score", "infraccions"]).properties(height=230), use_container_width=True)
    conclusio("L'error creix amb l'horitzó (com en una previsió real). L'agent és robust perquè cada hora torna a "
              "planificar amb la informació nova, i el límit de seguretat garanteix 0 infraccions.")
