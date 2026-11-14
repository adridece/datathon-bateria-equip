# Instruccions per a qualsevol assistent de codi d'aquest projecte

Llegeix aquest fitxer sencer abans de fer res. Després llegeix, en aquest ordre:
1. `docs/CONTEXT.md` – tot el repte resumit (normes, puntuació, dades, descobertes).
2. `docs/DECISIONS.md` – què hem decidit i per què.
3. `docs/DIARI.md` – resultats i registre de feina.
4. `docs/PLA.md` – què queda per fer.

## Qui som
Equip de 4 estudiants de 2n de carrera (UPC) a la Datathon FME 2026, repte UPC Sostenible (bateria).
Treballem des de Mac i Windows, cadascú amb el seu assistent de codi.

## Normes OBLIGATÒRIES
1. **Cap rastre d'assistents de codi.** Mai afegir línies `Co-Authored-By`, "Generated with...", ni
   mencions a cap assistent en commits, codi, comentaris, notebooks ni documents. Els commits els signa
   la persona de l'equip que treballa.
2. **Estil humà d'estudiants de 2n**: comentaris en català, curts i naturals; codi senzill i llegible,
   sense sobre-enginyeria ni comentaris excessivament formals.
3. **Documentar sempre**: tota decisió nova → `docs/DECISIONS.md`; tot resultat nou → taula de
   `docs/DIARI.md`. Si no està escrit, no ha passat.
4. **Avaluar sempre amb el simulador oficial**: `python -m src.evaluate agents/<carpeta>`.
   No modificar mai `starter_kit/` (és material oficial).
5. **agent.py ha de passar el checker**: `python scripts/make_submission.py agents/<carpeta>`.
   Només llibreries permeses; res de `os`, `sys`, `eval`... (llista a `docs/CONTEXT.md`).
6. **Mai pujar secrets**: la clau d'API va a `.env` (ignorat per git). Mai escriure-la en cap fitxer versionat.
7. Codi multiplataforma: `pathlib`, scripts en Python (no bash), sense rutes absolutes.
8. Cada agent nou en una carpeta pròpia `agents/<nom>/` (no trepitjar la feina dels altres).
9. Fer `git pull` abans de començar i commits petits amb missatges clars en català.

## Comandes útils
```
python scripts/setup.py                         # primer cop: dades
python -m src.evaluate agents/mpc_lp            # puntuació local
python -m src.evaluate --oracle                 # cota superior
python scripts/make_submission.py agents/mpc_lp # zip + validació
```
