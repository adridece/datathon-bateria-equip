# Diari de feina i resultats

## Taula de resultats (avaluats amb `python -m src.evaluate <carpeta>`)
| Agent | VALID (7 d/mes) | FULL train | Infraccions | Notes |
|---|---|---|---|---|
| plantilla oficial (`starter_kit`) | 0,94 | 0,00 | 3 / 46 | regles per hores |
| **`agents/mpc_lp`** | **6,08** | **5,65** | 0 | LP 24 h, terminal = 0 |
| oracle (cota superior) | 6,08 | 5,68 | – | sap el futur sencer |

## Enviaments a la web
| Data/hora | Fitxer | Score públic | Qui | Notes |
|---|---|---|---|---|
| 14/11 tarda | `mpc_lp_1114_1134.zip` (agents/mpc_lp) | **6,43** | Adrià | CO₂ −5,97 % (4.289 kg), factura −7,5 % (8.908 €), 0 infraccions. Local VALID: 6,08 |

## Registre
- **14/11** — Lectura de tot el material, pipeline de dades, avaluador local, primer agent MPC-LP.
- **14/11** — Dry-run a la web: OK. Dashboard v1 (`dashboard/`): animació, comparativa, "què passaria si".
  Sensibilitat (VALID): 1 MWh/250 kW → 3,04 · 2 MWh/500 kW → 6,08 · 4 MWh/1 MW → 11,12 · 8 MWh/1 MW → 16,53.
- **14/11** — Primer enviament oficial (equip **La Datoneta**): 6,43 al leaderboard públic. Coherent amb la validació local (6,08).
