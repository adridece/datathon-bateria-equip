# Recerca: com arriba l'electricitat al Campus Nord

*Data: 14/11/2026. Complementa `docs/RECERCA_CAMPUS3D.md`. Les dades surten de `scripts/build_campus_json.py` → `dashboard/static/campus_nord.json` (`energy_assets`).*

## 0. Resum en 6 línies

1. **Noms dels edificis: ja no n'hi ha cap de deduït.** A4, A5, A6 i B6 surten de l'etiqueta `addr:housenumber` d'OSM i de la llista oficial d'edificis de la UPC. B3 és l'ETSETB i B6 és la FIB (ho diuen les dues escoles). Els 4 pavellons d'1 planta no tenen nom públic, així que els anomenem "Pavelló entre A1 i A2", etc.
2. **A OSM no hi ha cap transformador ni subestació mapejats dins del campus.** Ho hem comprovat al fitxer en brut. Overpass ha tornat a donar error 502.
3. **L'única infraestructura elèctrica documentada és la del BSC**, que no és la de la UPC: una subestació soterrada de 110/25 kV amb 2 transformadors de 20/25 MVA, per a 20 MW.
4. **La UPC no publica on té els seus centres de transformació (CT) ni quants punts de subministrament té al Campus Nord.** No hem trobat cap document públic que ho digui.
5. Per tant, la xarxa de la UPC que dibuixem és **una proposta raonada**: una escomesa de mitja tensió (MT) amb un CT als aularis, més 3 CT interns (mòduls B/C/D, Omega i Vèrtex). Totes porten `confidence: "proposta"`.
6. La **bateria** va al costat de l'escomesa principal, en l'espai obert entre el poliesportiu i el C/ Jordi Girona. Les raons són al §4.

## 1. Vocabulari mínim

- **Escomesa**: punt on la xarxa de la distribuïdora (aquí Endesa / e‑distribución) entra a la propietat del client. En un client gran és de **mitja tensió** (MT: 11 o 25 kV a Barcelona).
- **CT (centre de transformació)**: sala o caseta amb un transformador que passa de MT a **baixa tensió** (BT: 400/230 V), la que fan servir els endollats i les màquines. Un transformador típic fa de 630 a 1.000 kVA.
- **Subestació**: el mateix concepte, però a alta tensió (110 kV o més) i amb molta més potència.
- **CUPS**: el codi de cada punt de subministrament que surt a la factura. Un CUPS correspon a un comptador.

## 2. Què és real i què és proposta

| Element | Estat | Font |
|---|---|---|
| Plaques FV a les cobertes A1–A6 | **Real** | OSM `power=generator` + SIRENA 2025 |
| Dues plantes FV separades: 170 kWp (A1–A4) i 80,18 kWp (A5–A6), amb un 50 % d'autoconsum | **Real** | SIRENA 2025 ("Aularis DNA1‑DNA6"), Programa d'accions energia 2022 |
| Subestació BSC 110/25 kV soterrada, 2 × 20/25 MVA, 20 MW, a l'edifici BSC‑Repsol (Pl. Eusebi Güell) | **Real** (la posició exacta dins de l'edifici no es publica) | Plec CONSER02019005OP del BSC |
| La línia del BSC ve de la línia Collblanc – Santa Creu d'Olorda (punt "Finestrelles", Esplugues) i passa per la galeria de la Ronda de Dalt | **Real** | Mateix plec |
| L'Omega té el CPD central de la UPC (6 % de l'electricitat de tota la UPC el 2010) i un SAI propi | **Real** | SIRENA 2010, licitació del SAI de l'Omega |
| El 70 % del consum del Campus Nord ve d'equips sempre connectats (sobretot TIC) | **Real** | Programa d'accions energia 2022 |
| Nombre de CUPS o d'escomeses de la UPC al Campus Nord | **No publicat** | – |
| Posició i nombre de CT de la UPC | **No publicat** → proposta | Aquest document |
| Bateria de 2 MWh / 500 kW | **Hipotètica** (la del repte) | Enunciat del repte |
| No hem trobat cap bateria actual ni prevista a la UPC. El conveni amb L'Energètica (2025) preveu més FV a Diagonal Nord, però no en parla. | – | SIRENA 2025 |

### Per què diem que hi ha més d'una connexió

- El campus té uns **100.000 m² construïts** (suma de la llista oficial de 2009: mòduls A–D, Vèrtex 18.574 m², Omega 10.083 m², Biblioteca, Poliesportiu, Nexus, Torre Girona). El nostre model dona puntes de ~1,8 MW. Amb transformadors de 630–1.000 kVA calen **almenys 2 o 3 transformadors**. A més, els edificis són de quatre èpoques diferents: mòduls (anys 90), Vèrtex, Omega i Nexus. Cada ampliació sol afegir el seu CT.
- Hi ha **dues plantes FV separades** (A1–A4 i A5–A6). Això fa pensar que almenys hi ha dos quadres de BT diferents a la fila A.
- El **BSC té la seva pròpia connexió d'alta tensió**. És un altre client, amb un altre comptador. El dibuixem com a context, però no compta en el consum de la UPC.
- La **Residència Torre Girona** i l'**Edifici Til·lers** no són UPC i tindran el seu propi subministrament. No els dibuixem.

L'hipòtesi més habitual en un campus així és **una escomesa de MT (o dues) amb un anell intern de MT del client que alimenta diversos CT**. Això és el que representem. No sabem si hi ha un o dos CUPS de MT. Al dashboard ho tractem com un sol punt de mesura (el del repte).

## 3. El que hi ha a `campus_nord.json`

`energy_assets.grid_connections[]` (coordenades en m: x = est, y = amunt, z = sud):

| id | Nom | Posició (x, y, z) | Alimenta | Confiança |
|---|---|---|---|---|
| `upc_main` | Escomesa principal UPC (MT) + CT aularis | (17,2, 0, 124,8) | A1–A6, pavellons, Biblioteca, Poliesportiu, Nexus 1 | proposta |
| `ct_modules` | CT mòduls B, C i D | (−122,3, 0, 8,4) | B0–B6, C1–C6, D1–D6 | proposta |
| `ct_omega` | CT Omega (CPD) | (45,7, 0, 22,3) | Omega, Nexus 2, edifici petit sense nom | proposta |
| `ct_vertex` | CT Vèrtex | (29,2, 0, −195,7) | Vèrtex | proposta |
| `bsc_substation` | Subestació BSC 110/25 kV (soterrada) | (175,8, 0, −119,6) | BSC‑Repsol, Capella | **documentada** |

- `grid_connection` es manté igual que abans (= `upc_main`), perquè `scene.js` el continua llegint.
- `mv_links`: `upc_main→ct_modules`, `upc_main→ct_omega`, `ct_omega→ct_vertex`. És l'anell intern de MT que proposem.
- Cada element porta `feeds` (ids d'edificis), `source` i `note`. El BSC porta `upc_meter: false` i `underground: true`.
- Com es posen els CT proposats: a l'espai lliure més proper (≥ 3 m de qualsevol edifici i dins del límit) a l'edifici de referència (C3, Omega, Vèrtex).
- Per què l'escomesa principal és a la vora del **C/ Jordi Girona**: és el carrer de l'adreça oficial (Jordi Girona 1‑3 i 31), on hi ha l'accés principal i les vies amb xarxa de distribució, i la tenim al costat dels aularis amb FV. És una hipòtesi: no ho hem pogut verificar.

## 4. La bateria (proposta)

Posició: (7,5, 0, 111,5), un contenidor de 20 peus (6,1 × 2,6 × 2,4 m) connectat a `upc_main` (`connects_to`). El camp `rationale` del JSON ho resumeix:

1. **Al costat de l'escomesa i del CT dels aularis.** És on es troben la xarxa i les dues plantes FV. La bateria es carrega amb l'excedent solar (avui el 50 % de la FV no s'autoconsumeix) sense passar per altres transformadors. A més, queda darrere del mateix comptador, que és el que el model del repte optimitza.
2. **Espai obert i pavimentat** entre el poliesportiu i el carrer: no cal treure aparcament ni zona verda interior.
3. **Accessible des del C/ Jordi Girona** per a un camió grua (per instal·lar-la) i per als bombers.
4. **A més de 10 m de qualsevol edifici.** Les guies de seguretat de bateries de liti demanen separar-les de les façanes i de les sortides. Tampoc queda a sota de cap aula.

Una alternativa raonable seria posar-la al costat de l'Omega (CPD, consum pla les 24 h). La descartem perquè l'Omega està al mig del campus, envoltat d'edificis, i el camió hi arribaria pitjor.

## 5. Com dibuixar-ho a l'escena 3D

- **Escomesa principal (`upc_main`)**: la torre/CT que ja hi ha, una mica més gran, amb l'etiqueta "Xarxa (Endesa, MT)". És l'únic punt on el flux de xarxa entra i surt del campus. El color segueix el CO₂, com ara.
- **CT interns (`ct_*`)**: caixetes petites (~0,6 u) de color neutre, totes iguals, amb un tooltip: "CT proposat – ubicació il·lustrativa". **No** han de semblar connexions a la xarxa. Són repartiment intern.
- **Anell de MT (`mv_links`)**: línies fines discontínues a nivell de terra entre l'escomesa i els CT (estil "cable soterrat"). Les partícules de flux van de l'escomesa als CT, i la seva quantitat és proporcional al consum del campus.
- **CT → edificis (`feeds`)**: en passar el ratolí per sobre d'un CT, ressalteu els edificis que alimenta (canvi de to). No dibuixeu un cable a cada edifici: carregaria massa l'escena i no sabem el traçat real.
- **FV**: les partícules solars baixen de les cobertes A1–A6 a `upc_main` (dues plantes: A1–A4 i A5–A6).
- **Bateria**: connectada només a `upc_main` amb un tram curt. Manteniu l'etiqueta "ubicació il·lustrativa".
- **BSC**: una marca gris tènue (sense flux animat) a l'edifici BSC‑Repsol, amb la nota "Subestació del BSC (110 kV), client diferent, fora del nostre balanç". Això ensenya que coneixem el context sense barrejar dades.
- **Llegenda**: "Real" (FV, edificis, BSC) / "Proposta" (escomesa, CT, bateria). Feu servir el camp `confidence`.

## 6. Què hem buscat i no hem trobat

- **OSM**: cap `power=transformer`, `power=substation`, `power=cable`/`minor_line` ni `building=transformer_tower` a la caixa del campus. Només hi ha generadors FV. La consulta a Overpass (bbox 41,384–41,392 / 2,106–2,118) ha tornat 502 ("server at capacity").
- **Web**: hem fet cerques en català, castellà i anglès sobre CT, mitja tensió, CUPS, subestacions d'Endesa i bateries a la UPC. No hi ha cap plànol elèctric públic del Campus Nord. Els plecs de manteniment de 2009 parlen només d'instal·lacions de **baixa tensió**. Així sabem que la UPC manté la BT, però no on són els CT.
- Si algú de l'equip vol la dada real, el camí és demanar-la a la **Unitat de Campus Nord** (campus.nord@upc.edu) o al **Servei d'Infraestructures**, que fa els informes SIRENA. Amb aquesta resposta només cal canviar les posicions i `confidence` al script.

## 7. Fonts

- Llista oficial d'edificis del Campus Nord (A1–A6, B0–B6, C1–C6, D1–D6, R/TG, VX, OM, PO, BIB, NXI, NXII), plec de manteniment de 2009: https://seuelectronica.upc.edu/ca/perfil-de-contractant/historic-de-licitacions/Licitacions_Previes_28-feb-2011/procediments-oberts-any-2009-carpeta/conse160000ho2009111-83/plec-tec.pdf
- ETSETB a l'edifici B3: https://telecos.upc.edu/ca
- FIB a l'edifici B6: https://www.fib.upc.edu/en/contact
- Aules de la FIB a A4, A5 i A6 i laboratoris a A5: https://www.fib.upc.edu/en/fib/rooms/computer-labs
- Subestació del BSC (plec CONSER02019005OP): https://ewebapps.bsc.es/tenders/ca/download/file/tender-file/47
- Notícia de l'edifici BSC‑Repsol (Pl. Eusebi Güell 1‑3): https://bsc.es/ca/printpdf/noticies/noticies-del-bsc/el-bsc-estrena-la-nova-seu-corporativa-el-bsc-repsol-building
- Informe SIRENA 2025 (FV Aularis DNA1–DNA6, 170 + 80,18 kWp, 50 % d'autoconsum, conveni amb L'Energètica): https://sostenible.upc.edu/ca/reptes/documents-pla-2030/informe-sirena-global-2025.pdf
- Programa d'accions energia 2022 (A1–A4 170 kWp, A5–A6 80,18 kWp; 70 % del consum sempre connectat): https://govern.upc.edu/ca/cs/ple-del-consell-social/ple-4-2022/informacio-del-gerent/programa-accions-energia/@@display-file/visiblefile/4.-Programa%20accions%20energia.pdf
- Informe SIRENA 2010 (CPD de l'Omega = 6 % de l'electricitat de la UPC): https://is.upc.edu/ca/publicacions/old/informes/documents/informe-sirena-2010-1/@@download/file/Informe%20SIRENA%2010.pdf
- Dades geogràfiques: © OpenStreetMap contributors, ODbL.
