# Side challenges i Data Missions

## 1. Tukey Commission — Dashboard per prendre decisions ⭐ (encaixa amb el nostre dashboard)
**Repte:** dissenyar un dashboard que ajudi a prendre decisions sobre el repte principal. Format lliure.
**Criteris del jurat:**
- **Utilitat per decidir:** respon les preguntes del repte? dona base per decidir?
- **Adequació:** les representacions són les adequades per a les dades i les comparacions?
- **Coherència:** indicadors, gràfics i conclusions lliguen entre ells i amb les dades?
Hi ha 3 finalistes i només 1 guanyador.

**Pla (Adrià):** el `dashboard/` ja fet és la base. Cal orientar-lo a DECISIONS, no només a "ensenyar":
- [ ] Pestanya "Decisions i conclusions" al principi: 3-4 preguntes clares amb la resposta i el gràfic que la justifica
      (Quan carregar? Quina estratègia? Quina mida de bateria li convé a la UPC? Quant s'estalvia a l'any?)
- [ ] Cada gràfic amb una frase de conclusió a sota (coherència)
- [ ] Tipus de gràfic adequat: línies per a sèries temporals, barres per a perfils horaris, corba per a sensibilitat
- [ ] Mateixes xifres a tot arreu (sortides del simulador oficial) → coherència
- [ ] Fer-lo accessible per URL (p. ex. Streamlit Community Cloud) per ensenyar-lo al jurat

## 2. Tinybird / RawTree — "Best agentic use of RawTree"
**Repte:** un agent d'IA que fa servir RawTree per guardar, analitzar i actuar sobre dades. L'agent és el
protagonista (no un embolcall): decideix què ingerir, quines preguntes fer i què fer amb les respostes, a
través de la CLI, l'API, l'SDK o l'MCP de RawTree. Obert a tots els equips, sigui quin sigui el repte principal.
**Entrega:** un repo amb README i una demo curta. "Un projecte petit amb una gran història guanya."
**Onboarding:** a l'estand de RawTree (aneu-hi a buscar accés i documentació).

**Idea proposada:** un "operador energètic" autònom per a la UPC: ingereix a RawTree la telemetria del
campus (consum, solar, preu, CO₂), es fa preguntes ell mateix (anomalies del comptador, hores més netes de
demà, quant ha estalviat la bateria) i actua (genera el pla de càrrega de les properes 24 h i un informe).
Model de llenguatge: la clau d'API de la Datathon (`.env`).
**Nota:** aquest projecte SÍ és d'IA per definició; ha d'anar en un **repo separat** del repte principal.

## 3. Data Missions (punts i premis del cap de setmana)
- Escanejar el QR a cada missió (check-in, GitHub, xerrades, VR, Wikirace...) → nivells Data Explorer / Runner / Master.
- Reserves de VR oficials a partir de les 13:00 (les anteriors no valen).
- **Per recollir premis cal haver anat com a mínim a UNA xerrada.**
- Premis a l'estand el diumenge al final, **per ordre d'arribada**: aneu-hi d'hora.
