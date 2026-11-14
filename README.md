# Optimització de la bateria del campus · Datathon FME 2026

Repte **UPC Sostenible**: decidir cada hora quanta energia carrega o descarrega una bateria de
2 MWh / 500 kW del Campus Nord per reduir les emissions de CO₂ (70 %) i la factura elèctrica (30 %).

## Equip
Jesús Martí · Adrià De La Cereza · Ivan Murillo · Martí Montemayor

## La nostra solució (resum)
Control predictiu (MPC) amb programació lineal: cada hora resolem un LP sobre les properes 24 h
(preu i CO₂ són coneguts) i apliquem només la primera decisió. Arriba al mateix resultat que un
"oracle" que coneix tot el futur. Detalls a [`docs/DECISIONS.md`](docs/DECISIONS.md).

| Agent | Score local (validació) |
|---|---|
| Plantilla oficial | 0,94 |
| **MPC + LP (nostre)** | **6,08** |
| Cota superior teòrica | 6,08 |

## Posar-ho en marxa
Cal Python 3.11.

**Mac / Linux**
```
python3.11 -m venv .venv
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
python -m src.evaluate agents/mpc_lp             # avaluar un agent
python scripts/make_submission.py agents/mpc_lp  # crear el zip per a la web i validar-lo
```

## Estructura
```
agents/        un agent per carpeta (agent.py + params)
src/           dades i avaluació local
scripts/       setup, empaquetar l'enviament, exportar
notebooks/     anàlisi exploratòria
docs/          context del repte, decisions, diari i pla
starter_kit/   material oficial (no es toca)
```
