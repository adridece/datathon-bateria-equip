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

### D-009 · 14/11 · Ivan — Agent robust (`agents/mpc_robust`)
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
