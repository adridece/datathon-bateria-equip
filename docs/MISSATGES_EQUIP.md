# Missatges per a l'equip

## 1) Missatge per al grup (WhatsApp / Discord)

> Ei equip! Ja tenim el projecte muntat i un primer agent que, en les nostres proves, arriba al
> màxim teòric (6,08 punts; la plantilla oficial en fa 0,94). Ja l'hem validat a la web, però encara
> no l'hem enviat al rànquing.
>
> **Què heu de fer ara (30 min):**
> 1. Accepteu la invitació de GitHub al repo `adridece/datathon-bateria-equip`.
> 2. Seguiu la guia pas a pas `docs/GUIA_EQUIP.md` (instal·lar Python 3.11 i Git, clonar, entorn, setup).
>    Al final, `python -m src.evaluate agents/estandard_lp` us ha de donar `score: 6.08`.
> 3. Llegiu `docs/EQUIP.md` (com treballem i què fa cadascú) i `docs/CONTEXT.md` (el repte resumit).
> 4. Obriu el vostre assistent de codi DINS la carpeta del projecte i enganxeu-li el missatge que us
>    toca (més avall).
>
> **Repartiment:**
> - **Adrià:** dashboard en temps real (`dashboard/`)
> - **Ivan:** agent final perfecte i robust + imprevistos (`agents/`, `tests/`). Només ell envia a la web.
> - **Jesús:** anàlisi de dades i gràfics per a la presentació (`notebooks/`, `docs/figures/`)
> - **Martí:** presentació i guió (`presentacio/`)
>
> **Branques:** cadascú treballa a la seva branca (`dashboard`, `agent`, `analisi`, `presentacio`); el primer cop
> feu `git fetch` i `git checkout <la-vostra-branca>`. Explicat pas a pas a `docs/GUIA_EQUIP.md` (secció 5).
>
> **Normes:** `git pull origin main` abans de començar, `git push` sovint, només toqueu la vostra carpeta, apunteu
> les decisions a `docs/DECISIONS.md` i els resultats a `docs/DIARI.md`. Mai pugeu la clau d'API ni
> el PIN.
> La clau d'OpenCode és al Discord: poseu-la al vostre fitxer `.env` (copieu `.env.example`).

---

## 2) Missatge per a la IA de l'IVAN

```
Ets el meu assistent en aquest projecte de la Datathon FME 2026. Abans de res, llegeix AGENTS.md i
després docs/CONTEXT.md, docs/DECISIONS.md, docs/DIARI.md, docs/EQUIP.md, docs/RISCOS.md i
docs/GUIA_EQUIP.md. Explica'm amb paraules senzilles on estem (no sé gaire de res) i, abans de
canviar cap fitxer, proposa'm un pla.

El meu bloc: l'AGENT FINAL, perfecte i sense errors. Treballa només a agents/ i tests/.
1. Copia agents/estandard_lp a agents/estandard_robust i fes-lo indestructible, resolent els riscos R1, R2, R3 i
   R8 de docs/RISCOS.md: try/except al LP amb una estratègia de reserva, neteja de NaN i llistes buides,
   límit de descàrrega quan el consum net previst sigui < 500 kW, i prova de sensibilitat de co2_ref/preu_ref.
2. Crea proves automàtiques a tests/ (obs amb NaN, llista de 1 valor, SOC a 0 i a 2000, salts de
   timestamp, temps total < 10 s per a 2.016 hores) i un script per executar-les.
3. Ajusta el paràmetre "terminal" i altres amb validació creuada per mesos (src/evaluate.py), sense
   sobreajustar. Compara sempre amb l'oracle (python -m src.evaluate --oracle).
4. Cada versió s'avalua amb python -m src.evaluate agents/<carpeta> i es valida amb
   python scripts/make_submission.py agents/<carpeta>. Apunta els resultats a docs/DIARI.md i les
   decisions a docs/DECISIONS.md, i marca a docs/RISCOS.md els riscos resolts.
Recorda: només llibreries permeses, res de os/sys/eval, 0 infraccions, i explica-m'ho tot pas a pas.
```

---

## 3) Missatge per a la IA del JESÚS

```
Ets el meu assistent en aquest projecte de la Datathon FME 2026. Abans de res, llegeix AGENTS.md i
després docs/CONTEXT.md, docs/DECISIONS.md, docs/DIARI.md, docs/EQUIP.md i docs/GUIA_EQUIP.md.
Explica'm amb paraules senzilles on estem (no sé gaire de res) i, abans de fer res, proposa'm un pla.
Ajuda'm primer a deixar l'entorn funcionant seguint docs/GUIA_EQUIP.md.

El meu bloc: ANÀLISI DE DADES I GRÀFICS per a la presentació. Treballa només a notebooks/ i
docs/figures/. Fes servir les funcions que ja existeixen a src/data.py (load_hourly) i
src/evaluate.py (run, oracle, valid_split, load_agent) i el simulador oficial de starter_kit/.
1. notebooks/01_eda.ipynb: consum del campus, solar, preu i CO2 per hora del dia, dia de la setmana
   i mes; correlació preu-CO2; per què el CO2 és baix al migdia; hores amb consum net < 500 kW.
2. notebooks/02_resultats.ipynb: comparativa sense bateria / plantilla oficial / el nostre agent /
   oracle; un dia d'exemple amb el que fa la bateria hora a hora.
3. Frontera de Pareto CO2 vs cost: canvia els pesos w_co2 i w_cost (0/1 ... 1/0) del params.json en
   una còpia de l'agent i dibuixa estalvi de CO2 contra estalvi de cost.
4. Sensibilitat de la bateria: capacitat 1, 2, 4, 8 MWh i potència 250, 500, 1000 kW (el simulador
   CampusBatteryEnv accepta un diccionari spec). Quant estalvia cada MWh extra?
5. Passa-ho a món real: tones de CO2 i euros estalviats per any, i equivalències fàcils d'entendre.
Guarda cada gràfic en PNG a docs/figures/ amb un nom clar, títols i eixos en català i estil net.
Apunta les conclusions principals a docs/DIARI.md. Explica-m'ho tot pas a pas.
```

---

## 4) Missatge per a la IA del MARTÍ

```
Ets el meu assistent en aquest projecte de la Datathon FME 2026. Abans de res, llegeix AGENTS.md i
després docs/CONTEXT.md, docs/DECISIONS.md, docs/DIARI.md, docs/EQUIP.md, docs/RISCOS.md i el PDF
docs/repte/presentacio_repte.pdf. Explica'm amb paraules senzilles on estem (no sé gaire de res) i,
abans de fer res, proposa'm un pla. Ajuda'm primer a deixar l'entorn funcionant seguint
docs/GUIA_EQUIP.md.

El meu bloc: LA PRESENTACIÓ. Treballa només a presentacio/. El jurat valora la presentació, la
claredat del raonament, l'anàlisi de dades i la justificació de l'estratègia.
1. presentacio/GUIO.md: història de 5-7 minuts. Problema → què hem descobert a les dades (consum net
   ≥ 500 kW gairebé sempre, preu i CO2 coneguts 24 h abans) → per què això el converteix en un problema
   de programació lineal → MPC → resultat igual que l'oracle (òptim) → impacte real per a la UPC →
   dashboard en directe → què faríem amb més temps.
2. Estructura de diapositives (títol i contingut de cada una) i on aniran els gràfics del Jesús
   (docs/figures/) i el dashboard de l'Adrià.
3. presentacio/PREGUNTES.md: 15 preguntes difícils que pot fer el jurat amb la resposta (per què no
   machine learning? per què no aprenentatge per reforç? què passa si les previsions fallen? com sabeu
   que és òptim? què passa amb la degradació?...).
4. Explicació de la solució amb paraules molt senzilles, perquè qualsevol de nosaltres la pugui defensar.
5. Al final, revisa el README.md perquè quedi molt clar per al repo públic.
Tot en català, natural, com a estudiants de 2n de carrera. Explica-m'ho tot pas a pas.
```

---
---

# ACTUALITZACIÓ 14/11 (tarda): missatges per seguir avançant

## Missatge per al grup

> Actualització de l'equip:
> - **Branques a GitHub**: cadascú treballa a la seva (`agent` Ivan, `analisi` Jesús, `presentacio` Martí,
>   `dashboard` Adrià). El primer cop: `git fetch` i `git checkout <la-vostra-branca>`. Cada vegada abans de
>   començar: `git pull origin main`. Quan una cosa funcioni: Pull Request cap a `main` (guia, secció 5).
> - **Estil de codi**: codi en **anglès**, comentaris en **català**, curts i naturals. Simple, que sembli
>   nostre. Ja és a `AGENTS.md`, la vostra IA ho llegirà sola.
> - **Side challenges** (`docs/SIDE_CHALLENGES.md`): el dashboard va per la Tukey Commission (Adrià),
>   amb el Campus Nord real en 3D. Per a RawTree, algú hauria d'anar a l'estand a demanar accés i docs.
> - **Premis**: cal anar com a mínim a **una xerrada** per poder-los recollir.
> - **Xifres que ja tenim** (per a l'anàlisi i la presentació): score 6,08 = òptim teòric; ≈ 44 t CO₂ i
>   ≈ 96 k€ estalviats l'any; amb un 50 % d'error a les previsions el score només baixa a 5,68; amb 500 kW,
>   més de 4.000 kWh no aporta gaire.
>
> Enganxeu a la vostra IA el missatge que us toca (a sota).

## Per a la IA de l'IVAN (agent)
```
Llegeix AGENTS.md i després docs/EQUIP.md, docs/CONTEXT.md, docs/DECISIONS.md i docs/RISCOS.md.
Treballa a la branca "agent" (git checkout agent; git pull origin main). Codi en anglès,
comentaris en català, simple. Explica'm cada pas abans de fer-lo.
Objectiu: deixar l'agent final indestructible i congelat abans de les +14 h.
1. agents/estandard_robust (còpia de agents/estandard_lp) resolent R1, R2, R3 i R8 de docs/RISCOS.md:
   try/except al LP amb una estratègia de reserva, neteja de NaN i llistes buides, límit de
   descàrrega si el consum net previst és < 500 kW, i comprovar la sensibilitat de co2_ref/preu_ref.
2. Proves automàtiques a tests/ (obs amb NaN, llista d'1 valor, SOC a 0 i a 2000, salts de
   timestamp, temps < 10 s per a 2.016 h) que s'executin amb: python -m pytest tests
3. Compara sempre amb l'oracle (python -m src.evaluate --oracle) i valida amb
   python scripts/make_submission.py agents/estandard_robust. Apunta els resultats a docs/DIARI.md.
4. Quan estigui, fes una Pull Request cap a main i avisa el grup. No enviïs res a la web sense parlar-ho.
```

## Per a la IA del JESÚS (anàlisi de dades)
```
Llegeix AGENTS.md i després docs/EQUIP.md, docs/CONTEXT.md, docs/DECISIONS.md i docs/DIARI.md.
Treballa a la branca "analisi" (git checkout analisi; git pull origin main). Codi en anglès,
comentaris en català, simple. Explica'm cada pas, no en sé gaire.
Objectiu: un notebook net d'anàlisi de dades que expliqui el repte al jurat.
1. notebooks/01_eda.ipynb amb src/data.py (load_hourly): consum, solar, preu i CO2 per hora,
   dia de la setmana i mes; correlació preu-CO2; per què el CO2 és baix al migdia; hores amb
   consum net < 500 kW; qualitat de les dades (forats del comptador, consum de nit constant).
2. Cada gràfic amb un títol que digui la conclusió i una frase a sota. Estil: segueix
   docs/RECERCA_DASHBOARD.md secció 6 (paleta, sense emojis).
3. Desa els gràfics bons en PNG a docs/figures/ i apunta les 5 conclusions principals a
   docs/DIARI.md. Quan estigui, Pull Request cap a main.
(Els gràfics de resultats, mida de bateria i robustesa ja els fa el dashboard: no els repeteixis.)
```

## Per a la IA del MARTÍ (presentació)
```
Llegeix AGENTS.md i després docs/EQUIP.md, docs/CONTEXT.md, docs/DECISIONS.md, docs/DIARI.md,
docs/RISCOS.md i el PDF docs/repte/presentacio_repte.pdf.
Treballa a la branca "presentacio" (git checkout presentacio; git pull origin main).
Explica'm cada pas, no en sé gaire.
Objectiu: la presentació final (el jurat valora presentació, raonament, anàlisi i justificació).
1. presentacio/GUIO.md, de 5 a 7 minuts: el problema -> què vam descobrir a les dades (consum net
   >= 500 kW gairebé sempre; preu i CO2 coneguts 24 h abans) -> per què això és programació
   lineal -> MPC -> resultat igual que l'òptim (6,08) -> impacte real (44 t CO2 i 96 k€ l'any)
   -> robustesa (amb 50 % d'error, 5,68) -> mida de bateria recomanada -> demo del dashboard
   amb el campus en 3D (2 min) -> què faríem amb més temps.
2. presentacio/DIAPOSITIVES.md: títol i contingut de cada diapositiva, sobri i sense emojis.
3. presentacio/PREGUNTES.md: 15 preguntes difícils del jurat amb la resposta (per què no ML?
   per què no aprenentatge per reforç? què passa si les previsions fallen? com sabeu que és
   òptim? i la degradació? per què aquests pesos?...).
4. L'explicació de la solució amb paraules molt senzilles perquè tots la puguem defensar.
Tot en català natural, com a estudiants de 2n. Quan estigui, Pull Request cap a main.
```
