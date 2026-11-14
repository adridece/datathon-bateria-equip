# Riscos i imprevistos (què pot fallar i com ho evitem)

| # | Risc | Probabilitat | Impacte | Com ho evitem | Estat |
|---|---|---|---|---|---|
| R1 | `linprog` falla o llença una excepció al servidor (versió de scipy vella) | Baixa | Molt alt (agent mort = 0 punts) | `try/except` al voltant del LP + estratègia de reserva simple (carregar a les hores més netes, descarregar a les més brutes) | Pendent (Ivan) |
| R2 | Valors estranys a `obs` (NaN, llistes buides, preus negatius) | Baixa | Alt | Netejar entrades: NaN → valor actual; llista buida → 0 kW | Pendent (Ivan) |
| R3 | Consum net < 500 kW (caps de setmana assolellats, forats del comptador) → descarreguem energia que es perd | Mitjana (≈0,5 % hores) | Petit | Limitar la descàrrega amb una previsió de consum (perfil per hora/dia + darrera mesura) | Pendent (Ivan) |
| R4 | Timeout de 60 s | Molt baixa (≈3 s ara) | Molt alt | Mesurar el temps a cada versió; mai entrenar models dins `act` | OK |
| R5 | Infraccions | Molt baixa | −0,2 punts cadascuna | *Safety clamp* oficial amb marge | OK |
| R6 | Sobreajustar paràmetres al leaderboard públic (50 % del test) | Mitjana | Mitjà | Ajustar només amb validació local per mesos; poques trameses i justificades | Norma |
| R7 | Llibreria o mòdul prohibit (`os`, `sys`...) → rebutjat | Baixa | Alt | Passar sempre `scripts/make_submission.py` + validació ràpida a la web | OK |
| R8 | Diferent pes CO₂/cost al test (normalització) | Segura (petita) | Petit | Provar la sensibilitat de `co2_ref`/`preu_ref` | Pendent (Ivan) |
| R9 | Conflictes de git entre els 4 | Mitjana | Mitjà | Cada un a la seva carpeta; pull/push sovint | Norma |
| R10 | Filtrar la clau d'API o el PIN | Baixa | Alt | `.env` ignorat; PIN mai al repo | OK |
| R11 | Rastre d'assistents al repo públic | Mitjana | Alt (requisit de l'equip) | `scripts/export_public.py` busca paraules prohibides i s'atura | OK |
| R12 | Quedar-nos sense temps per a la presentació | Mitjana | Molt alt | Punts de control a `docs/EQUIP.md`; congelar l'agent a +14 h | Norma |
