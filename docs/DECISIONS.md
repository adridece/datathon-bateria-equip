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

### D-017 · 14/11 · Adrià — Dashboard: eines de gestió i representació elèctrica del campus
- **Planificador "què passaria si":** recalcula el pla de 24 h al navegador amb programació dinàmica (nivells de 20 kWh)
  canviant preu, CO₂, reserva mínima, potència i prioritat. Sense canvis dona el mateix que l'agent (comprovat).
- **Informe PDF** d'una pàgina per a UPC Sostenible i **presentació guiada** de tot el dashboard per a la demo.
- **Mapa:** mode ampliat propi (funciona a tots els navegadors), zoom amb botons, comparació sense bateria.
- **Xarxa elèctrica:** la ubicació dels centres de transformació de la UPC no és pública. Representem una escomesa principal
  i 3 centres proposats amb un anell soterrat; el consum es reparteix segons el volum dels edificis que alimenta cada centre.
  La subestació del BSC (documentada) surt en gris perquè és un client a part. Detall i fonts: `docs/RECERCA_ELECTRICA_CAMPUS.md`.
- Noms dels edificis confirmats amb fonts de la UPC (ja no n'hi ha cap de deduït).

### D-018 · 14/11 · Adrià — Coherència del dashboard (revisió del Jesús)
- Totes les xifres del dashboard surten ara de `mpc_robust` (versió final). La corba de mida per a 1 MW queda bé
  (4.000 kWh i 1 MW: 11,84 punts, abans 11,12 amb mpc_lp, que descarregava més del que consumia el campus).
- El cost per tona de CO₂ és net: (inversió − estalvi en 15 anys) / tones. Si surt negatiu, la bateria es paga sola.
- 11 setmanes de validació (no 12) i "0 infraccions al test públic".
- El planificador mai proposa un pla pitjor que el de l'agent si el de l'agent compleix l'escenari (càlcul en salts de 10 kWh).
- La visió general comença a l'hora 0. Informe en una pàgina pròpia (`dashboard/report.html`) i presentació guiada amb portada i resum.

### D-019 · 14/11 · Adrià — 3D més llegible i reproducció contínua
- L'escomesa principal fa de nus: la xarxa hi entra pel sud (carrer), la bateria és a l'est i les plaques i els centres
  de transformació queden al nord, així els cables no es creuen. El consum viatja per l'anell soterrat fins a cada centre.
- Cada tipus de flux té el seu color (solar ambre, xarxa segons el CO₂, càrrega blau, descàrrega vermelló, consum pissarra)
  i cada centre de transformació porta una etiqueta.
- La reproducció avança de manera contínua (amb minuts) i interpola els valors entre hores. Velocitats: lenta, normal i ràpida.
- El mapa ampliat es col·loca sobre tota la pàgina i torna al seu lloc en tancar-lo. Cada secció s'obre a dalt de tot.
- Traiem la presentació guiada del dashboard (no aportava prou).

### D-020 · 14/11 · Adrià — Conclusions i decisions a la visió general (Tukey)
- La Tukey valora sobretot que el dashboard ajudi a decidir. A dalt de la visió general hi ha el bloc
  "Què concloem i què decidim": 5 decisions per a UPC Sostenible, cadascuna amb la xifra que la justifica
  i un botó que porta al gràfic on hi ha l'evidència.
- Les xifres es calculen de les mateixes dades del dashboard (no hi ha cap número escrit a mà).
- Decisions: control predictiu, horari de càrrega i descàrrega, ampliar a 3.000 kWh (retorn 9,4 anys),
  posar-la en marxa amb previsions de REE, i mantenir el límit de 500 kW (0 infraccions).

### D-021 · 14/11 · Adrià — Diagrama de caixa del CO₂ per hora (homenatge a Tukey)
- La mitjana per hora amagava la clau: a la mateixa hora el CO₂ canvia molt d'un dia a l'altre. A Estratègia hi ha
  un diagrama de caixa de Tukey per hora (77 dies), pintat segons què fa la bateria, i una conclusió calculada:
  a les 7 h el CO₂ va de 40 a 209 g/kWh i el 83 % dels dies l'hora més neta no és la de sempre.
- Justifica la decisió 01 (control predictiu i no un horari fix). És la gràfica que va inventar Tukey.
- Vista inicial del 3D: la càmera mira cap al punt durant el vol i no fa cap salt en acabar.

### D-022 · 14/11 · Adrià — Recerca per a la Tukey i què hi posem (i què no)
Hem fet una recerca sobre què guanya concursos de visualització (Iron Viz, Information is Beautiful) i quines eines
de Tukey té sentit fer servir. Els tres criteris del jurat (útil per decidir, gràfics adequats, coherència) coincideixen
amb els d'Iron Viz: guanya un camí clar pregunta → evidència → decisió, amb tots els números iguals a tot arreu.
- **Amb bateria i sense** (visió general): compra a la xarxa amb i sense bateria i CO₂ evitat acumulat de la setmana.
  És la pregunta que es fa UPC Sostenible: què hi guanyem? Mateixa fórmula que el calendari i el HUD.
- **Caixes amb osca** (McGill, Tukey i Larsen, 1978) i resum de cinc nombres a cada hora.
- **Quan compensa més**: CO₂ evitat de cada dia contra la diferència de CO₂ dins del dia, amb la recta resistent de
  Tukey. Conclusió: com més variable sigui la xarxa (més renovables), més val la bateria.
- **Polit de medianes** (Tukey, EDA cap. 11) de la taula dia × hora amb els 77 dies reals. Primer el vam fer amb mitjanes
  per dia de la setmana i deia que l'hora ho explicava gairebé tot, cosa que contradeia el diagrama de caixa; amb els dies
  reals surt 18 % hora, 46 % nivell del dia i 36 % forma del dia, coherent amb la resta.
- Traiem de la visió general els dos gràfics petits que repetien Estratègia.
- No hi posem: més 3D amb valors, més KPI, pastissos, xat amb IA, dades en directe d'APIs ni pàgines noves.

### D-023 · 14/11 · Adrià — El 3D en temps real és el centre, sense repeticions ni competició
- **El dashboard és per a UPC Sostenible, no per a la competició.** Traiem el leaderboard, la puntuació, el test públic i
  les infraccions del concurs. Tot es diu en tones de CO₂ i euros; la robustesa és "part de l'estalvi que es conserva" i les
  estratègies es comparen en t/any i €/any.
- **El 3D en temps real és la secció principal** i s'obre primer, reproduint-se sol (si el navegador no demana menys
  animació). A sota hi ha el pla de 24 h i els avisos, que segueixen l'hora que es reprodueix.
- **Cada hora del pla explica el seu motiu** en passar-hi el ratolí, i una franja diu com de segura és la decisió:
  refem el pla 20 vegades amb el mateix model d'error que a Fiabilitat (l'error creix amb l'horitzó) i comptem quantes
  vegades es manté (carregar, descarregar o esperar). Sense error coincideix amb l'agent en un 83-100 % de les hores.
- **Res repetit:** fora el 3D petit i la targeta Bateria de la visió general (repetien el panell del 3D), fora les respostes
  de dalt d'Estratègia i Fiabilitat (repetien les decisions) i fora els petits múltiples de setmanes (repetien el calendari).
  La visió general passa a dir-se Conclusions. Els KPI de puntuació i infraccions es canvien per energia moguda i cicles per any.

### D-024 · 14/11 · Adrià — Panell en directe sempre visible i planificador just
- El panell amb les dades de l'hora (bateria, compra, CO₂, preu, estalvi i el motiu de la decisió) es veu sempre sobre
  el 3D, en petit i a baix a l'esquerra. Abans només sortia a pantalla completa i el 3D no s'entenia sol.
- Planificador: el pla nou ha d'acabar el dia amb almenys la mateixa càrrega que el de l'agent. Si no, buidava la bateria
  al final "gratis" i semblava que millorava l'agent (257 contra 237 kg); ara surten iguals (264 i 263 kg).
  La reproducció s'atura en entrar-hi perquè l'escenari no es mogui mentre es prova.
- Estratègies amb noms per a UPC: "Horari fix" i "Control predictiu".

### D-025 · 14/11 · Adrià — Panell "Ara mateix", rellotge del dia i semàfor per al campus
- El panell de dades sobre el 3D tapava el campus i es veia malament en petit. Ara hi ha una columna al costat del 3D,
  "Ara mateix", i el panell flotant només surt a pantalla completa.
- **Rellotge de 24 h**: a fora, el CO₂ de la xarxa de cada hora del dia; a dins, què fa la bateria (blau carrega,
  vermelló descarrega, més llarg com més potència); l'agulla avança amb la reproducció i al centre hi ha la càrrega.
  Es veu d'un cop d'ull que carrega a les hores netes i descarrega a les brutes.
- **Semàfor per al campus** (idea d'Electricity Maps i Octopus): compara el CO₂ d'ara amb les properes 24 h i diu si és bon
  moment per fer servir consums que es poden moure (equips, càrrega de cotxes...) o a quina hora serà més neta.
  És una decisió nova per a UPC Sostenible, més enllà de la bateria.
- **Sense salts**: cada hora té una consigna; en començar l'hora els valors passen al nou en poc temps i suau, i la
  càrrega de la bateria avança contínua dins l'hora (abans mostrava la del final de l'hora i podia dir "100 %" carregant).
  El 3D, el rellotge i les xifres fan servir els mateixos valors.
- Disposició: el calendari ocupa tota l'amplada i un clic obre aquell dia al 3D; barres d'estratègia de gruix fix;
  la fiabilitat amb eix del 80 al 100 % i sense àrea (l'eix no comença a zero).

### D-026 · 14/11 · Adrià — Cada setmana comença al 50 % i la càrrega de la bateria, ben visible
- Fins ara el dashboard simulava les 11 setmanes de validació seguides: cada setmana començava amb la càrrega amb què
  acabava l'anterior, tot i que estan separades per mesos. Ara cada setmana és una simulació a part que comença al 50 %,
  com fa el simulador oficial (`soc_init: 0.5`), i les previsions no passen d'una setmana a la següent
  (`src/replay.py: replay_weeks`, `dashboard/analysis.py: oracle_weeks`).
- Resultat de validació setmana a setmana: 6,41, igual que l'òptim teòric calculat igual (6,41) i més a prop del 6,43
  del test públic. Totes les xifres del dashboard s'han recalculat (`python scripts/build_dashboard_data.py`).
- La càrrega passa a ser protagonista: bateria gran a dalt del panell "Ara mateix" (percentatge, kWh, si carrega o
  descarrega i en quant de temps s'omplirà o es buidarà) i corba de càrrega a sota del pla de 24 h.
  El centre del rellotge ara mostra l'hora.

### D-027 · 14/11 · Adrià — Sense reproducció automàtica, mides fixes i gràfic de Conclusions més clar
- En obrir la pàgina no es reprodueix sol: l'usuari decideix quan començar.
- Res canvia de mida quan canvia el text en directe: el panell "Ara mateix" té cada bloc d'alçada fixa (sense barra de
  desplaçament), els números fan servir xifres d'amplada fixa i el rellotge de dalt té amplada fixa. Comprovat reproduint:
  cap bloc canvia de mida.
- El gràfic "Què guanya el campus amb la bateria" ara mostra directament la diferència: cada hora, quant més (amunt) o
  menys (avall) compra el campus per tenir la bateria, pintat amb el CO₂ de la xarxa. Les dues línies d'abans gairebé es
  tapaven i les etiquetes es tallaven.

### D-028 · 14/11 · Adrià — Vista Rendiment, historial, informe de 2 pàgines i nom del repte
- **Rendiment** (abans Fiabilitat): taula setmana a setmana amb CO₂ i € estalviats, % de CO₂ i de factura, part de
  l'òptim (mateixa ponderació 70/30 i òptim calculat setmana a setmana), el que faria un horari fix i els cicles.
  Es pot descarregar en CSV i un clic obre la setmana al 3D. La conclusió diu per què unes setmanes rendeixen més
  (la variació del CO₂ dins del dia), amb la xifra.
- **Historial**: `python scripts/build_dashboard_data.py` afegeix una línia a `dashboard/data/history.json` cada cop que
  canvien els resultats (CO₂ i € per any, part de l'òptim, pitjor setmana, infraccions). Serveix per seguir el sistema
  al llarg del temps i entre versions de l'agent.
- **Decisió 05 corregida**: la infracció del simulador és demanar més de 500 kW o més energia de la que hi cap o en queda,
  no un límit de consum a la xarxa. Ara ho diu així.
- **Informe** en 2 pàgines A4: resum, 6 decisions amb la xifra que les justifica i 4 gràfics; i rendiment setmanal,
  historial, com funciona el control, com seguir-lo i supòsits. S'ha arreglat el gràfic d'estratègies (sortia buit).
- El nom que surt és el del repte, **UPC Sostenible**, amb "Bateria del Campus Nord" a sota.
- El semàfor queda centrat a la seva caixa.

### D-029 · 14/11 · Ivan — Les dues versions generalitzen: no les toquem
Comprovat amb `tests/check_generalization.py` (veure DIARI): validació creuada per mesos, 10 tests simulats com l'oficial,
error a les previsions, talls del comptador, final de simulació, SOC als límits i sensibilitat de params.json.
Cap problema real: 0 infraccions sempre, a 0,002 de l'òptim de mitjana i estables davant canvis dels paràmetres.
`mpc_robust` i `mpc_test_weights` empaten (+0,0001), així que per al jurat són dues opcions igual de bones.
El que més pesa al test privat són els talls del comptador: `mpc_lp` hi perdria fins a 0,2 punts, les nostres versions no.
**Decisió:** les dues versions queden congelades tal com estan. Si el test privat té talls, `mpc_robust`/`mpc_test_weights` són clarament millors que `mpc_lp`.

### D-030 · 14/11 · Ivan — Agent per al Mode Difícil (`agents/hard_mpc`)
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

### D-031 · 14/11 · Ivan — Mode Difícil amb models de previsió (`agents/hard_ml`)
Mateix LP que `hard_mpc`, però el consum i el preu els corregeix un model LightGBM entrenat amb el train: el model no prediu
el valor sinó l'error de la previsió senzilla, així si no es pot carregar al servidor l'agent funciona igual (sense la millora).
Els models es guarden en text (`.txt`) perquè no depenguin de la versió de LightGBM.
El CO₂ és el que més pesa i el que pitjor es pot predir amb 3 setmanes de dades per mes: cap model millora la previsió senzilla.
**Pendent:** enviar `hard_mpc` per saber quin score públic correspon al nostre 19,9 local abans de decidir res més.

### D-032 · 14/11 · Ivan — `hard_ml`: els models només corregeixen les hores properes
Substitueix la part de models de D-031. Hem mesurat que el que decideix el score és l'hora actual (consum i solar) i el mercat de
les hores +3..+7; més lluny, els models no milloren la previsió senzilla. Per tant: un model per sèrie, entrenat i aplicat només a
les hores properes (`near_hours` a params.json), i previsió senzilla per a la resta. Marge de descàrrega 0,96.

### D-033 · 14/11 · Ivan — Agent final del Mode Difícil (`agents/hard_final`)
Substitueix `hard_ml` com a candidat principal. Mateix LP + MPC, amb 5 millores validades a dues validacions independents
(veure DIARI 14/11 vespre): previsió solar del 1r dia, marge de descàrrega per hora segons l'error real, el pla també
compta amb aquest marge, historial del train al principi de cada setmana, i previsió de CO₂/preu a +3/+4 h amb la forma
d'ahir ancorada. Models: 5 llavors (mitjana) per ser més estables. Es reentrena amb `python scripts/train_hard_final.py`.
**Per què no LightGBM per a tot:** a partir de cert punt els models no milloren la previsió senzilla i afegeixen soroll.

### D-034 · 14/11 · Ivan — `hard_final` v2: excedent solar i preu a totes les hores
Amb excedent solar carreguem pensant en el cas de més sol (l'error de carregar de més és comprar una mica de xarxa a l'hora
més barata; el de carregar de menys és perdre energia gratis). El model de preu s'aplica a totes les hores. Validació: 19,22.

### D-035 · 14/11 · Adrià — Vista inicial al començament de la setmana i selector de setmanes propi
- "Vista inicial" (o la tecla 0) atura la reproducció, torna a la primera hora de la setmana i posa la càmera a lloc.
- El desplegable natiu de setmanes es veia diferent a cada sistema (Mac, Windows, Linux). Ara és un selector propi amb el
  mateix aspecte a tot arreu: llista amb les 11 setmanes i el CO₂ que estalvia cadascuna, la triada ressaltada, i es pot fer
  servir amb el teclat (fletxes, Enter, Esc). El `<select>` queda amagat perquè la resta del codi segueixi igual.

### D-036 · 14/11 · Adrià — `agents/hard_v3`: model directe de CO₂ a +3..+12 h
Anàlisi a fons del Mode Difícil amb un banc de proves honest (models entrenats sense les setmanes avaluades; F0, F1 i F2
reservada) i l'òptim teòric calculat igual (F0 20,28 · F1 18,75):
- `hard_final` és al 92,7 % de l'òptim. Amb totes les previsions perfectes el mateix LP faria 20,18 (F0): **tot el que falta
  és error de previsió**, no el mètode. El que més pesa: CO₂ +0,64 (només +3..+5 h ja +0,29), consum net de l'hora actual +0,51,
  preu +0,27. Els marges de descàrrega ja són als millors valors.
- El rècord de la web (24,10) és ~97 % de l'òptim; el sostre de la web és ~24,7–24,8 (22,96 / 0,927). **25 no s'hi arriba**
  ni sabent el futur.
- Millora trobada: un model directe de CO₂ (LightGBM, la corba de 48 h de CO₂ i 24 h de preu relativa a l'última hora coneguda)
  barrejat meitat i meitat amb la previsió de `hard_final` a les hores +3..+12. Error −5/−6 %; score F0 +0,08, F1 +0,07,
  F2 +0,17, 0 infraccions. Descartat: preu (+0,02), horitzó fins a +18 (empitjora F2), pes 0,7 (no millora les tres).
**Decisió:** `hard_v3` és el nou candidat del Mode Difícil (esperat ~23,1 a la web). Es reentrena amb `python scripts/train_hard_v3.py`.

### D-037 · 14/11 · Adrià — `hard_v3`: detecta si la irradiància és de l'hora actual
La web diu que `obs` porta "les lectures de la darrera hora de meteo.csv", però no si és l'hora que comença o la que acaba
d'acabar. Amb la irradiància de la mateixa hora la solar es preveu gairebé exacta (error 33 kW, correlació 0,995) i amb la de
l'hora anterior no (192 kW). En lloc d'endevinar-ho, l'agent ho comprova sol: compara la solar de l'hora passada amb la
irradiància que rep ara i amb la de l'hora anterior, i es queda amb la que encaixa (després de 6 hores de sol).
Si és de l'hora actual, la solar d'ara = 1,629 × irradiància (ajustat amb el train) i el marge de seguretat baixa al 70 %.
Banc honest (F0 / F1 / F2): si la web dona l'hora passada, igual que abans (18,88 / 17,42 / 17,92: no hi perdem res);
si dona l'hora actual, 19,02 / 17,55 / 18,20 (+0,14 / +0,13 / +0,28).
També provat i descartat (no milloren totes les validacions): valor de l'energia al final del pla, decisió amb escenaris,
variables d'ahir i de fa una setmana a l'hora objectiu per al CO₂.

### D-038 · 14/11 · Adrià — Revisió crítica: errors trobats a les dades, a l'agent i a una decisió nostra
- **Error nostre (D-026):** vam fer que cada setmana del dashboard comencés al 50 %. Les FAQ oficials diuen el contrari: la
  bateria comença al 50 % només a l'inici de tota la simulació i **no es reinicia mai** (ni cada dia ni cada setmana).
  Es desfà: el dashboard torna a la simulació contínua. El 6,41 que "s'acostava més al test públic" era casualitat.
- **El comptador es congela de nit:** de ~22 h a ~6 h el comptador repeteix el mateix valor cada 5 minuts (el 29,5 % de les
  hores del train són trams plans de 6 h o més; l'85 % de les hores de nit tenen el mateix consum que l'anterior).
  El consum real de nit no el coneixem. L'agent ja en treu profit sense trampes (marge de nit de 2,5 kW).
- **Canvi d'hora:** les dades són en hora local (el migdia solar passa de 12,3 h a l'hivern a 13,0 h a l'estiu) i els canvis
  d'hora (26/10 i 29/03) cauen a setmanes de test. Abans, una hora que falta feia esborrar l'historic. Hem provat les
  tres opcions simulant-ho: esborrar 18,96 · mantenir-lo desalineat 18,90 (pitjor!) · **repetir l'hora que falta 19,00**.
  `hard_v3` ara repeteix l'hora que falta i, si una hora arriba dues vegades, substitueix el valor. Sense canvi d'hora no canvia res.
  Els agents ja enviats (`hard_final`, `hard_ml`) no es toquen.
- **Penalització:** les FAQ diuen −1 punt per infracció; el simulador del starter kit en resta 0,2. Tots els nostres agents en fan 0.
- **Banc de proves:** alguns paràmetres de l'Ivan es van triar mirant F0 i F1, així que aquestes dues validacions són una mica
  optimistes. La més honesta és F2: `hard_v3` hi és al 88,6 % de l'òptim (F0 93,1 %, F1 92,9 %).
