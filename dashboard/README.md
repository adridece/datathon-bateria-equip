# Dashboard

Tauler de decisions per a UPC Sostenible (side challenge Tukey Commission).

```
streamlit run dashboard/app.py
```
S'obre sol al navegador (http://localhost:8501). Per parar-lo: `Ctrl + C` a la terminal.
Funciona sense internet: les fonts i three.js són dins del repo.

## Pàgines
1. **Resum** – què ha de fer la UPC, amb les xifres clau i les 4 decisions.
2. **Operació en directe** – el Campus Nord real en 3D hora a hora (o esquema 2D). Botó "Presentació guiada" (tecla P).
3. **Estratègia** – per què el control predictiu és el millor i quan carrega/descarrega.
4. **Dimensionament** – quina mida de bateria convé i en quants anys es recupera.
5. **Fiabilitat** – robustesa a errors de previsió, estacionalitat i supòsits.

## Fitxers
- `app.py` – navegació entre pàgines.
- `views.py` – les pàgines.
- `analysis.py` – càlculs (tots amb el simulador oficial; es guarden a `data/processed/`).
- `style.py` – colors, tipografia i tema dels gràfics (un sol lloc per a tot).
- `scene3d.html` – escena 3D (three.js 0.170.0, a `vendor/`).
- `live2d.html` – esquema 2D de reserva.
- `static/campus_nord.json` – edificis reals del campus (© OpenStreetMap contributors, ODbL), generat amb `scripts/build_campus_json.py`.
