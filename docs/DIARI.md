# Diari de feina i resultats

## Taula de resultats (avaluats amb `python -m src.evaluate <carpeta>`)
| Agent | VALID (7 d/mes) | FULL train | Infraccions | Notes |
|---|---|---|---|---|
| plantilla oficial (`starter_kit`) | 0,94 | 0,00 | 3 / 46 | regles per hores |
| **`agents/mpc_lp`** | **6,08** | **5,65** | 0 | LP 24 h, terminal = 0 |
| `agents/mpc_robust` | 6,08 | 5,67 | 0 | mpc_lp + límit de descàrrega + neteja d'obs + regla de reserva |
| `agents/mpc_test_weights` | 6,08 | 5,67 | 0 | mpc_robust amb la proporció CO₂/€ del test públic |
| oracle (cota superior) | 6,08 | 5,68 | – | sap el futur sencer |
| `mpc_robust`, cada setmana a part des del 50 % (dashboard) | 6,41 | – | 0 | igual que l'oracle setmana a setmana (6,41); més a prop del test públic (6,43) |

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

## Conclusions de l'anàlisi exploratòria (`notebooks/01_eda.ipynb`)
- **Consum net gairebé sempre > 500 kW (99,5 %):** el campus consumeix una mitjana de ~1.120 kW i la generació solar arriba com a màxim a ~145 kW. La bateria mai no exporta excedents a la xarxa i no cal predir el consum futur.
- **Finestra clara d'operació:** la intensitat de CO₂ cau al migdia (11–16 h) per la generació solar peninsular, mentre que el preu PVPC assoleix el màxim al vespre (19–22 h).
- **Correlació preu–CO₂ de 0,58:** els dos objectius van en la mateixa direcció però no són idèntics; formular-los com a funció objectiu lineal ponderada (70 % CO₂, 30 % cost) captura el compromís òptim.
- **Qualitat de dades i robustesa:** el comptador presenta consum nocturn pla (0–5 h) i talls puntuals a 0 kW (p. ex. 17/06/2026), fet que justifica el límit de descàrrega `max_dis_now` de `mpc_robust`.
- **Empat amb l'òptim teòric:** `mpc_robust` obté **6,08** a la validació (igual que l'Oracle, amb 0 infraccions) i **6,43** al test públic oficial.
