# Optimització de la bateria del Campus Nord (Datathon FME 2026)

Repte **UPC Sostenible**: decidir cada hora quanta energia carrega o descarrega la bateria del Campus Nord per reduir
les emissions de CO₂ (70 % del pes) i la factura elèctrica (30 %) respecte de no tenir bateria.

**Equip:** Jesús Valor, Adrià De La Cereza, Ivan Murillo i Martí Montemayor.

## La solució en poques paraules
- **Mode Estàndard** (2.000 kWh, ±500 kW, preu i CO₂ de les 24 h següents coneguts): control predictiu amb programació
  lineal. Cada hora planifica les 24 h següents i aplica només la primera decisió. Arriba a l'òptim teòric (6,08 a la
  validació local, 6,43 al test públic).
- **Mode Difícil** (6.000 kWh, ±1.500 kW, 12× solar, només 3 h de mercat): el mateix control amb previsions de preu,
  CO₂, consum i solar fetes amb models entrenats amb el train, marges de seguretat per a l'error de previsió i
  detecció de la irradiància de l'hora actual. Explicat pas a pas a [`docs/ANALISI_MODE_DIFICIL.md`](docs/ANALISI_MODE_DIFICIL.md).
- **Dashboard** per a UPC Sostenible: el campus en 3D en temps real, conclusions, estratègia, planificador, mida de la
  bateria i rendiment ([`dashboard/README.md`](dashboard/README.md)).

Totes les decisions i el seu perquè: [`docs/DECISIONS.md`](docs/DECISIONS.md). Resultats: [`docs/DIARI.md`](docs/DIARI.md).

## Posar-ho en marxa
Cal Python 3.11.

**Mac i Linux**
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/setup.py
```
**Windows (PowerShell)**
```
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/setup.py
```

## Ús
```
python -m src.evaluate agents/estandard_robust            # Mode Estàndard: puntuació local
python tests/bench_dificil.py 0,1,2                    # Mode Difícil: validació honesta i òptim teòric
python scripts/make_submission.py agents/dificil_co2_irradiancia    # zip per a la web, ja validat
python scripts/serve_dashboard.py                   # obre el dashboard a http://localhost:8000
```

## Estructura
```
agents/        un agent per carpeta (vegeu agents/README.md)
src/           dades, simulació i avaluació local
scripts/       preparar dades, entrenar, empaquetar i el dashboard
tests/         proves dels agents i bancs de validació
dashboard/     web del dashboard (HTML, CSS i JS)
notebooks/     anàlisi exploratòria
docs/          context, decisions, diari, anàlisi del Mode Difícil i figures
```
