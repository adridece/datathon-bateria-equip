# Entregues finals

Els dos zips que hem pujat a la web, un per mode. Es poden tornar a generar amb
`python scripts/make_submission.py agents/<carpeta>` (surten a `submissions/`, que git no guarda).

| Zip | Agent | Mode | Web (públic) | Notes |
|---|---|---|---|---|
| `estandard_robust.zip` | `agents/estandard_robust` | Estàndard (2.000 kWh, ±500 kW, 24 h de mercat) | 6,43 | Òptim a la validació (6,08), 0 infraccions. |
| `dificil_marges.zip` | `agents/dificil_marges` | Difícil (6.000 kWh, ±1.500 kW, solar ×12, 3 h de mercat) | **22,96** | La que presentem al jurat (només compta el Mode Difícil). 0 infraccions. |

Tots dos passen el checker oficial (`starter_kit/check_submission.py`). El zip del Difícil té els mateixos models que
l'enviament de dissabte a les 18:39 (només canvien comentaris de l'`agent.py`). Decisió: D-051.
