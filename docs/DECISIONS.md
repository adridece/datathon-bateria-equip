# Diari de decisions

Cada decisió important va aquí: **què**, **per què**, **alternatives** i **qui**.
Format: `D-XXX · data · autor`. Les noves, a sota de tot. No esborrem decisions antigues: si en
canviem una, n'escrivim una de nova que digui "substitueix D-XXX".

---

### D-001 · 14/11 · equip — Repte escollit: bateria UPC Sostenible
Controlar una bateria de 2 MWh hora a hora per reduir CO₂ (70 %) i cost (30 %).

### D-002 · 14/11 · equip — Organització del projecte
- Un repo **privat** per treballar tots (amb tot: dades, notebooks, proves).
- Un repo **públic** final, generat amb `scripts/export_public.py`, només amb el que s'entrega.
- Python 3.11 (el més probable al servidor i funciona a Windows i Mac).
- Dades de train dins del repo privat com a zip (13 MB) i `scripts/setup.py` per descomprimir-les.
- Fer servir sempre el simulador **oficial** (`starter_kit/environment.py`) per avaluar, no un de propi.

### D-003 · 14/11 · equip — Enfocament principal: MPC amb programació lineal
**Per què:** la puntuació és lineal en l'energia importada. Si l'energia descarregada sempre es consumeix
(consum net ≥ 500 kW el 99,5 % del temps), cada kWh importat a l'hora *t* val
`w_t = 0,7·co2_t/CO2_ref + 0,3·preu_t/preu_ref`. Amb els 24 valors futurs coneguts, minimitzar
`Σ w_t·(càrrega_t − descàrrega_t)` amb les restriccions de SOC és un LP petit (48 variables).
Cada hora el resolem (`scipy.optimize.linprog`, HiGHS), apliquem només la primera hora i repetim
(*rolling horizon*). Tècnica vista a IA (cerca/planificació) i optimització.
**Alternatives descartades (de moment):** regles fixes per hores (la plantilla fa 0,94 punts),
aprenentatge per reforç (massa lent d'entrenar i menys garantit que l'òptim exacte del LP).
**Resultat:** 6,08 al VALID; l'oracle (LP de tot el període sabent-ho tot) també fa 6,08.

### D-004 · 14/11 · equip — Normalització dels pesos
`CO2_ref` i `preu_ref` = mitjanes ponderades pel consum al train (0,0921 kg/kWh i 0,1568 €/kWh).
Al test seran una mica diferents, però només importa la proporció entre els dos.

### D-005 · 14/11 · equip — Seguretat: 0 infraccions
Sempre retallem la consigna amb el *safety clamp* oficial abans de retornar-la (amb marge 1e-4).

### D-006 · 14/11 · Adrià — Dashboard amb Streamlit + animació pròpia
**Per què:** Streamlit és Python (el que ja fem servir) i funciona a Mac i Windows. L'animació va en
SVG + JavaScript dins d'un sol fitxer, sense dependre d'internet, perquè no falli en directe a la presentació.
Totes les xifres surten del simulador oficial (`src/replay.py`), així són coherents amb el leaderboard.
També serveix per al side challenge de la Tukey Commission (veure `docs/SIDE_CHALLENGES.md`).

### D-007 · 14/11 · equip — No enviem encara a la web
L'agent `mpc_lp` està validat a la web (dry-run correcte, 0 infraccions, 1,55 ms/hora). Decidim esperar
abans de gastar un enviament al leaderboard.

### D-008 · 14/11 · Adrià — Dashboard orientat a decisions (side challenge Tukey)
Pestanya inicial "Decisions" amb 4 preguntes (estratègia, quan carregar, mida de bateria, robustesa),
cadascuna amb la resposta, el gràfic que la justifica i una conclusió. Totes les xifres surten de la mateixa
simulació. Resultats clau: MPC = òptim (gap 0 %); amb 50 % d'error a les previsions el score només baixa de 6,08 a 5,68;
amb 500 kW, més de 4.000 kWh no aporta gaire; ≈ 44 t CO₂ i ≈ 96 k€ estalviats per any (estimació).

### D-009 · 14/11 · Adrià — Dashboard v2: disseny propi i campus real en 3D
- **Disseny:** fons paper, un sol color d'accent (el nostre agent), escenaris de comparació en gris, colors
  d'energia aptes per a daltonisme (Okabe-Ito), CO₂ en una rampa d'un sol to, IBM Plex, cap emoji. Tot surt de
  `dashboard/style.py`, així un concepte té sempre el mateix color (coherència, criteri de la Tukey).
- **Estructura:** 5 pàgines, cadascuna una pregunta → resposta amb xifra → gràfic → supòsits.
- **3D:** edificis reals del Campus Nord (OpenStreetMap), three.js incrustat dins l'HTML perquè funcioni sense
  internet i a Windows. La ubicació de la bateria i de l'escomesa és una suposició (no està publicada) i es diu a la
  mateixa escena.
- Fonts de la recerca: `docs/RECERCA_DASHBOARD.md` i `docs/RECERCA_CAMPUS3D.md`.

### D-010 · 14/11 · equip — Primer enviament al leaderboard (substitueix D-007)
Enviem `agents/mpc_lp` amb el nom d'equip **La Datoneta**. Resultat públic: **6,43** (CO₂ −5,97 %, factura −7,5 %,
0 infraccions). La validació local donava 6,08: el nostre pseudo-test és una bona estimació del test real.
El PIN de l'equip el guarda l'Adrià (mai al repo).

### D-011 · 14/11 · Adrià — El dashboard passa a ser una web feta a mida (substitueix D-006)
Streamlit sempre semblava "una eina interna". Fem una web pròpia (HTML + CSS + JS, gràfics amb D3 i 3D amb three.js),
estil sala de control fosca, amb el campus real en 3D a la portada i les decisions a sota. Funciona sense internet
amb `python scripts/serve_dashboard.py`. Les xifres es generen amb `scripts/build_dashboard_data.py` a partir del
simulador oficial, així segueixen sent coherents amb el leaderboard.

### D-012 · 14/11 · Adrià — Regles de disseny del dashboard en un sol document
Les regles concretes del dashboard (estructura d'app d'una pantalla, KPI, gràfics, tokens del tema clar, moviment, 3D i
interacció) són a `docs/REGLES_DASHBOARD.md`. Canvis respecte a la recerca: formes rodones amb escala de radis
(6/10/14/20 px i píndola) en lloc de 4–6 px, tema clar (el fosc no es llegia bé), i corbes d'animació
`cubic-bezier(.23,1,.32,1)` / `(.77,0,.175,1)` amb durades curtes.

### D-013 · 14/11 · Adrià — Dashboard com a app clara amb targetes rodones (substitueix l'estil fosc de D-011)
La versió fosca es llegia malament. Passem a una app d'una sola pantalla: barra lateral amb 5 vistes, tema clar i càlid,
targetes rodones, un sol color d'accent per al nostre agent i colors d'energia aptes per a daltonisme. El 3D és una maqueta
blanca ben il·luminada. Animacions curtes en entrar a cada vista (xifres que compten, barres i línies que es dibuixen).
Normes a `docs/REGLES_DASHBOARD.md`.
### D-014 · 14/11 · Ivan — Agent robust (`agents/mpc_robust`)
mpc_lp + no descarregar més del consum net de l'hora anterior (talls del comptador: FULL 5,65 → 5,67)
+ neteja de NaN/llistes buides + regla de reserva si el LP falla (sola fa 4,68 al VALID).
Provat: el paràmetre `terminal` i `co2_ref/preu_ref` ±20 % no canvien el score → no els ajustem.

### D-015 · 14/11 · equip — El 6,43 és el sostre: no té sentit seguir ajustant l'agent per al score
Mesurat sense arrodonir (validació de 12 setmanes): `mpc_robust` = 6,0833 i l'òptim teòric (que sap tot el futur,
també el consum) = 6,0834. Provat i descartat: horitzó de 48 h (persistència d'avui per a demà) i pesos amb la proporció
CO₂/cost del test (71.816 kg / 118.746 €): canvis < 0,001.
Al leaderboard, el nostre 6,43 exacte és 0,7·4.289,4/71.816 + 0,3·8.907,86/118.746,34 = **6,4315**. Per sortir 6,44
caldrien 6,435: 35 vegades més que tot el marge que queda fins a l'òptim. Tots els equips de dalt són al mateix sostre
i el simulador arrodoneix a 2 decimals, per això l'ordre el decideix l'hora d'enviament.
**Decisió:** l'agent queda congelat (`mpc_robust`). El temps va al dashboard, a la presentació i als side challenges.

### D-016 · 14/11 · equip — El rànquing públic té soroll: triem dues versions òptimes diferents per al jurat
Un equip ha tret 6,44 al públic. Simulant la meitat pública amb la nostra validació, variants pràcticament igual de bones
en total (6,078–6,083) es separen fins a 0,1 punts segons quines hores compten. Per tant, el 6,44 no implica un agent millor
i perseguir el públic seria sobreajustar. Com que el jurat puntua al test privat les 2 trameses que triem, triem dues versions
òptimes però diferents (més opcions de quedar a dalt):
1. `agents/mpc_robust` (gestiona fallades del comptador).
2. `agents/mpc_test_weights`: el mateix codi amb la proporció CO₂/€ del test públic (71.816 kg / 118.746 €), que és la
   ponderació exacta del test. Validació 6,08 · train complet 5,67 · 0 infraccions.

### D-017 · 14/11 · Ivan — Les dues versions generalitzen: no les toquem
Comprovat amb `tests/check_generalization.py` (veure DIARI): validació creuada per mesos, 10 tests simulats com l'oficial,
error a les previsions, talls del comptador, final de simulació, SOC als límits i sensibilitat de params.json.
Cap problema real: 0 infraccions sempre, a 0,002 de l'òptim de mitjana i estables davant canvis dels paràmetres.
`mpc_robust` i `mpc_test_weights` empaten (+0,0001), així que per al jurat són dues opcions igual de bones.
El que més pesa al test privat són els talls del comptador: `mpc_lp` hi perdria fins a 0,2 punts, les nostres versions no.
**Decisió:** les dues versions queden congelades tal com estan. Si el test privat té talls, `mpc_robust`/`mpc_test_weights` són clarament millors que `mpc_lp`.

### D-020 · 14/11 · Ivan — Agent per al Mode Difícil (`agents/hard_mpc`)
Al Mode Difícil ja no val la idea del mode estàndard: només sabem 3 h de mercat i la bateria (1.500 kW) pot descarregar més
del que consumeix el campus. Mantenim LP + MPC de 24 h, amb dos canvis:
1. **Previsions.** Preu i CO₂: mitjana dels últims 3 dies a la mateixa hora barrejada amb el perfil del train del mateix mes
   (feiner / cap de setmana), corregida amb el nivell de les 3 h que sí sabem. Consum: perfil del train per dia de la setmana i
   hora, escalat amb les últimes mesures. Solar: la dels últims dies a la mateixa hora, corregida segons com de clar està avui.
2. **La xarxa dins del LP** (`xarxa ≥ consum − solar + bateria`, `xarxa ≥ 0`): el pla aprofita l'excedent solar gratuït i no
   descarrega més del que es consumirà. A l'hora actual descarreguem com a molt el 92 % del consum net previst (marge d'error).
**Alternatives:** adaptar `mpc_robust` sense previsions (10,50) o models LightGBM per a les previsions (més feina i risc de
sobreajustar; queda com a millora possible: el marge fins a l'òptim és de 2,5 punts).
Només hi ha 2 enviaments cada 4 h: validar sempre en local i amb la Validació Ràpida abans d'enviar.

### D-021 · 14/11 · Ivan — Mode Difícil amb models de previsió (`agents/hard_ml`)
Mateix LP que `hard_mpc`, però el consum i el preu els corregeix un model LightGBM entrenat amb el train: el model no prediu
el valor sinó l'error de la previsió senzilla, així si no es pot carregar al servidor l'agent funciona igual (sense la millora).
Els models es guarden en text (`.txt`) perquè no depenguin de la versió de LightGBM.
El CO₂ és el que més pesa i el que pitjor es pot predir amb 3 setmanes de dades per mes: cap model millora la previsió senzilla.
**Pendent:** enviar `hard_mpc` per saber quin score públic correspon al nostre 19,9 local abans de decidir res més.

### D-022 · 14/11 · Ivan — `hard_ml`: els models només corregeixen les hores properes
Substitueix la part de models de D-021. Hem mesurat que el que decideix el score és l'hora actual (consum i solar) i el mercat de
les hores +3..+7; més lluny, els models no milloren la previsió senzilla. Per tant: un model per sèrie, entrenat i aplicat només a
les hores properes (`near_hours` a params.json), i previsió senzilla per a la resta. Marge de descàrrega 0,96.

### D-023 · 14/11 · Ivan — Agent final del Mode Difícil (`agents/hard_final`)
Substitueix `hard_ml` com a candidat principal. Mateix LP + MPC, amb 5 millores validades a dues validacions independents
(veure DIARI 14/11 vespre): previsió solar del 1r dia, marge de descàrrega per hora segons l'error real, el pla també
compta amb aquest marge, historial del train al principi de cada setmana, i previsió de CO₂/preu a +3/+4 h amb la forma
d'ahir ancorada. Models: 5 llavors (mitjana) per ser més estables. Es reentrena amb `python scripts/train_hard_final.py`.
**Per què no LightGBM per a tot:** a partir de cert punt els models no milloren la previsió senzilla i afegeixen soroll.

### D-024 · 14/11 · Ivan — `hard_final` v2: excedent solar i preu a totes les hores
Amb excedent solar carreguem pensant en el cas de més sol (l'error de carregar de més és comprar una mica de xarxa a l'hora
més barata; el de carregar de menys és perdre energia gratis). El model de preu s'aplica a totes les hores. Validació: 19,22.
