# Diari de feina i resultats

## Taula de resultats (avaluats amb `python -m src.evaluate <carpeta>`)
| Agent | VALID (7 d/mes) | FULL train | Infraccions | Notes |
|---|---|---|---|---|
| plantilla oficial (`starter_kit`) | 0,94 | 0,00 | 3 / 46 | regles per hores |
| **`agents/mpc_lp`** | **6,08** | **5,65** | 0 | LP 24 h, terminal = 0 |
| `agents/mpc_robust` | 6,08 | 5,67 | 0 | mpc_lp + límit de descàrrega + neteja d'obs + regla de reserva |
| `agents/mpc_test_weights` | 6,08 | 5,67 | 0 | mpc_robust amb la proporció CO₂/€ del test públic |
| `agents/hard_mpc` (Mode Difícil) | 19,87 | – | 0 | LP amb xarxa i excedent solar + previsions de preu, CO₂, consum i solar. Òptim teòric: 22,34 |
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
- **14/11** — Mode Difícil (`agents/hard_mpc`, avaluat amb `python tests/evaluate_hard.py`; validació d'11 setmanes amb solar ×12,
  bateria 6.000 kWh / 1.500 kW i 3 h de mercat). Scores amb els perfils calculats SENSE les setmanes de validació:
  `mpc_robust` adaptat (planifica només amb 3 h) 10,50 · regla de reserva sola 15,47 · **`hard_mpc` 19,87** · òptim teòric 22,34.
  Què aporta cada peça: perfil de consum per dia i hora +1,9 · marge de descàrrega +0,4 · perfil de preu/CO₂ del mes +0,3.
  El que falta fins a l'òptim: previsió de mercat perfecta +1,4 · previsió de consum i solar perfecta +1,1.
  0 infraccions, ~6 s per 1.848 h, checker vàlid.
- **14/11** — Mode Difícil, segona versió (`agents/hard_ml`, models entrenats amb `python scripts/train_hard.py`).
  Validació honesta (models i perfils sense les setmanes de validació): `hard_mpc` 19,87 → **`hard_ml` 20,02**; òptim teòric 22,34.
  Quant valdria cada previsió si fos perfecta (sobre `hard_mpc`): CO₂ +0,9 · solar +0,4 · consum +0,3 · preu +0,3.
  Què hem provat amb LightGBM (error mitjà respecte a la previsió senzilla): consum −35 % (score +0,2), preu −30 % (+0,03),
  CO₂ −6 % (el score empitjora) i solar pitjor → només fem servir els models de consum i preu.
  Horitzó de 30–48 h: no canvia res. Al rànquing públic hi ha equips a 22–23; encara no sabem el nostre score públic.
