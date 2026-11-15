# Agents

Cada carpeta és un agent complet (`agent.py` i, si cal, paràmetres i models). El nom diu el mode i què fa diferent.
Els finals són els marcats en negreta. La columna "Abans" és el nom que tenia als primers enviaments a la web.

## Mode Estàndard (2.000 kWh, ±500 kW, 24 h de mercat)
| Carpeta | Abans | Què és |
|---|---|---|
| `estandard_lp` | `mpc_lp` | Primera versió: programació lineal sobre les 24 h següents. |
| **`estandard_robust`** | `mpc_robust` | L'anterior + límit de descàrrega segons el consum, neteja de dades estranyes i regla de reserva. |
| **`estandard_robust_pesos_test`** | `mpc_test_weights` | `estandard_robust` amb la proporció CO₂/€ del test públic. Empata amb l'anterior. |

## Mode Difícil (6.000 kWh, ±1.500 kW, 12× solar, 3 h de mercat)
| Carpeta | Abans | Què és |
|---|---|---|
| `dificil_previsio_simple` | `hard_mpc` | Previsions senzilles (dies anteriors i perfils del train) i el mateix LP. |
| `dificil_lightgbm` | `hard_ml` | L'anterior amb models LightGBM que corregeixen les previsions de les hores properes. |
| `dificil_marges` | `hard_final` | Versió validada de l'Ivan: marges per hora, historial del train, excedent solar. 22,96 a la web. |
| **`dificil_co2_irradiancia`** | `hard_v3` | L'anterior + model directe de CO₂ (+3..+12 h), detecció de la irradiància de l'hora actual, dades meteorològiques completes i marge calibrat fora de mostra. |
| `dificil_co2_ree` | – | `dificil_marges` + model directe de CO₂ (+3..+12 h) entrenat amb l'històric públic de REE 2023-2025. |

Entrenar: `python scripts/train_dificil_marges.py`, `python scripts/train_dificil_co2_irradiancia.py` i `python scripts/train_dificil_co2_ree.py`.
Validar: `python tests/bench_dificil.py 0,1,2` (Difícil) i `python -m src.evaluate agents/estandard_robust` (Estàndard).
