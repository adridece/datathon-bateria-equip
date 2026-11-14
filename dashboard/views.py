"""Les pagines del dashboard. Cada pagina respon una pregunta: resposta, grafic i supòsits."""
import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from dashboard import analysis as an
from dashboard import style as s
from src.data import contiguous_blocks

HERE = Path(__file__).parent
WEEKDAYS = ["dl", "dt", "dc", "dj", "dv", "ds", "dg"]


# ---------------------------------------------------------------- dades en cache
@st.cache_data(show_spinner="Simulant...")
def sim(agent="mpc_lp", cap=2000.0, power=500.0):
    return an.run(agent, cap, power)


@st.cache_data
def weeks():
    blocks = [b for b in contiguous_blocks(an.valid_data()) if len(b) >= 24 * 5]
    return {f"Setmana del {b.index[0].day} {b.index[0].strftime('%b %Y')}": (b.index[0], b.index[-1]) for b in blocks}


def chart(c, height=None):
    if height:
        c = c.properties(height=height)
    st.altair_chart(c, use_container_width=True, theme=None)


def answer(text):
    st.html(f'<p class="answer">{text}</p>')


def note(text=s.SOURCE_NOTE):
    st.html(f'<p class="note">{text}</p>')


# ---------------------------------------------------------------- 1. resum
def summary():
    s.topbar("Tauler de decisions per a UPC Sostenible")
    d = sim()
    y = an.yearly(d)
    st_ = an.strategies()
    gap = 100 * st_.score.iloc[2] / st_.score.iloc[3]
    st.html(f'<p class="lead">Operar la bateria amb control predictiu evita <b>{s.num(y["co2_t_year"])} t de CO₂</b> '
            f'i <b>{s.eur(y["eur_year"])}</b> de factura l\'any, al <b>{s.num(gap)} %</b> del màxim teòric.</p>')

    c1, c2, c3 = st.columns([1.4, 1, 1])
    c1.html(f'<div class="kpi-main">{s.num(y["co2_t_year"])} t</div>'
            f'<div class="kpi-label">CO₂ evitat per any ({s.pct(y["co2_pct"])} de les emissions de la xarxa)</div>')
    c2.html(f'<div class="kpi">−{s.pct(y["cost_pct"])}</div><div class="kpi-label">factura elèctrica '
            f'({s.eur(y["eur_year"])}/any)</div>')
    c3.html(f'<div class="kpi">{s.num(y["score"], 2)}</div><div class="kpi-label">puntuació del repte '
            f'(òptim teòric {s.num(st_.score.iloc[3], 2)}) · {y["violations"]} infraccions</div>')
    st.html('<div style="height:28px"></div>')

    sz = an.sizing()
    row = sz[(sz.power_kw == 500) & (sz.capacity_kwh == 3000)].iloc[0]
    h = an.hourly_profile(d)
    charge_h = ", ".join(f"{x} h" for x in sorted(h.nlargest(3, "battery_kw").hour))
    dis_h = ", ".join(f"{x} h" for x in sorted(h.nsmallest(3, "battery_kw").hour))
    rob = an.robustness()
    rows = [
        ("Com s'ha de controlar la bateria?",
         f"Amb control predictiu i programació lineal: {s.num(st_.score.iloc[2], 2)} punts, igual que l'òptim. "
         f"Les regles fixes per hores en fan {s.num(st_.score.iloc[1], 2)}.", "estrategia"),
        ("Quan carrega i quan descarrega?",
         f"Carrega quan la xarxa és neta (sobretot {charge_h}) i descarrega quan és bruta i cara ({dis_h}).",
         "estrategia"),
        ("Quina bateria li convé a la UPC?",
         f"Amb l'inversor actual (500 kW), ampliar fins a 3.000 kWh portaria l'estalvi a "
         f"{s.num(row.co2_t_year)} t CO₂/any. Més de 4.000 kWh no compensa sense més potència.", "dimensionament"),
        ("Ens en podem refiar?",
         f"Sí. Amb un 50 % d'error a les previsions, la puntuació només baixa de {s.num(rob.score.iloc[0], 2)} "
         f"a {s.num(rob.score.iloc[-1], 2)} i no hi ha cap infracció.", "fiabilitat"),
    ]
    html = "".join(f'<div class="decision-row"><div class="q">{q}</div><div class="a">{a}</div></div>'
                   for q, a, _ in rows)
    st.html(html)
    note()


# ---------------------------------------------------------------- 2. operacio en directe
def live_payload(d: pd.DataFrame) -> str:
    w = (0.7 * d.co2_kg_per_kwh / 0.0921 + 0.3 * d.precio_eur_per_kwh / 0.1568).values
    why = []
    for k in range(len(d)):
        ahead = w[k:k + 24]
        rank = int((ahead < w[k]).sum()) + 1
        b, soc = d.bat_kw.iloc[k], d.soc_pct.iloc[k]
        if b > 1:
            why.append(f"Carrega {b:.0f} kW. És la {rank}a hora més neta de les properes {len(ahead)}.")
        elif b < -1:
            why.append(f"Descarrega {-b:.0f} kW. Hora bruta i cara: el campus compra {-b:.0f} kW menys a la xarxa.")
        elif soc > 0.99:
            why.append("Espera amb la bateria plena per a una hora més bruta.")
        elif soc < 0.01:
            why.append("Espera amb la bateria buida fins a la propera hora neta.")
        else:
            why.append("Espera. Moure energia ara perdria més (10 % per cicle) del que estalviaria.")
    payload = {
        "ts": [f"{WEEKDAYS[t.dayofweek]} {t.day:02d}/{t.month:02d} · {t.hour:02d}:00" for t in d.index],
        "hour": [int(t.hour) for t in d.index], "day": [t.day for t in d.index],
        "load": d.load_kw.round(1).tolist(), "pv": d.pv_kw.round(1).tolist(),
        "price": d.precio_eur_per_kwh.round(4).tolist(), "co2": d.co2_kg_per_kwh.round(4).tolist(),
        "bat": d.bat_kw.round(1).tolist(), "soc": d.soc_pct.round(4).tolist(),
        "grid": d.grid_kw.round(1).tolist(), "base": d.base_grid_kw.round(1).tolist(),
        "co2_saved": d.co2_estalviat_acum.round(1).tolist(), "eur_saved": d.eur_estalviat_acum.round(1).tolist(),
        "why": why, "pmax": 500, "cap": 2000,
        "colors": {"ink": s.INK, "muted": s.MUTED, "rule": s.RULE, "paper": s.PAPER, "surface": s.SURFACE,
                   "accent": s.ACCENT, "solar": s.SOLAR, "charge": s.CHARGE, "discharge": s.DISCHARGE,
                   "price": s.PRICE, "co2": s.CO2_RAMP},
    }
    return json.dumps(payload, ensure_ascii=False)


@st.cache_resource
def asset(name):
    return (HERE / name).read_text(encoding="utf-8")


def live():
    s.topbar("Operació hora a hora")
    names = list(weeks())
    c1, c2 = st.columns([3, 1])
    week = c1.selectbox("Període", names, index=0, label_visibility="collapsed")
    use_3d = c2.toggle("Vista 3D", value=(HERE / "scene3d.html").exists())
    start, end = weeks()[week]
    d = sim().loc[start:end]
    payload = live_payload(d)
    if use_3d and (HERE / "scene3d.html").exists():
        html = asset("scene3d.html")
        html = (html.replace("__THREE_B64__", asset_b64("vendor/three.module.min.js"))
                    .replace("__ORBIT_B64__", asset_b64("vendor/OrbitControls.js"))
                    .replace("__CAMPUS__", asset("static/campus_nord.json"))
                    .replace("__DATA__", payload))
        st.iframe(html, height=900)
    else:
        st.iframe(asset("live2d.html").replace("__DATA__", payload), height=760)
    note("Simulació amb el simulador oficial i dades reals del Campus Nord. El consum i la solar són mesures reals.")


@st.cache_resource
def asset_b64(name):
    import base64
    return base64.b64encode((HERE / name).read_bytes()).decode()


# ---------------------------------------------------------------- 3. estrategia
def strategy():
    s.topbar("Estratègia de control")
    st_ = an.strategies()
    st.markdown("### El control predictiu arriba al màxim teòric")
    answer(f"Planificar les properes 24 h amb programació lineal dona <b>{s.num(st_.score.iloc[2], 2)}</b> punts, "
           f"el mateix que un agent que conegués tot el futur ({s.num(st_.score.iloc[3], 2)}). Les regles fixes per "
           f"hores només en treuen {s.num(st_.score.iloc[1], 2)}.")
    data = st_.iloc[:3].copy()
    data["color"] = [s.REF, s.REF, s.ACCENT]
    bars = alt.Chart(data).mark_bar(height=26).encode(
        y=alt.Y("strategy:N", sort=None, title=None, axis=alt.Axis(labelFontSize=13, labelColor=s.INK)),
        x=alt.X("score:Q", title="Puntuació oficial", scale=alt.Scale(domain=[0, 7])),
        color=alt.Color("color:N", scale=None),
        tooltip=[alt.Tooltip("strategy:N", title="Estratègia"), alt.Tooltip("score:Q", title="Puntuació", format=".2f"),
                 alt.Tooltip("co2_pct:Q", title="CO₂ evitat (%)", format=".1f"),
                 alt.Tooltip("cost_pct:Q", title="Factura (%)", format=".1f")])
    labels = bars.mark_text(align="left", dx=6, font=s.MONO).encode(text=alt.Text("score:Q", format=".2f"),
                                                                  color=alt.value(s.INK))
    best = alt.Chart(pd.DataFrame({"x": [st_.score.iloc[3]], "t": ["òptim teòric"]}))
    rule = best.mark_rule(strokeDash=[4, 3], color=s.INK).encode(x="x:Q")
    rule_txt = best.mark_text(align="left", dx=4, dy=-60, color=s.INK, fontSize=11).encode(x="x:Q", text="t:N")
    chart(bars + labels + rule + rule_txt, 150)
    note()

    st.markdown("### Carrega quan la xarxa és neta, descarrega quan és bruta")
    d = sim()
    h = an.hourly_profile(d)
    answer("Cada barra és la potència mitjana de la bateria a aquella hora. Les hores de càrrega coincideixen amb el "
           "CO₂ mínim del migdia (molta solar a la xarxa peninsular) i les de descàrrega amb el pic del vespre.")
    base = alt.Chart(h).encode(x=alt.X("hour:O", title="Hora del dia", axis=alt.Axis(labelAngle=0)))
    p1 = base.mark_bar().encode(
        y=alt.Y("battery_kw:Q", title="Bateria (kW)"),
        color=alt.condition(alt.datum.battery_kw > 0, alt.value(s.CHARGE), alt.value(s.DISCHARGE)),
        tooltip=[alt.Tooltip("hour:O", title="Hora"), alt.Tooltip("battery_kw:Q", title="kW", format=".0f")]
    ).properties(height=150, title=alt.Title("Potència de la bateria", subtitle="+ càrrega · − descàrrega · mitjana per hora"))
    p2 = base.mark_line(point=True, color=s.CO2_RAMP[3]).encode(
        y=alt.Y("co2_g:Q", title="g CO₂/kWh", scale=alt.Scale(zero=False))).properties(
        height=110, title=alt.Title("Intensitat de CO₂ de la xarxa"))
    p3 = base.mark_line(point=True, color=s.PRICE).encode(
        y=alt.Y("price_eur_mwh:Q", title="€/MWh", scale=alt.Scale(zero=False))).properties(
        height=110, title=alt.Title("Preu PVPC"))
    chart(alt.vconcat(p1, p2, p3, spacing=18))
    note()

    st.markdown("### Què fa la bateria cada hora de cada dia")
    hm = d[["bat_kw"]].copy()
    hm["date"] = hm.index.strftime("%d/%m/%y")
    hm["order"] = range(len(hm))
    hm["hour"] = hm.index.hour
    answer("Cada fila és un dia de les 12 setmanes de validació. El patró és molt estable: blau al migdia i a la "
           "matinada (càrrega), vermelló al vespre (descàrrega).")
    heat = alt.Chart(hm).mark_rect().encode(
        x=alt.X("hour:O", title="Hora del dia", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("date:N", sort=alt.EncodingSortField("order"), title=None, axis=alt.Axis(labelFontSize=9)),
        color=alt.Color("bat_kw:Q", title="kW", scale=alt.Scale(domain=[-500, 0, 500],
                        range=[s.DISCHARGE, "#F2EFE8", s.CHARGE])),
        tooltip=[alt.Tooltip("date:N", title="Dia"), alt.Tooltip("hour:O", title="Hora"),
                 alt.Tooltip("bat_kw:Q", title="kW", format=".0f")])
    chart(heat, 1100)
    note()


# ---------------------------------------------------------------- 4. dimensionament
def sizing():
    s.topbar("Quina bateria li convé a la UPC")
    sz = an.sizing()
    c1, c2, c3 = st.columns(3)
    cap = c1.select_slider("Capacitat (kWh)", options=an.CAPACITIES, value=2000)
    power = c2.select_slider("Potència de l'inversor (kW)", options=an.POWERS, value=500)
    cost = c3.slider("Cost instal·lat (€/kWh)", 150, 600, 350, 25,
                     help="Hipòtesi. Canvieu-la segons el pressupost real.")
    sz = sz.assign(invest=sz.capacity_kwh * cost)
    sz["payback"] = sz.invest / sz.eur_year
    cur = sz[(sz.capacity_kwh == cap) & (sz.power_kw == power)].iloc[0]
    base = sz[(sz.capacity_kwh == 2000) & (sz.power_kw == 500)].iloc[0]

    ok = sz[(sz.power_kw == power) & (sz.payback < 10)]
    best = ok.loc[ok.co2_t_year.idxmax()] if len(ok) else None
    st.markdown("### Més capacitat només ajuda fins a unes 4 hores de potència")
    txt = (f"La configuració triada ({s.num(cap)} kWh, {s.num(power)} kW) evitaria <b>{s.num(cur.co2_t_year)} t de CO₂</b> "
           f"i {s.eur(cur.eur_year)} l'any ({'+' if cur.co2_t_year >= base.co2_t_year else '−'}"
           f"{s.num(abs(cur.co2_t_year - base.co2_t_year))} t respecte a la bateria actual), amb un retorn de "
           f"{s.num(cur.payback, 1)} anys.")
    if best is not None:
        txt += (f" Amb {s.num(power)} kW, l'opció que evita més CO₂ amb retorn de menys de 10 anys és "
                f"<b>{s.num(best.capacity_kwh)} kWh</b>.")
    answer(txt)

    sz["series"] = sz.power_kw.map(lambda p: f"{p} kW")
    sz["color"] = sz.power_kw.map(lambda p: s.ACCENT if p == power else s.REF)
    lines = alt.Chart(sz).mark_line(point=True).encode(
        x=alt.X("capacity_kwh:Q", title="Capacitat de la bateria (kWh)"),
        y=alt.Y("co2_t_year:Q", title="CO₂ evitat (t/any)"),
        detail="series:N", color=alt.Color("color:N", scale=None),
        tooltip=[alt.Tooltip("capacity_kwh:Q", title="kWh"), alt.Tooltip("power_kw:Q", title="kW"),
                 alt.Tooltip("co2_t_year:Q", title="t CO₂/any", format=".0f"),
                 alt.Tooltip("eur_year:Q", title="€/any", format=",.0f")])
    last = sz[sz.capacity_kwh == an.CAPACITIES[-1]]
    lab = alt.Chart(last).mark_text(align="left", dx=8).encode(
        x="capacity_kwh:Q", y="co2_t_year:Q", text="series:N", color=alt.Color("color:N", scale=None))
    point = alt.Chart(pd.DataFrame([cur])).mark_point(size=180, filled=False, strokeWidth=2, color=s.INK).encode(
        x="capacity_kwh:Q", y="co2_t_year:Q")
    chart((lines + lab + point).properties(title=alt.Title(
        "CO₂ evitat segons la mida", subtitle="Cada línia és una potència d'inversor; el cercle és l'opció triada")), 320)

    st.markdown("### Inversió i retorn")
    t = sz[sz.power_kw == power][["capacity_kwh", "co2_t_year", "eur_year", "invest", "payback"]].copy()
    t["eur_per_t"] = t.invest / (t.co2_t_year * 15)
    t.columns = ["Capacitat (kWh)", "CO₂ evitat (t/any)", "Estalvi (€/any)", "Inversió (€)", "Retorn (anys)",
                 "€ per t CO₂ (15 anys)"]

    def mark(row):
        return [f"background-color: #E3EEEA; font-weight: 600" if row["Capacitat (kWh)"] == cap else ""] * len(row)

    st.dataframe(t.style.apply(mark, axis=1).format({
        "Capacitat (kWh)": lambda v: s.num(v), "CO₂ evitat (t/any)": lambda v: s.num(v),
        "Estalvi (€/any)": lambda v: s.num(v), "Inversió (€)": lambda v: s.num(v),
        "Retorn (anys)": lambda v: s.num(v, 1), "€ per t CO₂ (15 anys)": lambda v: s.num(v)}),
        hide_index=True, use_container_width=True)
    note("Retorn = inversió / estalvi anual. Vida útil suposada: 15 anys. Sense degradació ni manteniment. " + s.SOURCE_NOTE)


# ---------------------------------------------------------------- 5. fiabilitat
def reliability():
    s.topbar("Fiabilitat i supòsits")
    r = an.robustness()
    st.markdown("### Aguanta previsions dolentes")
    answer(f"Afegint un 50 % d'error a les previsions de preu i CO₂, la puntuació baixa de "
           f"<b>{s.num(r.score.iloc[0], 2)}</b> a <b>{s.num(r.score.iloc[-1], 2)}</b>. Cada hora l'agent torna a "
           f"planificar amb la informació nova, i el límit de seguretat evita qualsevol infracció.")
    line = alt.Chart(r).mark_line(point=True, color=s.ACCENT).encode(
        x=alt.X("error_pct:Q", title="Error afegit a les previsions (%)"),
        y=alt.Y("score:Q", title="Puntuació", scale=alt.Scale(domain=[0, 7])),
        tooltip=[alt.Tooltip("error_pct:Q", title="Error (%)"), alt.Tooltip("score:Q", title="Puntuació", format=".2f")])
    txt = line.mark_text(dy=-12, font=s.MONO, color=s.INK).encode(text=alt.Text("score:Q", format=".2f"))
    chart(line + txt, 260)
    note("L'error creix amb l'horitzó, com en una previsió real (0 % a l'hora actual, màxim a 24 h). " + s.SOURCE_NOTE)

    st.markdown("### Funciona tot l'any")
    m = an.monthly(sim())
    answer(f"La bateria redueix el CO₂ totes les setmanes de validació, entre un {s.pct(m.co2_pct.min())} i un "
           f"{s.pct(m.co2_pct.max())}. No depèn de l'estació.")
    mm = m.melt(["month", "order"], ["co2_pct", "cost_pct"], var_name="kpi", value_name="pct")
    mm["kpi"] = mm.kpi.map({"co2_pct": "CO₂ evitat", "cost_pct": "Factura estalviada"})
    bars = alt.Chart(mm).mark_bar().encode(
        x=alt.X("month:N", sort=alt.EncodingSortField("order"), title=None, axis=alt.Axis(labelAngle=0)),
        xOffset=alt.XOffset("kpi:N", sort=["CO₂ evitat", "Factura estalviada"]),
        y=alt.Y("pct:Q", title="Estalvi (%)"),
        color=alt.Color("kpi:N", scale=alt.Scale(domain=["CO₂ evitat", "Factura estalviada"], range=[s.ACCENT, s.REF])),
        tooltip=[alt.Tooltip("month:N", title="Mes"), alt.Tooltip("kpi:N", title=" "),
                 alt.Tooltip("pct:Q", title="%", format=".1f")])
    chart(bars, 260)
    note()

    st.markdown("### Supòsits i límits")
    st.markdown("""
- **Previsions:** el preu i el CO₂ de les properes 24 h es coneixen (com al repte). El consum i la solar futurs no.
- **Anualització:** les xifres per any multipliquen les 12 setmanes de validació per 8.760 / 1.848 hores.
- **Bateria:** 90 % de rendiment, sense degradació (com el simulador oficial). A la realitat, menys cicles allargarien la vida útil.
- **Excedents:** l'energia abocada a la xarxa no es paga ni compta com a CO₂ evitat.
- **Inversió:** el cost per kWh és una hipòtesi editable; no inclou manteniment ni subvencions.
""")
