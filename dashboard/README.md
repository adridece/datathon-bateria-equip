# Dashboard

Simulació en temps real del nostre agent, comparativa i "què passaria si".

```
streamlit run dashboard/app.py
```
S'obre sol al navegador (http://localhost:8501). Per parar-lo: `Ctrl + C` a la terminal.

- `app.py` – l'aplicació (Streamlit).
- `animacio.html` – l'animació del campus (SVG + JavaScript, funciona sense internet).
- Les dades surten de `src/replay.py`, que fa servir el simulador oficial.
