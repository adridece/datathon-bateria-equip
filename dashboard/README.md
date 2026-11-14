# Dashboard

Tauler de decisions per a UPC Sostenible (side challenge de la Tukey Commission). És una app d'una sola pantalla,
feta a mida: tema clar, targetes rodones, barra lateral amb 5 vistes i el Campus Nord real en 3D.

```
python scripts/serve_dashboard.py
```
S'obre sol al navegador (http://localhost:8000). Funciona sense internet. Per parar-lo: `Ctrl + C`.

Si canvia l'agent o les dades, regenereu les xifres amb:
```
python scripts/build_dashboard_data.py
```

## Què hi ha
- **Visió general:** xifres clau (CO₂ i € per any, puntuació oficial, infraccions), el campus en 3D, l'estat de la bateria
  i el "per què" de cada decisió, i dos gràfics resum.
- **Campus en directe:** el 3D a pantalla gran, franja de la setmana (clic per moure's) i **presentació guiada**
  (botó o tecla P; fletxes per avançar, Esc per sortir).
- **Estratègia:** comparació d'estratègies, què fa a cada hora i mapa de calor de tots els dies.
- **Mida de la bateria:** controls de capacitat, potència i cost, corba de CO₂ i taula de retorn de la inversió.
- **Fiabilitat:** robustesa a errors de previsió, estalvi per setmana i supòsits.

Les normes de disseny que seguim són a `docs/REGLES_DASHBOARD.md`.

## Fitxers
- `index.html`, `css/style.css`: estructura i estil (tema clar, targetes rodones, IBM Plex).
- `js/scene.js`: escena 3D (three.js 0.170.0, a `vendor/`).
- `js/main.js`: navegació entre vistes, reproducció, panell de la bateria i presentació guiada.
- `js/charts.js`: gràfics de les decisions (D3 7.9, a `vendor/`).
- `data/`: dades generades per `scripts/build_dashboard_data.py` (no editar a mà).
- `analysis.py`: càlculs amb el simulador oficial (els fa servir el script de dades).
- `static/campus_nord.json`: edificis reals (© OpenStreetMap contributors, ODbL), de `scripts/build_campus_json.py`.
- `app.py`, `views.py`, `style.py`, `live2d.html`, `scene3d.html`: versió antiga amb Streamlit, ja no es fa servir (es pot esborrar).
