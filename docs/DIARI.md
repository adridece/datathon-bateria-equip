# Diari de feina i resultats

## Taula de resultats (avaluats amb `python -m src.evaluate <carpeta>`)
| Agent | VALID (7 d/mes) | FULL train | Infraccions | Notes |
|---|---|---|---|---|
| plantilla oficial (`starter_kit`) | 0,94 | 0,00 | 3 / 46 | regles per hores |
| **`agents/mpc_lp`** | **6,08** | **5,65** | 0 | LP 24 h, terminal = 0 |
| `agents/mpc_robust` | 6,08 | 5,67 | 0 | mpc_lp + límit de descàrrega + neteja d'obs + regla de reserva |
| `agents/mpc_test_weights` | 6,08 | 5,67 | 0 | mpc_robust amb la proporció CO₂/€ del test públic |
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
- **14/11** — Anàlisi del sostre: òptim teòric 6,0834 vs nostre 6,0833 (validació). Al test som a 6,4315 exacte. Un altre equip treu 6,44 al públic: és soroll de la meitat pública (D-016).
- **14/11** — Comprovació de generalització al test privat (`python tests/check_generalization.py`, scores sense arrodonir,
  resultats a `tests/generalization_results.json`). `mpc_robust` i `mpc_test_weights`, 0 infraccions a totes les proves:
  - **Tests simulats** (12 setmanes a l'atzar, 1 per mes, 10 repeticions): 5,833 ± 0,177 totes dues; distància a l'òptim
    −0,002 de mitjana (pitjor −0,016, per un tall del comptador a la primera hora, impossible de preveure).
    Diferència entre les dues versions: +0,0001 (empat).
  - **Per mesos**: distància a l'òptim entre 0 i −0,04 (febrer i agost les més grans). No és cap error: amb la proporció
    CO₂/€ exacta del mes, l'agent fa exactament l'òptim. Al test real només compta la proporció del total, que és la que fem servir.
  - **Error a les previsions** 0 / 10 / 20 / 30 %: 5,83 / 5,79 / 5,71 / 5,63 (amb un 30 % d'error encara som al 97 %).
  - **Talls del comptador** (5 talls de 6 h): òptim 5,876 · `mpc_robust` 5,833 · `mpc_lp` 5,644 → el límit de descàrrega val +0,19.
  - **Sensibilitat de params.json** (validació): co2_ref/preu_ref ±20 % i w_co2 0,65–0,75 → entre −0,003 i −0,012. Estable; els valors actuals són els millors.
  - Temps: ~5 s per 2.016 h (en un portàtil lent ~13 s; el límit de la web és 60 s). `make_submission.py`: les dues vàlides.
