# Agents

Només hi deixem els dos agents que presentem al jurat, un per mode. Els altres que vam provar són a l'historial de git
i explicats a `docs/DECISIONS.md` i `docs/DIARI.md` (la columna "Abans" és el nom que tenien als enviaments a la web).

| Mode | Carpeta | Abans | Què és | Web (públic) |
|---|---|---|---|---|
| Estàndard (2.000 kWh, ±500 kW, 24 h de mercat) | `estandard_robust` | `mpc_robust` | Programació lineal de 24 h + límit de descàrrega segons el consum, neteja de dades estranyes i regla de reserva. | 6,43 |
| Difícil (6.000 kWh, ±1.500 kW, 12× solar, 3 h de mercat) | `dificil_marges` | `hard_final` | Programació lineal de 24 h amb previsions LightGBM, marges per hora segons l'error de previsió, historial del train i excedent solar. | 22,96 |

Entrenar el Difícil: `python scripts/train_dificil_marges.py`.
Validar: `python -m src.evaluate agents/estandard_robust` (Estàndard) i `python tests/bench_dificil.py 0,1,2` (Difícil).
Zip per a la web: `python scripts/make_submission.py agents/<carpeta>`.
