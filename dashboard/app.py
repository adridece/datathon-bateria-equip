"""
Tauler de decisions de la bateria del Campus Nord.
Executar des de l'arrel del projecte:
    streamlit run dashboard/app.py
"""
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dashboard import style, views  # noqa: E402

st.set_page_config(page_title="Bateria del Campus Nord", page_icon=str(ROOT / "dashboard/static/icon.svg"),
                   layout="wide", initial_sidebar_state="collapsed")
style.apply_style()

pages = [
    st.Page(views.summary, title="Resum", url_path="resum", default=True),
    st.Page(views.live, title="Operació en directe", url_path="directe"),
    st.Page(views.strategy, title="Estratègia", url_path="estrategia"),
    st.Page(views.sizing, title="Dimensionament", url_path="dimensionament"),
    st.Page(views.reliability, title="Fiabilitat", url_path="fiabilitat"),
]
st.navigation(pages, position="top").run()
