"""
Colors, formats i tema dels grafics. Tot el dashboard (Altair, CSS i l'escena 3D)
agafa els colors d'aqui, aixi un mateix concepte te sempre el mateix color.
"""
import altair as alt
import streamlit as st

# Base
PAPER = "#F6F4EF"
SURFACE = "#FFFFFF"
INK = "#1C1F22"
MUTED = "#6B6760"
RULE = "#DAD6CE"

# El nostre agent es l'unic color fort; la resta d'escenaris van en gris
ACCENT = "#0F5C4D"
REF = "#A9A49B"
REF_DARK = "#6B6760"

# Energia (Okabe-Ito, apte per a daltonisme)
SOLAR = "#E69F00"
CHARGE = "#0072B2"
DISCHARGE = "#D55E00"
PRICE = "#7A5195"

# CO2: de net (clar) a brut (fosc)
CO2_RAMP = ["#EFE9DD", "#D7C3A0", "#B58D5E", "#87603A", "#4E3524"]

FONT = "IBM Plex Sans, system-ui, sans-serif"
MONO = "IBM Plex Mono, ui-monospace, monospace"

SOURCE_NOTE = "Font: simulador oficial del repte, 12 setmanes de validació (1.848 h)."


@alt.theme.register("campus", enable=True)
def campus_theme():
    return alt.theme.ThemeConfig({"config": {
        "background": "transparent", "font": FONT,
        "view": {"stroke": None, "continuousHeight": 260},
        "title": {"font": FONT, "fontSize": 16, "fontWeight": 600, "color": INK, "anchor": "start",
                  "subtitleFont": FONT, "subtitleFontSize": 13, "subtitleColor": MUTED, "offset": 12},
        "axis": {"labelFont": FONT, "titleFont": FONT, "labelFontSize": 12, "titleFontSize": 12,
                 "labelColor": MUTED, "titleColor": MUTED, "titleFontWeight": 400,
                 "domainColor": RULE, "tickColor": RULE, "gridColor": RULE, "gridOpacity": 0.6,
                 "labelPadding": 6},
        "axisX": {"grid": False},
        "axisY": {"domain": False, "ticks": False},
        "legend": {"orient": "top", "labelFont": FONT, "titleFont": FONT, "labelColor": INK,
                   "titleColor": MUTED, "symbolType": "square", "title": None},
        "range": {"category": [ACCENT, REF, REF_DARK, CHARGE, DISCHARGE, SOLAR]},
        "line": {"strokeWidth": 2},
        "bar": {"cornerRadiusEnd": 2},
        "text": {"font": FONT, "fontSize": 12, "color": INK},
    }})


CSS = f"""<style>
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stDecoration"] {{ display: none; }}
.block-container {{ padding-top: 2.2rem; max-width: 1240px; }}
[data-testid="stMetricValue"] {{ font-family: {MONO}; font-variant-numeric: tabular-nums; }}
[data-testid="stCaptionContainer"] {{ color: {MUTED}; }}
footer {{ visibility: hidden; }}
.topbar {{ display: flex; justify-content: space-between; align-items: baseline;
          border-bottom: 1px solid {RULE}; padding-bottom: 10px; margin-bottom: 28px; }}
.topbar .name {{ font-weight: 600; letter-spacing: .01em; }}
.topbar .sub {{ color: {MUTED}; font-size: 14px; }}
.lead {{ font-size: 28px; line-height: 1.25; font-weight: 400; max-width: 30em; margin: 0 0 28px; }}
.lead b {{ font-weight: 600; color: {ACCENT}; }}
.kpi-main {{ font-family: {MONO}; font-size: 44px; line-height: 1.05; color: {ACCENT}; font-variant-numeric: tabular-nums; }}
.kpi {{ font-family: {MONO}; font-size: 26px; line-height: 1.1; font-variant-numeric: tabular-nums; }}
.kpi-label {{ color: {MUTED}; font-size: 13px; margin-top: 4px; }}
.answer {{ font-size: 18px; line-height: 1.45; margin: 4px 0 14px; max-width: 46em; }}
.answer b {{ font-weight: 600; }}
.question {{ font-size: 13px; text-transform: uppercase; letter-spacing: .08em; color: {MUTED}; margin-top: 8px; }}
.decision-row {{ display: grid; grid-template-columns: 220px 1fr; gap: 24px; padding: 18px 0;
                border-top: 1px solid {RULE}; }}
.decision-row .q {{ color: {MUTED}; font-size: 14px; }}
.decision-row .a {{ font-size: 17px; line-height: 1.45; }}
.note {{ color: {MUTED}; font-size: 13px; }}
</style>"""


def apply_style():
    st.html(CSS)


def topbar(subtitle: str):
    st.html(f'<div class="topbar"><span class="name">Bateria del Campus Nord</span>'
            f'<span class="sub">{subtitle}</span></div>')


# Formats en catala (punt de milers, coma decimal)
def num(x, decimals=0):
    s = f"{x:,.{decimals}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(x, decimals=1):
    return f"{num(x, decimals)} %"


def eur(x):
    return f"{num(x / 1000)} k€" if abs(x) >= 10000 else f"{num(x)} €"
