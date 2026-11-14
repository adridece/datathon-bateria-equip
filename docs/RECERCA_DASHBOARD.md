# Recerca de disseny per al dashboard (Tukey Commission)

> Objectiu: guanyar el side challenge *"Design a dashboard that can help you take decisions about the main challenge"*.
> Criteris del jurat: **utilitat per decidir**, **adequació de les representacions**, **coherència** entre indicadors, gràfics i conclusions.
> Aquest document recull la recerca (amb fonts), un diagnòstic del dashboard actual, un sistema visual concret, un pla 3D implementable i una llista de tasques per a les properes ~8 h.
> Data de la recerca: novembre 2026. Entorn verificat a la màquina: **Streamlit 1.67.0**, **Altair 6.3.0**, Node 25 (per empaquetar JS una sola vegada).

---

## 0. Resum executiu (llegiu només això si aneu justos)

1. **El que fa que sembli "fet per IA"** al nostre dashboard: emojis a tot arreu (títol, pestanyes, `1️⃣`, `✅`, `📌`, icones 🏭☀️🏫 dins l'SVG), paleta Tailwind per defecte (`#0f172a`, `#60a5fa`, `#4ade80`, `#f472b6` són exactament slate‑900, blue‑400, green‑400, pink‑400), font `system-ui`, fila de 4 targetes iguals, caixes verdes "Decisió" amb vora esquerra, i el look per defecte de Streamlit. Tot això es pot treure en 1–2 h.
2. **El que guanya el Tukey** no és el 3D: és que cada pantalla sigui *pregunta → resposta en una frase → gràfic que ho demostra → supòsit/límit*, amb **les mateixes xifres a tot arreu** i el gràfic adequat per a cada comparació. El 3D és el "ganxo" de la demo, no l'argument.
3. **3D recomanat:** three.js **0.170.0** (última versió amb `three.module.min.js` en un sol fitxer; des de 0.17x la build es parteix en `three.module` + `three.core`) **empaquetat una sola vegada amb esbuild en un IIFE** i **incrustat inline** a l'HTML que Python passa a `st.iframe`. Zero xarxa, zero problemes de MIME a Windows. Escena "diorama" low‑poly amb càmera ortogràfica isomètrica, partícules (`InstancedMesh`) seguint corbes `CatmullRomCurve3`, bateria amb nivell de càrrega com a malla escalada, color del cable de xarxa segons CO₂. Fallback automàtic a l'SVG actual si no hi ha WebGL.
4. **`components.html` està deprecat des de Streamlit 1.56** (tenim 1.67) → fer servir **`st.iframe(html_string, height=...)`**.
5. **Sistema visual:** fons paper càlid, tinta gairebé negra, **un sol color d'accent** (el nostre agent), escenaris de referència en gris, paleta semàntica d'energia basada en Okabe‑Ito (apta per a daltonisme), CO₂ en rampa seqüencial d'un sol to (mai vermell→verd). Tipografia **IBM Plex Sans + IBM Plex Mono** (o Source Serif 4 per a les respostes), servida en local.

---

## 1. Diagnòstic del dashboard actual (`dashboard/`)

Fitxers llegits: `app.py` (165 línies), `decisions.py` (150), `analisi.py` (122), `animacio.html` (119).

**El que ja està bé (mantenir):**
- La pestanya **Decisions** ja segueix l'estructura pregunta → decisió → gràfic → conclusió (Q1 estratègia, Q2 quan carregar, Q3 mida, Q4 robustesa). És exactament el que demana el criteri "utilitat".
- Totes les xifres surten del simulador oficial via `src/replay.py` i es fan servir a tot arreu (coherència). `analisi.py` cacheja a `data/processed/dash_*.csv`.
- L'animació SVG+JS funciona sense internet, té play/pausa/velocitat/scrub i una frase "per què" a cada hora. És una bona base i serà el **fallback 2D**.
- Hi ha un control "Què passaria si" (capacitat, potència, pes CO₂) i una taula d'inversió/retorn amb hipòtesi editable (€/kWh): això és *decision support* de veritat.

**Problemes a resoldre (ordenats per impacte en el jurat):**

| # | Problema | Per què resta | Solució |
|---|----------|---------------|---------|
| 1 | Emojis a títols, pestanyes, respostes, llegendes i nodes SVG | Senyal núm. 1 de "plantilla/IA"; soroll visual | Text pur + icones SVG pròpies de traç fi (o cap icona) |
| 2 | Paleta Tailwind 400 sobre slate‑900 | És el look "dashboard generat" per excel·lència | Paleta pròpia (secció 6) |
| 3 | Colors inconsistents entre gràfics: càrrega és `#2dd4bf` en un lloc i `VERD` en un altre; CO₂ és lila a Decisions i verd→vermell a l'animació | Trenca la **coherència** (criteri 3) | Un fitxer `estil.py` amb tokens semàntics usats per Altair, CSS i JS |
| 4 | CO₂ codificat amb `hsl(120→0)` (verd→vermell) | No apte per a daltonisme (deuteranopia ~8 % dels homes) | Rampa seqüencial d'un to (secció 6.2) |
| 5 | 4 KPIs iguals en targetes | Aplana la jerarquia: "Infraccions 0" pesa igual que "CO₂ evitat" | 1 xifra protagonista + 2 de suport + 1 nota |
| 6 | Q2 fa dos gràfics separats (barres de bateria i línies CO₂/preu) amb eixos diferents | El lector ha de comparar de memòria | Small multiples verticals alineats amb el mateix eix X (hora), o heatmap dia×hora |
| 7 | La comparativa (`tab2`) usa `st.line_chart`/`st.bar_chart` per defecte i `st.dataframe` cru | Estil inconsistent amb les gràfiques Altair de Decisions | Tot amb Altair + tema registrat |
| 8 | Unitats i arrodoniments barrejats (kg vs t, € vs k€, 2 decimals a %) | Coherència i precisió excessiva (error de Few) | Regles d'unitats (secció 6.6) |
| 9 | `components.html` deprecat | Avís a la consola, risc futur | `st.iframe` |
| 10 | "= òptim teòric" al KPI de puntuació | Afirmació forta sense context visible | Mostrar "a X % de l'òptim (oracle)" amb el número |

---

## 2. Què fa que un dashboard sembli genèric o "generat per IA" — i regles concretes

### 2.1 Senyals de "plantilla/IA" identificats per la comunitat de disseny (2025–2026)
Fonts: [saasui.design – SaaS UI looks AI generated](https://www.saasui.design/blog/saas-ui-looks-ai-generated), [bswen – AI‑generated UI anti‑patterns (2026)](https://docs.bswen.com/blog/2026-03-20-ai-generated-ui-anti-patterns/), [bswen – make AI frontend unique](https://docs.bswen.com/blog/2026-03-30-ai-frontend-design-unique), [Towards AI – 10 signs of AI‑generated design](https://pub.towardsai.net/10-signs-of-ai-generated-design-and-how-to-make-yours-not-look-like-it-482ff7da81fc), [Medium – why your AI UI looks like everyone else's](https://medium.com/@Rythmuxdesigner/why-your-ai-generated-ui-looks-like-everyone-elses-and-how-to-break-the-pattern-7a3bf6b070be), [Cerebras – generating beautiful UIs](https://cerebras.ai/blog/generating-beautiful-uis). (Són heurístiques d'opinió, no un estàndard; però coincideixen.)

- Degradats lila/blau, glassmorphism, neó cian sobre fons blau marí fosc.
- **Graella de targetes iguals** (i targetes dins de targetes): totes les mètriques pesen igual.
- Emojis fent d'icones; icones decoratives al costat de cada títol.
- Inter / system‑ui per defecte, tot amb el mateix pes i mida; números sense xifres tabulars.
- Cantonades molt arrodonides a tot arreu, ombres suaus a tot arreu.
- Copy genèric: "Insights", "Overview", "Powered by AI", signes d'exclamació, adjectius ("increïble", "potent").
- Tots els gràfics amb els colors per defecte de la llibreria i llegendes separades.

### 2.2 Regles de la tradició de visualització (fonts primàries/canòniques)
- **Tufte – data‑ink ratio i chartjunk:** maximitzar la tinta dedicada a dades; esborrar la tinta que no és dada i la redundant. [edwardtufte.com](https://www.edwardtufte.com/) · resum: [antoinebuteau.com – lessons from Tufte](https://www.antoinebuteau.com/lessons-from-edward-tufte.md). Small multiples: mateixa escala, comparació a cop d'ull.
- **Stephen Few – *Information Dashboard Design*:** un dashboard és la informació més important per assolir objectius, *en una sola pantalla*, per monitoritzar a cop d'ull. Els 13 errors (excedir una pantalla, context insuficient, detall/precisió excessius, mesures inadequades, gràfics mal triats, varietat innecessària, codificació quantitativa incorrecta, mala disposició, no destacar el que importa, decoració inútil, mal ús del color, disseny poc estètic…). [perceptualedge.com](https://www.perceptualedge.com/) · resum: [Data School part 1](https://www.thedataschool.co.uk/anh-vu/are-you-making-these-13-dashboard-design-mistakes/), [part 2](https://www.thedataschool.co.uk/anh-vu/are-you-making-these-13-dashboard-design-mistakes-part-2) · [UXmatters review](https://uxmatters.com/mt/archives/2007/04/book-review-information-dashboard-design.php).
- **Cole Nussbaumer Knaflic – *Storytelling with Data*:** treure el desordre; començar el gràfic en gris i triar deliberadament què es destaca; **títols d'acció** que diuen la conclusió ("L'agent carrega quan el CO₂ és mínim"), no l'etiqueta ("Perfil horari"). [storytellingwithdata.com](https://www.storytellingwithdata.com/gallery) · [O'Reilly](https://oreilly.com/library/view/storytelling-with-data/9781119621492) · [Chartio – declutter](https://chartio.com/blog/declutter-your-data-visualizations).
- **Datawrapper (Lisa Charlotte Muth):** gris per a tot primer, color només per al que importa; menys colors; colors amb lluminositat diferent; fons. [Emphasize with color](https://www.datawrapper.de/blog/emphasize-with-color-in-data-visualizations) · [10 ways to use fewer colors](https://www.datawrapper.de/blog/10-ways-to-use-fewer-colors-in-your-data-visualizations) · [Choosing colors](https://www.datawrapper.de/blog/colors) · [Beautiful colors](https://www.datawrapper.de/blog/beautifulcolors) · [Colors in style guides](https://www.datawrapper.de/blog/colors-for-data-vis-style-guides) · [Background color](https://www.datawrapper.de/blog/background-color-of-data-visualizations).
- **Financial Times – Visual Vocabulary:** triar el gràfic segons la *relació* que es vol mostrar (desviació, correlació, rànquing, distribució, canvi en el temps, magnitud, part‑tot, espacial, flux). [GitHub chart‑doctor](https://github.com/Financial-Times/chart-doctor/blob/main/visual-vocabulary/README.md) · [web](https://ft-interactive.github.io/visual-vocabulary/).
- **The Economist – chart style guide:** fons blanc, una línia/etiqueta de marca a dalt, títol + subtítol amb unitats, font a sota, gris per a la reixeta, paleta curta. [PDF 2017](https://d30jyndnpz0ndz.cloudfront.net/documents/CHARTstyleguide_20170505.pdf) · [Data School – 5 lessons from The Economist](https://thedataschool.co.uk/johann-shin/visual-storytelling-done-right-5-lessons-from-the-economist).
- Altres guies públiques útils: [ONS chart style guide](https://ons-design.notion.site/ONS-chart-style-guide-abc7605a97624dc2bc7f2a3e16379d82), [ONS typography](https://service-manual.ons.gov.uk/data-visualisation/build-specifications/typography), [World Bank chart elements](https://worldbank.github.io/data-visualization-style-guide/chartelements), [UK Gov Analysis Function – charts](https://analysisfunction.civilservice.gov.uk/policy-store/data-visualisation-charts), [Royal Statistical Society – choosing](https://royal-statistical-society.github.io/datavisguide/docs/choosing.pdf), [data.europa.eu – choosing charts](https://data.europa.eu/apps/data-visualisation-guide/choosing-charts-the-message), [Maersk chart style guide](https://designsystem.maersk.com/guidelines/data-visualisation/chart-style-guide/), [Nightingale – colour accessibility](https://nightingaledvs.com/data-journalism-colour-accessibility/). Referents editorials: [The Pudding](https://pudding.cool/), [Observable Plot](https://observablehq.com/plot/).

### 2.3 Regles concretes per al nostre dashboard ("checklist anti‑genèric")
1. **Zero emojis.** Ni a `page_icon`, ni a pestanyes, ni a respostes. Si cal icona, SVG propi de 1,5 px de traç, mateix color que el text.
2. **Un sol accent.** El nostre agent = accent; "sense bateria" i "plantilla" = grisos; l'oracle = línia de referència discontínua. Res més té color fort.
3. **Títols d'acció** a cada gràfic (la conclusió), subtítol amb la mesura i unitats, nota de font a sota en petit: *"Font: simulador oficial, 12 setmanes de validació (2.016 h)."*
4. **Etiquetatge directe** a final de línia en lloc de llegendes (Datawrapper/FT). Elimina la majoria de llegendes.
5. **Jerarquia, no graella:** una xifra protagonista gran (CO₂ evitat, t/any), dues secundàries, la resta en text.
6. **Xifres tabulars** (`font-variant-numeric: tabular-nums`) a KPIs, taules i eixos.
7. **Cantonades petites** (4–6 px) o cap; sense ombres; separar amb espai i línies fines (1 px `#DAD6CE`), no amb caixes.
8. **Copy en català, sobri, actiu i curt:** verbs ("Carrega al migdia"), xifres concretes, sense adjectius ni signes d'exclamació, sense "IA", "intel·ligent", "potent".
9. **Precisió justa:** % amb 1 decimal, kW i kWh sense decimals, € arrodonits a centenars o k€, t CO₂ amb 0 decimals per any.
10. **Mateixa escala** quan es comparen panells (small multiples); eix Y a zero en barres; no a línies de puntuació si s'indica.
11. **Una pantalla per pregunta**: el jurat no ha de fer scroll infinit (Few, error 1).
12. **Detall d'artesania:** espaiats consistents (escala de 4 px), alineació a una graella de 12 columnes, marges iguals, línia de base comuna entre KPI i gràfics.

---

## 3. Referents d'energia/xarxa/bateria (què copiar de cadascun)

| Referent | URL | Què fa bé | Què n'agafem |
|---|---|---|---|
| **Electricity Maps** | [app.electricitymaps.com/map](https://app.electricitymaps.com/map) · [producte](https://electricitymaps.com/platform/map) · [metodologia](https://electricityMap.org/methodology) · [repo obert](https://awesome.ecosyste.ms/projects/github.com%2Felectricitymaps%2Felectricitymaps-contrib) · [TechCrunch 2024](https://techcrunch.com/2024/05/06/electricity-maps-calculates-the-carbon-intensity-of-electricity-consumption-to-optimize-usage-at-scale) | Color = intensitat de carboni (gCO₂/kWh) amb llegenda contínua; fletxes animades d'intercanvi; capes (carboni, preu, renovable, càrrega); lliscador temporal | Codificar el **cable de la xarxa pel CO₂** amb rampa contínua + llegenda amb unitats; fletxes/partícules amb velocitat ∝ potència |
| **Red Eléctrica – REData** | [ree.es/es/datos](https://www.ree.es/es/datos) · [nou espai REData](https://www.ree.es/en/datos/publications/news-todate/redata-is-now-part-of-all-our-lives-a-new-web-space) · [demanda en temps real](https://www.ree.es/en/node/1240) · [bloc d'emmagatzematge 2025](https://www.ree.es/en/press-office/press-release/news/press-release/2025/02/red-electrica-expands-information-electricity-system-to-adapt-it-ecological-transition) | Corbes previsió/programada/real superposades; mix per tecnologia; és la font del PVPC i CO₂ que fem servir | Mostrar "previsió vs real" a la robustesa; anomenar la font (credibilitat local) |
| **Grid Status** | [gridstatus.io](https://www.gridstatus.io/) · [docs](https://docs.gridstatus.io/llms.txt) · [changelog maig 2026](https://docs.gridstatus.io/changelog/may-2026/15-may-add-supply-and-demand-chart-to-ercot-live-page) | Gràfics densos però nets, molt textuals; anàlisi "càrrega amb i sense càrrega de bateries" a CAISO | Gràfic **"consum del campus amb i sense bateria"** (dues línies, l'àrea entre elles = energia desplaçada) |
| **Ember – Electricity Data Explorer** | [ember-energy.org/data/electricity-data-explorer](https://ember-energy.org/data/electricity-data-explorer/) · [Data Explorer 2.0 (2025)](https://ember-energy.org/latest-updates/newsletter-ember-current-july-2025) | Tipografia editorial, gris + un color, comparacions per selector, títols que expliquen | Estil editorial i títols d'acció |
| **NESO Carbon Intensity (GB)** | [carbonintensity.org.uk](https://carbonintensity.org.uk/) · [app](https://www.neso.energy/about/our-progress-towards-net-zero/carbon-intensity-app) · [dashboard](https://neso.energy/future-energy/our-progress/carbon-intensity-dashboard) | Previsió de 96 h en franges de color per index (very low → very high); missatge accionable "millor moment per consumir" | **Franja de 24 h de CO₂** sota l'escena 3D, amb les hores que l'agent tria per carregar marcades: és la "previsió" que l'agent veu |
| **Tesla app (Powerwall)** | [Energy data](https://www.tesla.com/support/energy/powerwall/mobile-app/energy-data) · [Time‑based control](https://www.tesla.com/support/energy/powerwall/mobile-app/time-based-control-user-guide) · [podfeet – flux](https://www.podfeet.com/blog/2022/09/solar-batteries/) · [card HA estil Tesla](https://www.github.com/reptilex/tesla-style-solar-power-card) | Casa al centre; fonts → casa amb línies animades; color fix per font (solar groc, bateria verd, xarxa gris, casa blau); casa 3D des de la v4.10 | **Colors fixos per actor** i el campus com a centre; gruix/densitat ∝ kW |
| **Octopus Agile (UK)** | [octopus.energy/smart/agile](https://octopus.energy/smart/agile/) | Barres de preu per franja amb les més barates destacades: decisió immediata | Barres de preu/CO₂ de les properes 24 h amb el pla de l'agent sobreposat |
| **LLNL Energy Flow (Sankey)** | [flowcharts.llnl.gov](https://flowcharts.llnl.gov/) · [ANS](https://www.ans.org/news/article-461/llnl-expands-release-of-energy-flowcharts/) | Sankey amb "energia rebutjada" explícita | **Sankey del període**: xarxa+solar → bateria/campus, amb les **pèrdues del 10 %** visibles (honestedat = coherència) |

---

## 4. Estructura d'un dashboard per decidir

### 4.1 Patró de cada secció (Q → A → E → L)
1. **Pregunta** (la del gestor de la UPC, en llenguatge seu): *"Quina mida de bateria hauríem de comprar?"*
2. **Resposta en una frase amb xifra** (títol d'acció): *"2.000 kWh amb l'inversor de 500 kW: 9 de cada 10 € d'estalvi possibles, retorn en X anys."*
3. **Evidència**: 1 gràfic (màxim 2) triat segons la comparació; el punt de la decisió anotat dins del gràfic.
4. **Límits/supòsits**: una línia en gris ("Suposa 350 €/kWh i 15 anys de vida; editable").

### 4.2 Disseny de KPIs
- Cada KPI = **valor + unitat + comparació + període**. Ex.: "**−X t CO₂/any** · −Y % vs. sense bateria · estimació anual a partir de 12 setmanes".
- Sempre amb referència (vs. sense bateria, vs. plantilla, vs. oracle). Un número sol no ajuda a decidir.
- Mostrar el **rang** si n'hi ha (ex. mín–màx mensual) en lloc de 2 decimals de falsa precisió.
- "Infraccions: 0" no és un KPI, és una garantia: posar‑ho com a nota sota la puntuació.

### 4.3 Anotacions
- Anotar *dins* del gràfic el que el títol afirma: el "colze" de la corba de sensibilitat, les hores de càrrega, la fletxa "−X %".
- A Altair: `mark_text` + `mark_rule` sobre un DataFrame d'anotacions; text en el color de tinta, mida 12.

### 4.4 Quin gràfic per a quina comparació (aplicat al nostre cas)

| Pregunta / comparació | Relació (FT) | Gràfic recomanat | Ara | Canvi |
|---|---|---|---|---|
| Quina estratègia? (4 escenaris, 1 mètrica) | Rànquing / magnitud | **Barres horitzontals ordenades**, nostre agent en accent, oracle com a línia vertical discontínua | Barres | Afegir oracle com a regla + etiqueta directa |
| CO₂ vs cost per estratègia | Correlació | **Dot plot de 2 columnes** (ΔCO₂ %, Δcost %) o scatter amb 4 punts etiquetats | Taula | Afegir |
| Quan carregar? (24 h) | Desviació + temps | **Barres divergents** (+càrrega/−descàrrega) amb **CO₂ i preu en panells petits alineats a sobre** (mateix eix X) | 2 gràfics separats | Small multiples verticals (`alt.vconcat`, `shared x`) |
| Patró dia × hora (12 setmanes) | Distribució temporal | **Heatmap** hora (x) × dia (y) de la potència de bateria, divergent | — | Nou: prova visual que no és un horari fix |
| Estalvi per mes | Canvi en el temps / rànquing | **Dot plot o barres** per mes, un sol color (CO₂) + un altre (cost) etiquetats directament | Barres agrupades | Simplificar |
| Mida de bateria | Canvi continu | **Línies** capacitat→t CO₂/any per potència, amb el "colze" anotat; barra vertical a 2.000 kWh | Línies | Anotar colze i selecció |
| Inversió i retorn | Magnitud | Taula curta amb 3 files destacades + slider d'hipòtesi | Taula llarga | Ressaltar la fila recomanada |
| Robustesa a errors de previsió | Canvi | **Línia** error% → puntuació amb banda "zona d'error realista" | Línia | Afegir banda i línia d'oracle |
| Balanç energètic del període | Flux | **Sankey** xarxa/solar → bateria → campus amb pèrdues | — | Nou (Plotly `go.Sankey` o SVG) |
| Operació hora a hora | Flux en el temps | **Escena 3D** + franja de 24 h + gràfic de 7 dies sincronitzat | SVG 2D | 3D (secció 5), SVG com a fallback |
| Campus amb vs sense bateria | Desviació | **Dues línies + àrea entre elles** (estil Grid Status) | — | Nou, a la pestanya "En directe" |

---

## 5. 3D interactiu de l'operació del campus

### 5.1 Comparació d'opcions (mides mesurades a jsDelivr, novembre 2026)

| Opció | Mida JS | Offline | Qualitat visual | Interacció | Partícules de flux | Postprocés (bloom) | Cost de setup | Veredicte |
|---|---|---|---|---|---|---|---|---|
| **three.js 0.170.0** | `three.module.min.js` 691 KB (1 fitxer) + OrbitControls 32 KB | Sí (vendoritzat) | Alta, control total | Orbit, raycast per hover | `InstancedMesh` + corbes: trivial i ràpid | `UnrealBloomPass` (addon) o glow fals amb sprites | Baix‑mitjà | **Recomanat** |
| three.js ≥0.171 (última 0.187.0) | `three.module.min.js` 365 KB + `three.core.min.js` 384 KB (2 fitxers que s'importen) | Sí, però cal import map o bundle | Igual | Igual | Igual | Igual | Mitjà | OK si s'empaqueta amb esbuild |
| react‑three‑fiber | React + three + r3f + bundler | Requereix build | Alta | Alta | Alta | pmndrs/postprocessing | Alt (toolchain React) | Massa pesat per 8 h |
| Babylon.js 7.54 | `babylon.js` 6,8 MB | Sí | Molt alta, PBR | Alta (inspector) | Particle system integrat | Integrat | Mitjà | Pesat; API més gran |
| deck.gl 9.1 (`dist.min.js`) | 1,6 MB | Sí però pensat per a mapes | Bona per a dades geo | Hover/pick | `TripsLayer`/`ArcLayer` | No | Mitjà | Per a mapes, no per a una diorama |
| pydeck (`st.pydeck_chart`) | ve amb Streamlit | El mapa base necessita tiles (xarxa) | Correcta | Tooltip | Limitat (arcs estàtics) | No | Molt baix | Sense animació temporal fluida; dependència de mapa |
| Plotly 3D (`plotly.min.js` 4,6 MB) | ve amb Streamlit | Sí | "Gràfic científic", no escena | Orbit | No (frames lents) | No | Molt baix | Sembla un gràfic, no una escena |

Fonts: [three.js – Installation (import maps, mateix CDN i versió per a tots els mòduls)](https://threejs.org/manual/en/installation) · [Discourse – addons sense npm](https://discourse.threejs.org/t/importing-addons-without-npm/44471) · [Discourse – import map r170](https://discourse.threejs.org/t/error-on-android-devices-failed-to-resolve-module-specifier-three/75607) · [registry npm three](https://registry.npmjs.com/three) (latest = 0.187.0 verificat) · [UnrealBloomPass docs](https://threejs.org/docs/pages/UnrealBloomPass.html) · [Discourse – com funciona UnrealBloomPass](https://discourse.threejs.org/t/i-still-dont-get-how-unrealbloompass-works/57843) · [Discourse – selective bloom](https://discourse.threejs.org/t/unrealbloom-only-on-some-selected-objects/74587.md) · [InstancedFlow / CurveModifier](https://threejs.org/docs/pages/InstancedFlow.html) · [varun.ca – 3 maneres de partícules](https://varun.ca/three-js-particles/) · [Discourse – partícules seguint un camí](https://discourse.threejs.org/t/make-particles-follow-a-path-issues/50633).

### 5.2 Recomanació: three.js 0.170.0, bundle IIFE incrustat inline a `st.iframe`

**Per què inline i no servir fitxers estàtics:**
- `st.iframe(html_string)` (i l'antic `components.html`) incrusta l'HTML dins d'un iframe; no hi ha carpeta pròpia per a rutes relatives.
- La via `server.enableStaticServing` + `/app/static/three.module.js` funciona a Mac, però Streamlit decideix el `Content-Type` amb el mòdul `mimetypes` de Python, i **a Windows aquest llegeix el registre**: si `HKEY_CLASSES_ROOT\.js\Content Type = text/plain` (passa sovint), el navegador rebutja els mòduls ES ("strict MIME type checking"). Fonts: [Streamlit – static files](https://docs.streamlit.io/develop/concepts/configuration/serving-static-files), [Python bug 43975](https://bugs.python.org/msg392294), [Windows MIME pitfalls](https://taricorp.net/2020/windows-mime-pitfalls/), [Django #32041](https://code.djangoproject.com/ticket/32041). Risc inacceptable en una demo en directe.
- **Inline = cap petició de xarxa, mateix comportament a Mac/Windows, funciona sense wifi.** Cost: ~750 KB de text per rerun de la pestanya (acceptable en local; es pot cachejar la cadena amb `@st.cache_resource`).

**Pas únic d'empaquetat (Mac, amb Node; el resultat es fa commit i ningú més necessita Node):**
```bash
mkdir -p /tmp/t3 && cd /tmp/t3
npm init -y >/dev/null && npm i three@0.170.0 esbuild@0.24.2
cat > entry.js <<'EOF'
export * from 'three';
export { OrbitControls } from 'three/addons/controls/OrbitControls.js';
export { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
export { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
export { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
export { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
export { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
export { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
EOF
npx esbuild entry.js --bundle --minify --format=iife --global-name=THREE --outfile=three-bundle.min.js
cp three-bundle.min.js /Users/adridece/Documents/Datathon/dashboard/vendor/three-0.170.0-bundle.min.js
cp node_modules/three/LICENSE /Users/adridece/Documents/Datathon/dashboard/vendor/three-LICENSE.txt
```
(Es pot fer amb la versió més nova, 0.187.0, exactament igual: esbuild resol la partició `three.core` sol. Recomanem **0.170.0** perquè, si esbuild fallés, el pla B sense bundler és trivial: `three.module.min.js` és un sol fitxer i OrbitControls només importa `'three'`.)

**Pla B sense bundler (import map amb Blob URLs, també 100 % offline):**
```html
<script type="text/plain" id="src-three">__THREE_MODULE__</script>      <!-- three@0.170.0/build/three.module.min.js -->
<script type="text/plain" id="src-orbit">__ORBIT__</script>             <!-- three@0.170.0/examples/jsm/controls/OrbitControls.js -->
<script>
  const blob = id => URL.createObjectURL(new Blob([document.getElementById(id).textContent], {type: 'text/javascript'}));
  const im = document.createElement('script'); im.type = 'importmap';
  im.textContent = JSON.stringify({imports: {'three': blob('src-three'),
    'three/addons/controls/OrbitControls.js': blob('src-orbit')}});
  document.head.appendChild(im);           // abans de qualsevol mòdul
  const m = document.createElement('script'); m.type = 'module';
  m.textContent = document.getElementById('escena').textContent; document.body.appendChild(m);
</script>
```
URLs exactes per descarrregar (versió fixada):
- `https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.min.js` (691.648 bytes, verificat 200)
- `https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js` (1,31 MB, no minificat, per depurar)
- `https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/controls/OrbitControls.js` (32.134 bytes)
- Bloom (té imports relatius a `../shaders/…`, per això millor via esbuild): `…/examples/jsm/postprocessing/UnrealBloomPass.js`, `EffectComposer.js`, `RenderPass.js`, `OutputPass.js`.
- Import map oficial equivalent (només per desenvolupar amb internet):
  ```html
  <script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js",
   "three/addons/":"https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"}}</script>
  ```

**Integració Python:**
```python
VENDOR = Path(__file__).parent / "vendor" / "three-0.170.0-bundle.min.js"

@st.cache_resource
def _three_js() -> str:
    return VENDOR.read_text(encoding="utf-8")

html = (Path(__file__).parent / "escena3d.html").read_text(encoding="utf-8")
html = html.replace("/*__THREE__*/", _three_js()).replace("__DADES__", dades_animacio(d, 500.0))
st.iframe(html, height=760)   # components.html està deprecat des de 1.56
```
Ull: `str.replace` amb el bundle —no fer servir f‑strings ni `.format()` (el JS té `{}`).

### 5.3 Composició de l'escena ("diorama" del Campus Nord)
- **Estil:** maqueta d'arquitecte low‑poly, colors mats (paper/argila), sense textures. Res de neó. La "vida" la donen les partícules i la llum, no els colors saturats.
- **Terra:** pla 60×40 u, color paper `#ECE8DF`, carrers lleugerament més foscos `#DDD8CC` (plans prims). Opcional: graella de punts molt subtil.
- **Edificis:** ~12–16 blocs `RoundedBoxGeometry` (radi 0,15) en files, inspirats en la disposició en pintes dels edificis A/B/C/D del Campus Nord (verificar amb el plànol oficial de la UPC abans de presentar; si no, dir "esquemàtic"). Alçades 3–5 u. Material `MeshStandardMaterial({color:'#F4F1EA', roughness:.9, metalness:0})`. **Il·luminació de finestres** (emissive) ∝ consum del campus de l'hora: `emissiveIntensity = 0.1 + 0.6·(load−min)/(max−min)`, color `#FFD9A0`.
- **Plaques solars:** 3 terrats amb plans inclinats blau‑pissarra `#3B4A5A`; brillantor ∝ `pv_kw/145`. El sol (DirectionalLight) gira amb l'hora del dia (azimut i elevació aproximats per Barcelona), i de nit s'apaga i entra una llum ambient blavosa: l'hora del dia es "llegeix" sense text.
- **Bateria (BESS):** contenidor de 6×2,4×2,6 u a prop de la subestació. Cara frontal amb **indicador de nivell**: malla interior que s'escala en Y (`scale.y = soc`, amb `position.y` compensat) dins d'una carcassa semitransparent; color de l'interior = color de bateria (secció 6). Text CSS2D a sobre: "64 % · +420 kW".
- **Xarxa:** torre/subestació a la vora, amb un cable (tub) fins al campus. **Color del tub i de les partícules de xarxa = CO₂ de l'hora** (rampa seqüencial, secció 6.2).
- **Fluxos (4 corbes):** xarxa→nus, solar→nus, nus↔bateria, nus→campus. `CatmullRomCurve3` amb 4–6 punts per arc, elevats 0,3 u sobre el terra; `TubeGeometry(curve, 64, 0.05)` amb opacitat 0,25 com a "guia".
- **Partícules:** un `InstancedMesh` per flux (esferes `IcosahedronGeometry(0.12, 1)`, `MeshBasicMaterial`), N màx = 60. Nombre visible ∝ kW (`n = round(Nmax·kW/1500)`), velocitat ∝ kW, direcció segons el signe (bateria). Posició per instància: `curve.getPointAt((t0_i + v·time) % 1)` (`getPointAt` = velocitat constant per longitud d'arc).
- **Glow:** dues opcions:
  - *Barata i robusta (recomanada):* sprite additiu (textura radial generada amb `<canvas>`) a cada partícula, `blending: AdditiveBlending`, `depthWrite:false`.
  - *Bloom real:* `EffectComposer → RenderPass → UnrealBloomPass(strength .6, radius .4, threshold .85) → OutputPass`; amb `renderer.toneMapping = ACESFilmicToneMapping`. Fer que només les partícules superin el llindar (color > 1 en HDR). Desactivar si FPS < 45.
- **Càmera:** `OrthographicCamera` isomètrica (posició (40, 40, 40) mirant a l'origen, zoom ajustat) → look "maqueta", sense distorsió de perspectiva. `OrbitControls` amb `enableDamping`, `minPolarAngle .6`, `maxPolarAngle 1.2`, `enablePan:false`, zoom limitat, i **auto‑rotació lenta desactivable**. Botó "Vista inicial".
- **Llums:** `HemisphereLight('#FFFFFF','#D8D2C4',0.9)` + `DirectionalLight` (sol) amb ombres `PCFSoftShadowMap`, mapa 2048, càmera d'ombra ajustada al terreny. Sense `RoomEnvironment` (estalvia mida i dona look mat).
- **Hover:** `Raycaster` sobre edificis/bateria/xarxa/solar → tooltip HTML (no CSS2D) amb valors de l'hora: "Xarxa · 1.240 kW · 142 g CO₂/kWh · 0,153 €/kWh".

### 5.4 Interfície i sincronització temporal
- Totes les hores del període (fins a 2.016 h × ~12 camps ≈ 200 KB JSON) entren al JS d'una vegada: **la reproducció no fa reruns de Streamlit** (si no, l'iframe es recrea i perd l'estat).
- Controls (HTML sobre el canvas, no widgets Streamlit): Play/Pausa (tecla espai), velocitat (1×, 4×, 24× h/s), **scrubber** amb marques de dia, salt a "pic de CO₂ següent" i "hora de càrrega següent" (botons que porten el jurat directament als moments interessants).
- Interpolació: `time` continu; valors interpolats linealment entre hora `k` i `k+1` → moviment suau del nivell de bateria i dels colors.
- **Franja de previsió de 24 h** sota l'escena (estil NESO/Octopus): 24 barres de CO₂ (rampa) amb el pla de l'agent (càrrega/descàrrega) superposat; deixa veure *per què* decideix.
- **Panell "per què"** (frase actual, sense emojis) i 3 comptadors acumulats (kg CO₂, €, kWh desplaçats) amb xifres tabulars.
- Mini‑gràfic de 7 dies (el que ja hi ha a `animacio.html`, re‑estilitzat) amb el cursor sincronitzat.

### 5.5 Rendiment
- `renderer.setPixelRatio(Math.min(devicePixelRatio, 2))`; `antialias:true`; una sola `requestAnimationFrame`.
- Geometries i materials compartits; 4 `InstancedMesh` en total per a les partícules; `instanceMatrix.setUsage(DynamicDrawUsage)`.
- Ombres només del sol i només per edificis i bateria; `shadowMap.autoUpdate=false` i actualitzar‑lo quan el sol canvia d'hora.
- Pausar el render quan la pestanya no és visible (`document.visibilityState`) i quan està en pausa i no hi ha interacció (render on demand).
- `ResizeObserver` sobre el contenidor per ajustar mida (iframe d'alçada fixa).
- Objectiu: 60 FPS en un portàtil integrat; provar a Windows amb Chrome i Edge.

### 5.6 Fallback 2D
```js
const gl = document.createElement('canvas').getContext('webgl2') || document.createElement('canvas').getContext('webgl');
if (!gl) { /* mostrar l'SVG actual (animacio.html re-estilitzat) */ }
```
I a Streamlit un `st.toggle("Vista 3D", value=True)` per poder canviar a l'SVG en calent si el projector o l'ordinador de la demo fallen.

### 5.7 Esquelet mínim (orientatiu)
```js
const D = __DADES__;               // mateix contracte JSON que animacio.html
const { Scene, OrthographicCamera, WebGLRenderer, CatmullRomCurve3, Vector3, InstancedMesh,
        IcosahedronGeometry, MeshBasicMaterial, Object3D, Color, OrbitControls } = THREE;
const flows = {
  grid: new CatmullRomCurve3([new Vector3(-26,.3,6), new Vector3(-14,.3,4), new Vector3(-4,.3,1), new Vector3(0,.3,0)]),
  bat:  new CatmullRomCurve3([new Vector3(0,.3,0), new Vector3(3,.3,5), new Vector3(6,.3,9)]),
  /* sol, campus … */
};
function particles(curve, color, N=60){
  const m = new InstancedMesh(new IcosahedronGeometry(.12,1), new MeshBasicMaterial({color}), N);
  m.userData = {curve, N, seed: Float32Array.from({length:N}, Math.random)}; scene.add(m); return m;
}
const dummy = new Object3D();
function updateFlow(m, kw, dir, t){           // kw: potència, dir: +1/-1
  const {curve, N, seed} = m.userData, n = Math.round(N * Math.min(1, kw/1500)), v = .05 + .25*Math.min(1, kw/1500);
  m.count = n;
  for (let i=0;i<n;i++){ let u = (seed[i] + dir*v*t) % 1; if (u<0) u+=1;
    dummy.position.copy(curve.getPointAt(u)); dummy.updateMatrix(); m.setMatrixAt(i, dummy.matrix); }
  m.instanceMatrix.needsUpdate = true;
}
```

---

## 6. Sistema visual proposat

### 6.1 Paleta (tokens; clar per defecte perquè els projectors renten els fons foscos)

| Token | Clar | Fosc | Ús |
|---|---|---|---|
| `--paper` (fons) | `#F6F4EF` | `#141618` | Fons de la pàgina |
| `--surface` | `#FFFFFF` | `#1B1E21` | Panells, escena 3D |
| `--ink` | `#1C1F22` | `#E9E6E0` | Text, eixos |
| `--muted` | `#6B6760` | `#9A968F` | Subtítols, fonts, unitats |
| `--rule` | `#DAD6CE` | `#2E3236` | Separadors, reixeta (si cal) |
| `--accent` (el nostre agent) | `#0F5C4D` (verd petroli fosc) | `#5FB3A1` | Única sèrie destacada |
| `--ref` (escenaris de referència) | `#A9A49B` | `#5E625F` | Sense bateria, plantilla |
| `--oracle` | `#1C1F22` discontinu | `#E9E6E0` discontinu | Línia de referència "òptim" |

**Colors semàntics d'energia** (basats en Okabe‑Ito, dissenyats per ser distingibles amb daltonisme; [hex de referència](https://siegal.bio.nyu.edu/color-palette/), [Paul Tol](https://rdrr.io/cran/khroma/f/vignettes/tol.Rmd)):

| Actor | Hex | Nota |
|---|---|---|
| Solar | `#E69F00` (Okabe‑Ito taronja) | Sempre i només solar |
| Bateria – càrrega | `#0072B2` (Okabe‑Ito blau) | |
| Bateria – descàrrega | `#D55E00` (Okabe‑Ito vermelló) | Parella blau/vermelló segura per a deuteranopia |
| Campus (consum) | `#1C1F22` / tinta | El "centre", neutre |
| Xarxa | rampa CO₂ (6.2) | El color diu l'emissió |
| Preu | `#7A5195` (porpra apagat) o línia de tinta discontínua | Preferible: no donar‑li un color nou |

Regla: en els gràfics de *comparació d'estratègies* només hi ha accent + grisos; els colors d'energia només apareixen on es parla de *fluxos*.

### 6.2 Rampa de CO₂ (seqüencial, un sol to, sense vermell‑verd)
5 parades (de net a brut), lluminositat decreixent i monòtona:
`#EFE9DD → #D7C3A0 → #B58D5E → #87603A → #4E3524`
(terra/fum: "més fosc = més brut", intuïtiu i imprimible en gris). Alternativa provada: `viridis` invertit (`alt.Scale(scheme='viridis', reverse=True)`). Llegenda contínua amb unitats **g CO₂/kWh** i els valors mín/màx del període.

### 6.3 Tipografia
- **IBM Plex Sans** (text i títols; 400/500/600) + **IBM Plex Mono** (xifres de KPI, eixos opcionals, codi). Família d'enginyeria, oberta (OFL), suporta català (`l·l`, accents), té xifres tabulars. Evita Inter (associada a "plantilla").
- Alternativa editorial: **Source Serif 4** només per a les frases‑resposta (Q→A), amb Plex Sans a la resta.
- Escala (px): 12 · 14 · 16 (base) · 20 · 28 · 40 (KPI protagonista). Interlineat 1,45 al text, 1,1 als números grans. Pesos: 400 text, 600 títols; mai 800.
- `font-variant-numeric: tabular-nums;` a KPIs, taules i eixos.
- **Offline:** descarregar els `.woff2` (Google Fonts / [IBM Plex GitHub](https://github.com/IBM/plex)) a `dashboard/static/fonts/` i declarar‑los a `config.toml` (6.5). Per a l'iframe 3D, incrustar‑los com a `@font-face` amb `data:font/woff2;base64,…` (≈ 60–90 KB cada pes) o caure a `system-ui` (degradació acceptable).

### 6.4 Espaiat, graella, formes
- Escala 4 px: 4, 8, 12, 16, 24, 32, 48, 64. Entre seccions 48–64; entre títol i gràfic 8–12.
- Amplada de lectura de text ≤ 72 caràcters; gràfics a amplada completa del contenidor.
- `baseRadius` 4–6 px; sense ombres; vores de 1 px `--rule` només on calgui.

### 6.5 Configuració Streamlit (`.streamlit/config.toml`, verificat contra 1.67)
Claus disponibles confirmades amb `streamlit config show`: `font`, `headingFont`, `codeFont`, `fontFaces`, `baseFontSize`, `baseFontWeight`, `headingFontSizes`, `headingFontWeights`, `baseRadius`, `buttonRadius`, `borderColor`, `dataframeBorderColor`, `dataframeHeaderBackgroundColor`, `showWidgetBorder`, `showSidebarBorder`, `chartCategoricalColors`, `chartSequentialColors`, `chartDivergingColors`, `linkColor`, seccions `[theme.light]`, `[theme.dark]`, `[theme.sidebar]`; `client.toolbarMode`; `server.enableStaticServing`. Docs: [fonts](https://docs.streamlit.io/develop/concepts/configuration/theming-customize-fonts), [static fonts](https://docs.streamlit.io/develop/tutorials/configuration-and-theming/static-fonts), [variable fonts](https://docs.streamlit.io/develop/tutorials/configuration-and-theming/variable-fonts), [colors i vores](https://docs.streamlit.io/develop/concepts/configuration/theming-customize-colors-and-borders), [static files](https://docs.streamlit.io/develop/concepts/configuration/serving-static-files).

```toml
[server]
enableStaticServing = true          # serveix dashboard/static/ a /app/static/ (carpeta "static" al costat de app.py)

[client]
toolbarMode = "minimal"             # amaga el menú de desenvolupador i el botó Deploy
showErrorDetails = "none"           # a la demo, cap traceback a pantalla

[browser]
gatherUsageStats = false

[[theme.fontFaces]]
family = "IBM Plex Sans"
url = "app/static/fonts/IBMPlexSans-Regular.woff2"
weight = 400
[[theme.fontFaces]]
family = "IBM Plex Sans"
url = "app/static/fonts/IBMPlexSans-SemiBold.woff2"
weight = 600
[[theme.fontFaces]]
family = "IBM Plex Mono"
url = "app/static/fonts/IBMPlexMono-Regular.woff2"
weight = 400

[theme]
base = "light"
font = "IBM Plex Sans, system-ui, sans-serif"
headingFont = "IBM Plex Sans, system-ui, sans-serif"
codeFont = "IBM Plex Mono, ui-monospace, monospace"
baseFontSize = 16
headingFontWeights = 600
primaryColor = "#0F5C4D"
backgroundColor = "#F6F4EF"
secondaryBackgroundColor = "#ECE8DF"
textColor = "#1C1F22"
linkColor = "#0F5C4D"
borderColor = "#DAD6CE"
showWidgetBorder = true
baseRadius = "small"
chartCategoricalColors = ["#0F5C4D", "#A9A49B", "#6B6760", "#0072B2", "#D55E00", "#E69F00"]
chartSequentialColors = ["#EFE9DD", "#D7C3A0", "#B58D5E", "#87603A", "#4E3524"]
```
Nota: el `config.toml` es llegeix des del directori on s'executa `streamlit run` (l'arrel del repo) → posar‑lo a `/Users/adridece/Documents/Datathon/.streamlit/config.toml`. La carpeta `static/` ha d'estar al costat de l'script principal (`dashboard/static/`). Si una clau no s'accepta, Streamlit avisa a la terminal: comprovar‑ho un cop.

**Treure el "look Streamlit" restant** (amb `st.html`, que injecta CSS sense iframe):
```python
st.html("""<style>
  [data-testid="stHeader"]{background:transparent}
  [data-testid="stDecoration"]{display:none}
  .block-container{padding-top:2rem;max-width:1240px}
  [data-testid="stMetricValue"]{font-family:'IBM Plex Mono',monospace;font-variant-numeric:tabular-nums}
  [data-testid="stCaptionContainer"]{color:#6B6760}
  footer{visibility:hidden}
</style>""")
```
(Els `data-testid` poden canviar entre versions; provar‑ho a 1.67.)

- `st.set_page_config(page_title="Bateria del Campus Nord", page_icon=Path("dashboard/static/icon.svg") o cap, layout="wide")`.
- Pestanyes sense emojis; o millor `st.navigation` amb pàgines (URL per pàgina, útil per al jurat).
- Widgets: `st.segmented_control` / `st.pills` per a selectors curts (període, agent) en lloc de `selectbox` a la sidebar → tot visible a la pantalla principal; amagar la sidebar.

### 6.6 Regles de gràfics (tema Altair registrat una vegada)
Altair 5.5+ / 6: [`@alt.theme.register`](https://altair-viz.github.io/user_guide/generated/theme/altair.theme.register.html), [`ThemeConfig`](https://altair-viz.github.io/user_guide/generated/theme/altair.theme.ThemeConfig.html), [customització](https://altair-viz.github.io/user_guide/customization.html). A Streamlit, **`st.altair_chart(chart, theme=None)`** perquè no sobreescrigui el nostre tema.

```python
import altair as alt
INK, MUTED, RULE, PAPER = "#1C1F22", "#6B6760", "#DAD6CE", "#F6F4EF"
FONT = "IBM Plex Sans, system-ui, sans-serif"

@alt.theme.register("campus", enable=True)
def campus():
    return alt.theme.ThemeConfig({"config": {
        "background": "transparent", "font": FONT,
        "view": {"stroke": None, "continuousHeight": 260},
        "title": {"font": FONT, "fontSize": 16, "fontWeight": 600, "color": INK, "anchor": "start",
                  "subtitleFont": FONT, "subtitleFontSize": 13, "subtitleColor": MUTED, "offset": 12},
        "axis": {"labelFont": FONT, "titleFont": FONT, "labelFontSize": 12, "titleFontSize": 12,
                 "labelColor": MUTED, "titleColor": MUTED, "titleFontWeight": 400,
                 "domainColor": RULE, "tickColor": RULE, "gridColor": RULE, "gridOpacity": .6,
                 "labelPadding": 6},
        "axisX": {"grid": False}, "axisY": {"domain": False, "ticks": False},
        "legend": {"orient": "top", "labelFont": FONT, "titleFont": FONT, "labelColor": INK,
                   "titleColor": MUTED, "symbolType": "square"},
        "range": {"category": ["#0F5C4D", "#A9A49B", "#6B6760", "#0072B2", "#D55E00", "#E69F00"]},
        "line": {"strokeWidth": 2}, "bar": {"cornerRadiusEnd": 2},
        "text": {"font": FONT, "fontSize": 12, "color": INK},
    }})
```
Regles:
- Títol del gràfic = conclusió; subtítol = mesura + unitats + període.
- Reixeta només horitzontal i suau; sense vores de vista; eix X sense reixeta.
- Etiquetes directes al final de les línies (`mark_text` amb l'últim punt) i llegenda només si hi ha > 3 sèries.
- Tooltips formatats (`format=",.0f"`, títols en català) — Altair fa servir punt com a separador de milers només si es configura el locale: usar `alt.renderers.set_embed_options(formatLocale={"decimal": ",", "thousands": ".", "grouping": [3], "currency": ["", " €"]})`.
- Unitats canòniques: potència **kW**, energia **kWh/MWh**, CO₂ **kg** (període) i **t** (any), intensitat **g CO₂/kWh**, preu **€/MWh** (eixos) i **€/kWh** (només a l'escena), diners **€** i **k€/any**.
- Mateixa escala Y en panells que es comparen (`resolve_scale(y="shared")`).

### 6.7 Iconografia
- Cap emoji. Si cal, icones de línia pròpies (SVG 16/20 px, traç 1,5, `currentColor`) per a: xarxa (torre), sol, bateria, edifici. Es poden dibuixar a mà en 10 min; dona caràcter propi.
- Alternativa acceptable: Material Symbols de Streamlit (`:material/bolt:`), però amb moderació i només en navegació.

### 6.8 To del text (català)
- Frases curtes, verb al principi, xifra concreta: *"Carrega al migdia, quan la xarxa emet un 35 % menys."*
- Sense "increïble", "potent", "intel·ligent", "IA". Sense exclamacions. Sense "Insights".
- Explicacions de l'escena per hora (substituir les actuals amb emojis):
  - Càrrega: *"Carrega 480 kW. Aquesta és la 3a hora més neta de les properes 24 h."*
  - Descàrrega: *"Descarrega 500 kW. Hora cara i bruta: el campus compra 500 kW menys a la xarxa."*
  - Espera: *"Espera. Moure energia ara perdria més (10 % per cicle) del que estalviaria."*
- Glossari d'un clic (expander): MPC, programació lineal, PVPC, intensitat de CO₂, SOC.

### 6.9 Proposta pàgina a pàgina

**Capçalera comuna (totes les pàgines):** nom del projecte a l'esquerra ("Bateria del Campus Nord · Tauler de decisions"), selector de període en `segmented_control` a la dreta, línia fina a sota. Res més.

**1. Resum — "Què ha de fer la UPC"** (la pàgina que el jurat ha de veure primer; una pantalla)
- Frase protagonista (Source Serif 4 o Plex 28 px): *"Operar la bateria amb control predictiu evita X t de CO₂ i Y k€ l'any, a Z % de l'òptim teòric."*
- KPI protagonista (40 px): **X t CO₂/any**; dos secundaris: **−Y % factura**, **puntuació 6,08 / oracle 6,08**; nota: "0 infraccions en 2.016 h".
- Quatre "fitxes de decisió" en **llista vertical** (no graella): pregunta · resposta d'una línia · mini‑gràfic (sparkline/minibarra) · enllaç a la pàgina. Les 4 preguntes: estratègia, horari, mida, fiabilitat.

**2. Operació en directe** — escena 3D (secció 5) a amplada completa, a sota la franja de 24 h + "per què", i el gràfic "campus amb i sense bateria" de 7 dies sincronitzat. Toggle 3D/2D.

**3. Estratègia** — barres ordenades amb oracle; dot plot CO₂ vs cost per estratègia; Sankey del període amb pèrdues; heatmap dia×hora de l'acció de la bateria.

**4. Dimensionament (què passaria si)** — sliders (capacitat, potència, pes CO₂, €/kWh) en una sola fila; corbes capacitat→t CO₂/any amb colze anotat i la configuració actual marcada; taula de retorn amb la fila recomanada destacada; resposta dinàmica.

**5. Fiabilitat i supòsits** — robustesa a l'error de previsió (línia + banda), estalvi per mes (consistència estacional), i una llista explícita de supòsits i límits (anualització lineal, sense degradació, preu PVPC, CO₂ de la xarxa peninsular). Coherència = honestedat sobre els límits.

---

## 7. Streamlit: detalls pràctics de polit i rendiment
- **`st.iframe`** substitueix `components.html` (deprecat a 1.56). Accepta string HTML, `Path` a un `.html`, o URL `/app/static/...`; `height="content"` pot autoajustar l'alçada amb HTML string — per a un canvas WebGL millor fixar‑la (p. ex. 760). Comprovat a la signatura instal·lada: `st.iframe(src, *, width='stretch', height='content', tab_index=None, alt=None)`.
- **Cache:** `@st.cache_data` per a simulacions (ja hi és); afegir `@st.cache_resource` per a cadenes grans (bundle JS, fonts base64). Precalcular **totes** les combinacions dels sliders del "què passaria si" a `data/processed/` abans de la demo (si no, el jurat espera).
- **`@st.fragment`** per a la secció de sliders, perquè moure un slider no re‑executi tota la pàgina (ni recreï l'iframe 3D).
- **Layout:** `layout="wide"` + `max-width` per CSS (1.240 px) perquè en pantalles grans les línies de text no s'estirin; `st.columns([2,1])` en lloc de columnes iguals quan hi ha jerarquia.
- **Pantalla de projector:** provar a 1.280×720 i 1.920×1.080; zoom del navegador 110–125 % si la sala és gran; mode clar.
- **Offline:** cap `https://` al HTML final (fer `grep -n "https://" dashboard/*.html` abans de la demo). Altair/Vega es serveixen des del paquet de Streamlit (no necessiten CDN).
- **Accés per URL** (si es vol mostrar al jurat després): Streamlit Community Cloud, però la demo en directe sempre local.

---

## 8. Llista de tasques prioritzada (~8 h, per impacte en el Tukey)

| Ordre | Tasca | Temps | Impacte | Criteri |
|---|---|---|---|---|
| 1 | Crear `dashboard/estil.py` (tokens de color, unitats, formatadors `fmt_kw`, `fmt_t`, `fmt_eur`) + registrar el tema Altair i passar `theme=None` a tots els `st.altair_chart` | 45 min | Molt alt | Coherència + adequació |
| 2 | `.streamlit/config.toml` + fonts locals a `dashboard/static/fonts/` + CSS mínim amb `st.html`; `toolbarMode="minimal"` | 30 min | Alt | Aspecte professional |
| 3 | Eliminar tots els emojis (títols, pestanyes, respostes, `explicacio()`, nodes de l'SVG); reescriure el copy amb títols d'acció | 40 min | Alt | Anti‑genèric |
| 4 | Pàgina **Resum** nova (frase protagonista, 1+2 KPIs, 4 fitxes de decisió verticals) | 60 min | Molt alt | Utilitat per decidir |
| 5 | Refer Q2 com a small multiples alineats (barres divergents + CO₂ + preu, mateix eix X) + heatmap dia×hora | 45 min | Alt | Adequació |
| 6 | Q1 amb oracle com a regla i etiquetes directes; Q3 amb colze anotat i fila recomanada destacada; Q4 amb banda | 45 min | Alt | Adequació + coherència |
| 7 | Bundle three.js 0.170.0 (esbuild) + `escena3d.html` amb terra, edificis, bateria escalada, 4 fluxos amb partícules, càmera isomètrica, play/pausa/scrub, fallback SVG | 2 h 30 | Mitjà‑alt (ganxo de demo) | Memorabilitat |
| 8 | Franja de previsió 24 h + "per què" dins de l'escena | 30 min | Alt | Utilitat (explica la decisió) |
| 9 | Pàgina **Fiabilitat i supòsits** + glossari | 30 min | Mitjà | Coherència |
| 10 | Sankey del període amb pèrdues | 30 min | Mitjà | Adequació |
| 11 | Repàs final: mateixes xifres a tot arreu (un sol `resultat` per període), arrodoniments, prova offline (wifi apagat), prova a Windows, prova al projector | 30 min | Molt alt | Coherència + risc demo |

Si el temps s'acaba: **fer 1–6 i 11 sempre**; el 3D (7–8) només si 1–6 estan acabats. Un dashboard 2D impecable i coherent guanya a un 3D espectacular amb incoherències.

**Guió de demo per al jurat (2 min):** Resum (la decisió i les xifres) → una fitxa (per què a aquestes hores) → Operació en directe (3D, saltar al "pic de CO₂ següent", veure la bateria descarregant i el cable de xarxa clarejant) → Dimensionament (moure €/kWh i veure canviar la recomanació) → Fiabilitat (què passa si les previsions fallen).

---

## 9. Fonts (llista completa)

**Disseny de dashboards i visualització**
- Tufte: https://www.edwardtufte.com/ · https://www.antoinebuteau.com/lessons-from-edward-tufte.md
- Few: https://www.perceptualedge.com/ · https://www.thedataschool.co.uk/anh-vu/are-you-making-these-13-dashboard-design-mistakes/ · https://www.thedataschool.co.uk/anh-vu/are-you-making-these-13-dashboard-design-mistakes-part-2 · https://uxmatters.com/mt/archives/2007/04/book-review-information-dashboard-design.php · https://speckyboy.com/designing-information-dashboards/
- Knaflic: https://www.storytellingwithdata.com/gallery · https://oreilly.com/library/view/storytelling-with-data/9781119621492 · https://chartio.com/blog/declutter-your-data-visualizations · https://www.thedataschool.co.uk/gabriela-scherbinek/context-and-focus-in-data-storytelling
- Datawrapper: https://www.datawrapper.de/blog/colors · https://www.datawrapper.de/blog/emphasize-with-color-in-data-visualizations · https://www.datawrapper.de/blog/10-ways-to-use-fewer-colors-in-your-data-visualizations · https://www.datawrapper.de/blog/beautifulcolors · https://www.datawrapper.de/blog/colors-for-data-vis-style-guides · https://www.datawrapper.de/blog/create-good-color-palettes · https://www.datawrapper.de/blog/background-color-of-data-visualizations
- FT Visual Vocabulary: https://github.com/Financial-Times/chart-doctor/blob/main/visual-vocabulary/README.md · https://ft-interactive.github.io/visual-vocabulary/
- Economist: https://d30jyndnpz0ndz.cloudfront.net/documents/CHARTstyleguide_20170505.pdf · https://thedataschool.co.uk/johann-shin/visual-storytelling-done-right-5-lessons-from-the-economist
- Altres guies: https://ons-design.notion.site/ONS-chart-style-guide-abc7605a97624dc2bc7f2a3e16379d82 · https://service-manual.ons.gov.uk/data-visualisation/build-specifications/typography · https://worldbank.github.io/data-visualization-style-guide/chartelements · https://analysisfunction.civilservice.gov.uk/policy-store/data-visualisation-charts · https://royal-statistical-society.github.io/datavisguide/docs/choosing.pdf · https://data.europa.eu/apps/data-visualisation-guide/choosing-charts-the-message · https://designsystem.maersk.com/guidelines/data-visualisation/chart-style-guide/ · https://nightingaledvs.com/data-journalism-colour-accessibility/ · https://pudding.cool/ · https://observablehq.com/plot/
- Senyals "IA": https://www.saasui.design/blog/saas-ui-looks-ai-generated · https://docs.bswen.com/blog/2026-03-20-ai-generated-ui-anti-patterns/ · https://docs.bswen.com/blog/2026-03-30-ai-frontend-design-unique · https://pub.towardsai.net/10-signs-of-ai-generated-design-and-how-to-make-yours-not-look-like-it-482ff7da81fc · https://medium.com/@Rythmuxdesigner/why-your-ai-generated-ui-looks-like-everyone-elses-and-how-to-break-the-pattern-7a3bf6b070be · https://cerebras.ai/blog/generating-beautiful-uis
- Color accessible: https://siegal.bio.nyu.edu/color-palette/ · https://rdrr.io/cran/khroma/f/vignettes/tol.Rmd · https://conceptviz.app/blog/okabe-ito-palette-hex-codes-complete-reference

**Referents d'energia**
- https://app.electricitymaps.com/map · https://electricitymaps.com/platform/map · https://electricityMap.org/methodology · https://techcrunch.com/2024/05/06/electricity-maps-calculates-the-carbon-intensity-of-electricity-consumption-to-optimize-usage-at-scale
- https://www.ree.es/es/datos · https://www.ree.es/en/datos/publications/news-todate/redata-is-now-part-of-all-our-lives-a-new-web-space · https://www.ree.es/en/node/1240 · https://www.ree.es/en/press-office/press-release/news/press-release/2025/02/red-electrica-expands-information-electricity-system-to-adapt-it-ecological-transition · https://vizzuality.com/project/red-electrica-de-espana
- https://www.gridstatus.io/ · https://docs.gridstatus.io/llms.txt · https://docs.gridstatus.io/changelog/may-2026/15-may-add-supply-and-demand-chart-to-ercot-live-page
- https://ember-energy.org/data/electricity-data-explorer/ · https://ember-energy.org/latest-updates/newsletter-ember-current-july-2025
- https://carbonintensity.org.uk/ · https://www.neso.energy/about/our-progress-towards-net-zero/carbon-intensity-app · https://neso.energy/future-energy/our-progress/carbon-intensity-dashboard
- https://www.tesla.com/support/energy/powerwall/mobile-app/energy-data · https://www.tesla.com/support/energy/powerwall/mobile-app/time-based-control-user-guide · https://www.podfeet.com/blog/2022/09/solar-batteries/ · https://www.github.com/reptilex/tesla-style-solar-power-card
- https://octopus.energy/smart/agile/
- https://flowcharts.llnl.gov/ · https://www.ans.org/news/article-461/llnl-expands-release-of-energy-flowcharts/

**3D / three.js**
- https://threejs.org/manual/en/installation · https://registry.npmjs.com/three · https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.min.js · https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/controls/OrbitControls.js
- https://discourse.threejs.org/t/importing-addons-without-npm/44471 · https://discourse.threejs.org/t/error-on-android-devices-failed-to-resolve-module-specifier-three/75607
- https://threejs.org/docs/pages/UnrealBloomPass.html · https://discourse.threejs.org/t/i-still-dont-get-how-unrealbloompass-works/57843 · https://discourse.threejs.org/t/unrealbloom-only-on-some-selected-objects/74587.md
- https://threejs.org/docs/pages/InstancedFlow.html · https://varun.ca/three-js-particles/ · https://discourse.threejs.org/t/make-particles-follow-a-path-issues/50633
- Mides mesurades: babylonjs@7.54.0 `babylon.js` (6,8 MB), deck.gl@9.1.14 `dist.min.js` (1,6 MB), plotly.js-dist-min@2.35.2 (4,6 MB), three@0.170.0 `three.module.min.js` (691 KB), three@0.184.0 `three.module.min.js` + `three.core.min.js` (365 + 384 KB).

**Streamlit / Altair / MIME**
- https://docs.streamlit.io/develop/concepts/configuration/theming-customize-fonts · https://docs.streamlit.io/develop/tutorials/configuration-and-theming/static-fonts · https://docs.streamlit.io/develop/tutorials/configuration-and-theming/variable-fonts · https://docs.streamlit.io/develop/concepts/configuration/theming-customize-colors-and-borders · https://docs.streamlit.io/develop/concepts/configuration/serving-static-files · https://docs.streamlit.io/develop/api-reference/custom-components/st.components.v1.html
- https://altair-viz.github.io/user_guide/generated/theme/altair.theme.register.html · https://altair-viz.github.io/user_guide/generated/theme/altair.theme.ThemeConfig.html · https://altair-viz.github.io/user_guide/customization.html
- https://docs.python.org/3/library/mimetypes · https://bugs.python.org/msg392294 · https://taricorp.net/2020/windows-mime-pitfalls/ · https://code.djangoproject.com/ticket/32041
