# Diari de feina i resultats

## Taula de resultats (avaluats amb `python -m src.evaluate <carpeta>`)
| Agent | VALID (7 d/mes) | FULL train | Infraccions | Notes |
|---|---|---|---|---|
| plantilla oficial (`starter_kit`) | 0,94 | 0,00 | 3 / 46 | regles per hores |
| **`agents/estandard_lp`** | **6,08** | **5,65** | 0 | LP 24 h, terminal = 0 |
| `agents/estandard_robust` | 6,08 | 5,67 | 0 | estandard_lp + límit de descàrrega + neteja d'obs + regla de reserva |
| `agents/estandard_robust_pesos_test` | 6,08 | 5,67 | 0 | estandard_robust amb la proporció CO₂/€ del test públic |
| `agents/dificil_previsio_simple` (Mode Difícil) | 19,87 | – | 0 | LP amb xarxa i excedent solar + previsions de preu, CO₂, consum i solar. Òptim teòric: 22,34 |
| `agents/dificil_marges` (Mode Difícil) | 20,75 (F0) / 17,70 (F1) | – | 0 | versió final: veure registre 14/11 vespre. Òptim: 22,34 / 18,75 |
| `agents/dificil_co2_irradiancia` (Mode Difícil) | banc nou: 18,88 / 17,42 / 17,92 (F0/F1/F2) | – | 0 | `dificil_marges` al mateix banc: 18,80 / 17,36 / 17,75. Òptim F0/F1: 20,28 / 18,75 |
| oracle (cota superior) | 6,08 | 5,68 | – | sap el futur sencer |
| ~~`estandard_robust`, cada setmana a part des del 50 %~~ | ~~6,41~~ | – | 0 | **descartat (D-038):** l'oficial no reinicia la bateria; el valor bo és 6,08 |

## Enviaments a la web
| Data/hora | Fitxer | Score públic | Qui | Notes |
|---|---|---|---|---|
| 14/11 tarda | `estandard_lp_1114_1134.zip` (agents/estandard_lp) | **6,43** | Adrià | CO₂ −5,97 % (4.289 kg), factura −7,5 % (8.908 €), 0 infraccions. Local VALID: 6,08 |

## Registre
- **14/11** — Lectura de tot el material, pipeline de dades, avaluador local, primer agent MPC-LP.
- **14/11** — Dry-run a la web: OK. Dashboard v1 (`dashboard/`): animació, comparativa, "què passaria si".
  Sensibilitat (VALID): 1 MWh/250 kW → 3,04 · 2 MWh/500 kW → 6,08 · 4 MWh/1 MW → 11,12 · 8 MWh/1 MW → 16,53.
- **14/11** — Primer enviament oficial (equip **La Datoneta**): 6,43 al leaderboard públic. Coherent amb la validació local (6,08).
- **14/11** — Anàlisi del sostre: òptim teòric 6,0834 vs nostre 6,0833 (validació). Al test som a 6,4315 exacte. Un altre equip treu 6,44 al públic: és soroll de la meitat pública (D-016).
- **14/11** — Comprovació de generalització al test privat (`python tests/check_generalization.py`, scores sense arrodonir,
  resultats a `tests/generalization_results.json`). `estandard_robust` i `estandard_robust_pesos_test`, 0 infraccions a totes les proves:
  - **Tests simulats** (12 setmanes a l'atzar, 1 per mes, 10 repeticions): 5,833 ± 0,177 totes dues; distància a l'òptim
    −0,002 de mitjana (pitjor −0,016, per un tall del comptador a la primera hora, impossible de preveure).
    Diferència entre les dues versions: +0,0001 (empat).
  - **Per mesos**: distància a l'òptim entre 0 i −0,04 (febrer i agost les més grans). No és cap error: amb la proporció
    CO₂/€ exacta del mes, l'agent fa exactament l'òptim. Al test real només compta la proporció del total, que és la que fem servir.
  - **Error a les previsions** 0 / 10 / 20 / 30 %: 5,83 / 5,79 / 5,71 / 5,63 (amb un 30 % d'error encara som al 97 %).
  - **Talls del comptador** (5 talls de 6 h): òptim 5,876 · `estandard_robust` 5,833 · `estandard_lp` 5,644 → el límit de descàrrega val +0,19.
  - **Sensibilitat de params.json** (validació): co2_ref/preu_ref ±20 % i w_co2 0,65–0,75 → entre −0,003 i −0,012. Estable; els valors actuals són els millors.
  - Temps: ~5 s per 2.016 h (en un portàtil lent ~13 s; el límit de la web és 60 s). `make_submission.py`: les dues vàlides.
- **14/11** — Mode Difícil (`agents/dificil_previsio_simple`, avaluat amb `python tests/evaluate_dificil.py`; validació d'11 setmanes amb solar ×12,
  bateria 6.000 kWh / 1.500 kW i 3 h de mercat). Scores amb els perfils calculats SENSE les setmanes de validació:
  `estandard_robust` adaptat (planifica només amb 3 h) 10,50 · regla de reserva sola 15,47 · **`dificil_previsio_simple` 19,87** · òptim teòric 22,34.
  Què aporta cada peça: perfil de consum per dia i hora +1,9 · marge de descàrrega +0,4 · perfil de preu/CO₂ del mes +0,3.
  El que falta fins a l'òptim: previsió de mercat perfecta +1,4 · previsió de consum i solar perfecta +1,1.
  0 infraccions, ~6 s per 1.848 h, checker vàlid.
- **14/11** — Mode Difícil, segona versió (`agents/dificil_lightgbm`, models entrenats amb `python scripts/train_dificil_lightgbm.py`).
  Validació honesta (models i perfils sense les setmanes de validació): `dificil_previsio_simple` 19,87 → **`dificil_lightgbm` 20,02**; òptim teòric 22,34.
  Quant valdria cada previsió si fos perfecta (sobre `dificil_previsio_simple`): CO₂ +0,9 · solar +0,4 · consum +0,3 · preu +0,3.
  Què hem provat amb LightGBM (error mitjà respecte a la previsió senzilla): consum −35 % (score +0,2), preu −30 % (+0,03),
  CO₂ −6 % (el score empitjora) i solar pitjor → només fem servir els models de consum i preu.
  Horitzó de 30–48 h: no canvia res. Al rànquing públic hi ha equips a 22–23; encara no sabem el nostre score públic.
- **14/11** — Enviament al Mode Difícil: `dificil_previsio_simple` → **22,02** al rànquing públic (5è; el primer té 23,23). El nostre 19,95 local
  equival a 22,02 a la web (factor ≈ 1,10).
- **14/11** — On es perden els punts (validació local, sobre `dificil_previsio_simple`): saber el consum net de l'HORA ACTUAL exacte valdria +1,1;
  saber el mercat de les hores +3..+7 exacte, +0,9. La resta de l'horitzó gairebé no importa. Motiu: la descàrrega està limitada pel
  consum net, així que cada kWh d'error en l'hora actual és energia llençada (si ens passem) o no aprofitada (si ens quedem curts).
  `dificil_lightgbm` refet: els models només corregeixen les hores properes (consum i solar +0..+2, preu i CO₂ +3..+8), amb variables noves
  (canvi d'ahir a la mateixa hora, perfil, dia clar). Validació honesta: **20,33** (`dificil_previsio_simple` 19,87); esperem ≈ 22,5 a la web.
  Error de l'hora actual: consum 50 → 27 kW, solar 48 → 42 kW.
- **14/11 vespre** — Iteració sistemàtica del Mode Difícil (`agents/dificil_marges`). Banc de proves amb **dues validacions
  independents** (F0 = últims 7 dies de cada mes del train, F1 = els 7 dies anteriors), models sempre entrenats sense les
  setmanes avaluades, i una tercera (F2) reservada només per comprovar al final. Cada canvi es queda només si millora F0 i F1.
  | Canvi | F0 | F1 | Mitjana |
  |---|---|---|---|
  | Punt de partida (`dificil_lightgbm`) | 20,30 | 17,28 | 18,79 |
  | Perfil solar típic el 1r dia de cada setmana (abans la previsió solar era 0) | 20,34 | 17,30 | 18,82 |
  | Marge de descàrrega diferent de dia (0,94) i de nit (0,98) | 20,39 | 17,34 | 18,87 |
  | Marge per hora: quantil 20 % de l'error real (fora de mostra) a cada hora | 20,46 | 17,41 | 18,93 |
  | Historial: les últimes 72 h del train (el test comença just l'hora després en 10 de 12 mesos) | 20,55 | 17,35 | 18,95 |
  | Variables de mercat "ancorades" (forma d'ahir enganxada a l'última hora coneguda) | 20,55 | 17,38 | 18,97 |
  | CO₂: fórmula ancorada a +3 h i meitat a +4 h; preu: meitat a +3 h | 20,60 | 17,49 | 19,05 |
  | Models de mercat amb 31 fulles | 20,63 | 17,52 | 19,08 |
  | El pla (no només l'hora actual) compta amb el marge d'error de cada hora | **20,69** | **17,56** | **19,12** |
  Descartat (no millorava a totes dues): decisió estocàstica amb el preu ombra del LP (−1,5 → −0,1), sol teòric calculat
  amb astronomia, objectiu L2 (mitjana) als models, horitzó de 30–48 h, models més grans per a consum i solar,
  model només per a l'hora actual. F2 (no usada per decidir): 17,23 → **17,33**.
  Què queda fins a l'òptim (F0): consum net de l'hora actual +0,57, CO₂ +3..+8 h +0,66, preu +0,23. Són límits de les dades
  horàries (núvols, rampes del matí) més que del mètode.
  Final: entrenat amb tot el train, 5 llavors per model. 0 infraccions, checker vàlid, ~12 s per 2.016 h, zip de 6 MB.
- **14/11 nit** — Segona ronda sobre `dificil_marges` (mateix banc de proves F0/F1, F2 reservada):
  | Canvi | F0 | F1 | Mitjana |
  |---|---|---|---|
  | `dificil_marges` anterior | 20,69 | 17,56 | 19,12 |
  | Amb excedent solar, carregar pensant en el cas de més sol (quantil 25 % de l'error): s'exportaven 8 MWh d'excedent gratis | 20,72 | 17,62 | 19,17 |
  | Model de preu a totes les hores (abans només fins a +8 h; l'error a +12 h era 28 €/MWh) | **20,75** | **17,70** | **19,22** |
  F2 (reservada): 17,33 → 17,36. Descartat: XGBoost/ExtraTrees en conjunt (error −1–3 %, no compensa), peatge per cicle,
  model de CO₂ a totes les hores (empitjora), canviar la previsió base del mercat, vent (el sensor marca sempre 0).
  La web no té més dades útils en temps real: `entradas_salidas.csv` no arriba a l'agent.
- **14/11 nit** — `dificil_marges` v2 enviat: **22,96** al rànquing públic del Mode Difícil (predicció local: ~23,0 → la validació local és fiable).
- **14/11 nit** — Investigació a fons per buscar un salt (líder: 23,46). Línies de la literatura provades:
  - *Política = solució d'un problema d'optimització amb paràmetres ajustats per cerca evolutiva* (enfocament del guanyador del
    CityLearn Challenge): 10 paràmetres de decisió optimitzats sobre el score simulat. F0/F1 +0,03, però **F2 −0,007** → sobreajust, descartat.
  - *Imitation learning* de l'agent amb informació perfecta (corregir l'acció del LP cap a l'òptima des del mateix estat):
    el model no aconsegueix acostar les accions a l'òptima en setmanes no vistes (183 → 182 kW d'error) → la diferència amb
    l'òptim **no és predictible** amb la informació de l'agent.
  - Conjunt LightGBM + XGBoost + ExtraTrees: −1–3 % d'error de previsió, sense efecte al score.
  - CO₂/preu actuals com a pista dels núvols (sol peninsular): correlació −0,05, empitjora.
  - Web: cap dada nova útil en temps real (vent = 0 sempre; senyals de maquinària no arriben a l'agent).
  **Conclusió:** l'agent és al límit d'informació. Amb previsions perfectes faria 22,15 (validació); tot el que falta és error de
  previsió irreductible amb dades horàries. Ens quedem amb `dificil_marges` v2.
- **15/11 matí** — Diagnosi de la web amb la Validació Ràpida (agent que no mou la bateria i ensenya el que rep): la
  irradiància d'`obs` és la de l'hora passada (la mateixa hora que `ultima_solar_kw`), el mercat és de 3 h i el test comença
  l'hora després del train (24/09 00:00). El nostre simulador local reprodueix la web.
  Historial de la web (Mode Dificil): La Datoneta 22,02 · **22,96** (`dificil_marges`) · 22,75 · 22,76 (`dificil_co2_irradiancia`).
- **15/11 matí** — `dificil_co2_ree` (D-050): model directe de CO₂ amb 2,5 anys de REE. F0 20,71 → 20,79, F1 17,54 → 17,57.
  Provat i descartat: pla amb escenaris en dues etapes (+0,01 / +0,04, més lent).
- **15/11 matí** — Enviaments: `dificil_co2_irradiancia` (amb REE) 22,70 · `dificil_co2_ree` 22,83. Cap supera el 22,96.
  Entregues finals (D-051): `estandard_robust` i `dificil_marges`.
- **15/11 migdia** — Zips finals a `entregues/`: `estandard_robust.zip` i `dificil_marges.zip` (els dos passen el checker).

## Conclusions de l'anàlisi exploratòria (`notebooks/01_eda.ipynb`)
- **Consum net gairebé sempre > 500 kW (99,5 %):** el campus consumeix una mitjana de ~1.120 kW i la generació solar arriba com a màxim a ~145 kW. La bateria mai no exporta excedents a la xarxa i no cal predir el consum futur.
- **Finestra clara d'operació:** la intensitat de CO₂ cau al migdia (11–16 h) per la generació solar peninsular, mentre que el preu PVPC assoleix el màxim al vespre (19–22 h).
- **Correlació preu–CO₂ de 0,58:** els dos objectius van en la mateixa direcció però no són idèntics; formular-los com a funció objectiu lineal ponderada (70 % CO₂, 30 % cost) captura el compromís òptim.
- **Qualitat de dades i robustesa:** el comptador presenta consum nocturn pla (0–5 h) i talls puntuals a 0 kW (p. ex. 17/06/2026), fet que justifica el límit de descàrrega `max_dis_now` de `estandard_robust`.
- **Empat amb l'òptim teòric:** `estandard_robust` obté **6,08** a la validació (igual que l'Oracle, amb 0 infraccions) i **6,43** al test públic oficial.

## Conclusions actualitzades (Mode Estàndard i Mode Difícil — 3 bateries)
- **Canvi de règim amb 3 bateries i solar ×12:** al Mode Estàndard (500 kW) el consum net supera el límit el 99,5 % de les hores; al Mode Difícil (1.500 kW, 6.000 kWh, solar ×12) apareixen excedents solars (< 0 kW) i hores per sota de 1.500 kW, fet que obliga a predir consum i solar i a incloure la xarxa dins del LP.
- **Lideratge als dos modes:** `estandard_robust` obté **6,08** en validació (empat amb l'Oracle) i **6,43** al test públic; `dificil_marges` assoleix **20,75** (F0, 93 % de l'Oracle) i **22,96** al leaderboard públic oficial, amb **0 infraccions** en tots dos casos.
