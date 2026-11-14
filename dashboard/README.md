# Dashboard

Tauler de decisions per a UPC Sostenible (side challenge de la Tukey Commission). És una web feta a mida:
el Campus Nord real en 3D a la portada i, a sota, les decisions amb els gràfics que les justifiquen.

```
python scripts/serve_dashboard.py
```
S'obre sol al navegador (http://localhost:8000). Funciona sense internet. Per parar-lo: `Ctrl + C`.

Si canvia l'agent o les dades, regenereu les xifres amb:
```
python scripts/build_dashboard_data.py
```

## Què hi ha
- **Portada (Directe):** campus real en 3D hora a hora. Fluxos d'energia, estat de la bateria, CO₂ i preu, estalvi acumulat,
  franja de la setmana (clic per moure's) i **presentació guiada** (botó o tecla P; fletxes per avançar, Esc per sortir).
- **01 Estratègia:** per què el control predictiu és el millor.
- **02 Quan carrega:** perfil horari i mapa de calor de cada hora de cada dia.
- **03 Mida:** quina bateria convé i retorn de la inversió (controls interactius).
- **04 Fiabilitat:** robustesa a errors de previsió i resultats per setmana.
- **05 Supòsits i límits.**

## Fitxers
- `index.html`, `css/style.css`: estructura i estil (sala de control fosca, IBM Plex).
- `js/scene.js`: escena 3D (three.js 0.170.0, a `vendor/`).
- `js/main.js`: reproducció, panells i presentació guiada.
- `js/charts.js`: gràfics de les decisions (D3 7.9, a `vendor/`).
- `data/`: dades generades per `scripts/build_dashboard_data.py` (no editar a mà).
- `analysis.py`: càlculs amb el simulador oficial (els fa servir el script de dades).
- `static/campus_nord.json`: edificis reals (© OpenStreetMap contributors, ODbL), de `scripts/build_campus_json.py`.
- `app.py`, `views.py`, `style.py`, `live2d.html`, `scene3d.html`: versió antiga amb Streamlit, ja no es fa servir (es pot esborrar).
