# Dashboard

Tauler de decisions per a UPC Sostenible (side challenge de la Tukey Commission). És una web feta a mida, d'una sola
pantalla: barra lateral amb 6 vistes i el Campus Nord real en 3D com a peça central.

```
python scripts/serve_dashboard.py
```
S'obre sol al navegador (http://localhost:8000). Funciona sense internet. Per parar-lo: `Ctrl + C`.

A la barra superior hi ha un interruptor **Estàndard / Difícil**. Estàndard mostra `estandard_robust` (2.000 kWh, ±500 kW);
Difícil mostra `dificil_marges` (6.000 kWh, ±1.500 kW, solar ×12 i només 3 h de mercat, com la web). El mode queda a
l'adreça (`http://localhost:8000/?mode=dificil`), així es pot compartir l'enllaç.

Si canvia algun agent o les dades, regenereu les xifres dels dos modes amb (el primer cop tarda uns 10 minuts):
```
python scripts/build_dashboard_data.py
```

## Què hi ha
- **Campus en directe** (s'obre primer): el 3D amb els fluxos d'energia hora a hora, el panell "Ara mateix" (bateria,
  rellotge del dia, semàfor per al campus, xifres i el motiu de cada decisió), el pla de 24 h amb com de segura és cada
  decisió i els avisos de la setmana.
- **Conclusions:** les decisions per a UPC Sostenible amb la xifra que les justifica, què guanya el campus amb la bateria
  i el calendari d'estalvi.
- **Estratègia:** estratègies comparades, què fa a cada hora, diagrames de caixa de Tukey del CO₂, quan compensa més i
  polit de medianes.
- **Planificador:** "què passaria si" canvien el preu, el CO₂, la reserva, la potència o la prioritat.
- **Mida de la bateria:** capacitat, potència i cost, corba de CO₂ i retorn de la inversió.
- **Rendiment:** taula setmana a setmana (descarregable), robustesa a errors de previsió, historial i supòsits.
- **Informe PDF** (botó de dalt): 2 pàgines A4 amb el resum, les decisions i el rendiment.

Les normes de disseny que seguim són a `docs/REGLES_DASHBOARD.md`.

## Fitxers
- `index.html`, `css/style.css`: estructura i estil (tema clar, targetes rodones, IBM Plex).
- `js/scene.js`: escena 3D (three.js 0.170.0, a `vendor/`).
- `js/main.js`: navegació, reproducció, panell "Ara mateix", pla de 24 h i selector de setmanes.
- `js/planner.js`: planificador (programació dinàmica al navegador).
- `report.html`: informe de 2 pàgines per desar en PDF.
- `js/charts.js`: gràfics de les decisions (D3 7.9, a `vendor/`).
- `data/`: dades generades per `scripts/build_dashboard_data.py` (no editar a mà); `history.json` guarda l'historial de rendiment.
- `analysis.py`: càlculs amb el simulador oficial (els fa servir el script de dades).
- `static/campus_nord.json`: edificis reals (© OpenStreetMap contributors, ODbL), de `scripts/build_campus_json.py`.
