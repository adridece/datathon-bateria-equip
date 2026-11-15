# Instruccions per a qualsevol assistent de codi d'aquest projecte

Llegeix aquest fitxer sencer abans de fer res. Després llegeix, en aquest ordre:
0. `docs/EQUIP.md` – qui fa què, branques i punts de control.
1. `docs/CONTEXT.md` – tot el repte resumit (normes, puntuació, dades, descobertes).
2. `docs/DECISIONS.md` – què hem decidit i per què.
3. `docs/DIARI.md` – resultats i registre de feina.
4. `docs/PLA.md` – què queda per fer.
5. `docs/GUIA_EQUIP.md` – guia pas a pas des de zero (instal·lar, treballar, enviar).

## Qui som
Equip de 4 estudiants de 2n de carrera (UPC) a la Datathon FME 2026, repte UPC Sostenible (bateria).
Treballem des de Mac i Windows, cadascú amb el seu assistent de codi.

## Normes OBLIGATÒRIES
1. **Cap rastre d'assistents de codi.** Mai afegir línies `Co-Authored-By`, "Generated with...", ni
   mencions a cap assistent en commits, codi, comentaris, notebooks ni documents. Els commits els signa
   la persona de l'equip que treballa.
2. **Estil de codi (molt important):** ha de semblar escrit per nosaltres.
   - **Codi en anglès** (noms de variables, funcions i fitxers nous) i **comentaris en català**.
   - Simple i llegible: funcions curtes, noms clars, res de sobre-enginyeria ni capes innecessàries.
   - Comentaris curts i naturals, només on aporten (el "per què", no el "què"). Res de comentaris
     estranys, decoratius, en majúscules, amb emojis o massa formals.
   - Ha de funcionar sempre: provar-ho abans de pujar-ho.
3. **Documentar sempre**: tota decisió nova → `docs/DECISIONS.md`; tot resultat nou → taula de
   `docs/DIARI.md`. Si no està escrit, no ha passat.
4. **Avaluar sempre amb el simulador oficial**: `python -m src.evaluate agents/<carpeta>`.
   No modificar mai `starter_kit/` (és material oficial).
5. **agent.py ha de passar el checker**: `python scripts/make_submission.py agents/<carpeta>`.
   Només llibreries permeses; res de `os`, `sys`, `eval`... (llista a `docs/CONTEXT.md`).
6. **Mai pujar secrets**: la clau d'API va a `.env` (ignorat per git). Mai escriure-la en cap fitxer versionat.
7. Codi multiplataforma: `pathlib`, scripts en Python (no bash), sense rutes absolutes.
8. Cada agent nou en una carpeta pròpia `agents/<nom>/` (no trepitjar la feina dels altres).
9. **Explicar-ho tot com si l'usuari no en sabés res**: cap membre de l'equip és expert. Abans de
   fer res, explica què faràs i per què; després, com comprovar-ho. Dona les comandes exactes (Windows
   i Mac si canvien), defineix els termes tècnics i actualitza `docs/GUIA_EQUIP.md` si canvia el procés.
10. **Branques:** treballar a la branca del bloc (`dashboard`, `agent`, `analisi`, `presentacio`), mai directament a `main`.
    Abans de començar: `git pull origin main`. Per passar a `main`: Pull Request a GitHub.
11. **Dashboards i visuals:** seguir `docs/RECERCA_DASHBOARD.md` (sistema de disseny, 3D, regles per no semblar genèric).
12. Fer `git pull` abans de començar i commits petits amb missatges clars en català.

## Comandes útils
```
python scripts/setup.py                         # primer cop: dades
python -m src.evaluate agents/estandard_robust            # puntuació local
python -m src.evaluate --oracle                 # cota superior
python scripts/make_submission.py agents/estandard_robust # zip + validació
```
