# Agents

Cada carpeta és un agent complet (`agent.py` i, si cal, paràmetres i models). Els finals són els marcats en negreta.

## Mode Estàndard (2.000 kWh, ±500 kW, 24 h de mercat)
| Carpeta | Què és |
|---|---|
| `mpc_lp` | Primera versió: programació lineal sobre les 24 h següents. |
| **`mpc_robust`** | `mpc_lp` + límit de descàrrega segons el consum, neteja de dades estranyes i regla de reserva. |
| **`mpc_test_weights`** | `mpc_robust` amb la proporció CO₂/€ del test públic. Empata amb `mpc_robust`. |

## Mode Difícil (6.000 kWh, ±1.500 kW, 12× solar, 3 h de mercat)
| Carpeta | Què és |
|---|---|
| `hard_mpc` | Primera versió: previsions senzilles (dies anteriors i perfils del train) i el mateix LP. |
| `hard_ml` | `hard_mpc` amb models LightGBM que corregeixen les previsions de les hores properes. |
| `hard_final` | Versió validada de l'Ivan: marges per hora, historial del train, excedent solar. 22,96 a la web. |
| **`hard_v3`** | `hard_final` + model directe de CO₂ (+3..+12 h) + detecció de la irradiància de l'hora actual. |

Per entrenar els del Mode Difícil: `python scripts/train_hard_final.py` i `python scripts/train_hard_v3.py`.
