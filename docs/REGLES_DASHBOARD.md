# Regles del dashboard (versió curta)

Regles concretes per al dashboard web (`dashboard/`), destil·lades de totes les fonts revisades. Si alguna cosa
contradiu `RECERCA_DASHBOARD.md`, mana aquest document (és posterior i inclou les preferències de l'equip).
Objectiu: guanyar el Tukey → **útil per decidir, gràfic adequat a cada comparació, coherència de xifres**.

**Fonts** (entre claudàtors a cada regla):
[REC] `docs/RECERCA_DASHBOARD.md` · [EQ] preferències de l'equip (formes rodones, tema clar llegible) ·
[KPI] wshobson `kpi-dashboard-design` · [GRA] wshobson `grafana-dashboards` · [VDF] wshobson `visual-design-foundations` ·
[EMIL] `emil-design-eng` + `review-animations/STANDARDS.md` · [COR] `choreograph` ·
[3DL] `threejs-lighting` · [3DI] `threejs-interaction` · [3DP] `threejs-performance` · [IMP] `impeccable-lite`

## 1. Estructura d'app (una pantalla per vista)

1. **Res de scroll de pàgina.** `body` a `100vh`, cada vista cap sencera a 1440×900 i aguanta 1280×720 (projector). Si no hi cap, sobra contingut, no falta scroll. [REC §2.3.11] [IMP]
2. **Closca fixa:** barra lateral estreta (64–72 px, icones + etiqueta curta) amb les vistes; barra superior (56 px) amb el títol de la vista, el període i els controls globals (escenari, reproduir). El contingut no salta en canviar de vista. [EQ] [GRA]
3. **Una vista = una pregunta.** Ordre fix dins la vista: pregunta → resposta en una frase amb xifra → 1–2 gràfics d'evidència → línia de supòsits en gris. [REC §4.1]
4. **Graella de 12 columnes**, separació 16 px, marge 24 px. Peça protagonista (escena 3D o gràfic principal) de 7–8 columnes; la columna lateral porta KPI i explicació. [REC §2.3.12]
5. **Jerarquia, no mosaic:** xifres grans dalt → tendències al mig → detall (taules, heatmap) a baix o al hover. Una targeta protagonista més gran; mai 4 targetes idèntiques en fila com a única estructura. [GRA] [REC §2.3.5]
6. **Màxim 5–7 KPI per vista**; si n'hi ha més, van a una altra vista o al detall. [KPI]
7. Filtres i període són **globals** (barra superior) i s'apliquen a totes les peces de la vista alhora; mai un filtre amagat dins d'una sola targeta. [KPI] [GRA]

## 2. Targetes KPI (honestes)

1. Cada KPI = **etiqueta (què i unitat) + valor + comparació + període**. Ex.: «CO₂ evitat · 41 t/any · −12 % vs. sense bateria · estimat de 12 setmanes». Un número sol no ajuda a decidir. [REC §4.2] [KPI]
2. Valor en Plex Mono amb `tabular-nums`, 28–40 px; etiqueta 12–13 px en `--muted`. [REC §6.3]
3. **Comparació sempre contra una referència explícita** (sense bateria, plantilla o oracle) amb signe i fletxa. Color: accent si és el nostre resultat, tinta si és neutre. **Mai vermell/verd** per bo/dolent (daltonisme); el signe i el text ho diuen. [REC §6.1] — substitueix «red=bad, green=good» de [KPI].
4. **Sparkline honest:** dades reals sense suavitzar (res de `curveBasis`/spline), mateixa escala i període a totes les targetes que es comparen, punt final marcat, línia de referència fina si n'hi ha. Sense eixos però amb el rang al tooltip. [REC §2.3.10] [KPI]
5. Metodologia a un clic o hover («com es calcula»), no amagada. [KPI]
6. Precisió justa: % amb 1 decimal, kW/kWh sense decimals, € en k€, t CO₂ sense decimals. «0 infraccions» és una nota de garantia, no un KPI. [REC §2.3.9, §4.2]
7. Mètode USE adaptat a la bateria: **ús** (% del temps carregant/descarregant), **saturació** (hores a SoC 0 o 100 %), **errors** (infraccions). Bon complement de detall. [GRA]

## 3. Quin gràfic per a cada comparació

| Pregunta | Gràfic |
|---|---|
| Quina estratègia és millor (1 mètrica) | Barres horitzontals ordenades; nostre agent en accent, la resta en gris, oracle com a línia discontínua |
| CO₂ vs. cost per estratègia | Scatter de pocs punts etiquetats directament |
| Quan carrega/descarrega (24 h) | Barres divergents (+/−) amb CO₂ i preu en panells petits a sobre, mateix eix X |
| Patró dia × hora | Heatmap divergent de la potència de la bateria |
| Mida de bateria | Línies capacitat → resultat, colze anotat |
| Campus amb vs. sense bateria | Dues línies + àrea entre elles |
| Balanç d'energia | Sankey amb pèrdues visibles |
| Operació hora a hora | Escena 3D + franja de 24 h sincronitzada |

Regles comunes: títol = conclusió; etiquetes directes en lloc de llegenda; eix Y a zero a les barres; mateixa escala als
panells que es comparen; anotar dins el gràfic el que afirma el títol. **Res de gràfics 3D per comparar magnituds**: el 3D
explica l'operació, els números es llegeixen en 2D. [REC §4.4, §2.3] [KPI]

## 4. Tema clar: tokens

Colors (ja a `css/style.css`) i contrast mesurat (sobre blanc / sobre `--bg`):

| Token | Valor | Contrast | Ús permès |
|---|---|---|---|
| `--text` | `#1F2326` | 15,8 / 13,7 | Text, xifres |
| `--muted` | `#6E6A63` | 5,4 / 4,6 | Text secundari (aprova AA) |
| `--dim` | `#A19C93` | 2,7 / 2,4 | **Només decoració o desactivat, mai text que s'hagi de llegir** |
| `--accent` | `#0F7A62` | 5,3 / 4,6 | El nostre agent, botó principal |
| `--charge` / `--price` | `#0072B2` / `#7A5195` | 5,2 / 6,1 | Línies i text |
| `--discharge` | `#D55E00` | 3,9 / 3,3 | Formes i línies (≥3:1), no text petit |
| `--solar` | `#E69F00` | 2,3 / 2,0 | **Només farciment**; l'etiqueta va en `--text` al costat |

- Mínims: text 4,5:1, text gran i elements de gràfic 3:1. [VDF] Vores de controls interactius ≥3:1 (fer servir `--muted`,
  no `--line`). Les targetes es separen del fons per color + ombra suau, no per vora.
- **Escala de radis** (formes rodones [EQ], substitueix els 4–6 px de [REC §6.4]): `--r-xs 6px` (xips, tooltips),
  `--r-sm 10px` (botons quadrats, inputs), `--r-md 14px` (targetes petites, KPI), `--r-lg 20px` (panells grans, escena 3D),
  `--r-pill 999px` (botons de control, segmented). **Radi interior = radi exterior − padding** quan hi ha targetes dins de targetes.
- Ombra única i suau (la de `--shadow`); res d'ombres acolorides, degradats ni vidre esmerilat. [IMP] [REC §2.3.7]
- Espais en múltiples de 4 px; un sol accent; zero emojis. [REC §2.3]

## 5. Moviment

1. **Abans d'animar:** amb quina freqüència es veu i per a què serveix (retroacció, orientació, canvi d'estat). Si és «queda bonic» i es veu sovint, no s'anima. Tecla espai (play/pausa) i dreceres: **sense animació**. [EMIL]
2. **Corbes** (substituir l'actual `--ease`):
   `--ease-out: cubic-bezier(.23, 1, .32, 1)` (entrades, hover, premer) · `--ease-in-out: cubic-bezier(.77, 0, .175, 1)` (coses que es desplacen dins la pantalla, càmera 3D). **Mai `ease-in`** a la interfície. Moviment continu (partícules, barra de progrés): `linear`. [EMIL]
3. **Durades:** premer 120–160 ms · hover/color 150 ms · tooltip 125–200 ms · desplegable 150–250 ms · canvi de vista 200–250 ms · panell lateral/modal ≤350 ms · moviment de càmera 3D 600–900 ms (és explicatiu, l'excepció). Sortida més ràpida que l'entrada. [EMIL] [COR]
4. Només s'animen `transform` i `opacity` (i `clip-path` si cal). Mai `transition: all`, ni `width/height/top/left`. Preferir transicions CSS (interrompibles) a `@keyframes` per a coses que es repeteixen. [EMIL]
5. Botons: `transform: scale(.97)` a `:active`. Res surt de `scale(0)`: com a molt de `scale(.96)` + `opacity: 0`. Hover amb moviment només dins `@media (hover: hover) and (pointer: fine)`. [EMIL]
6. **Canvi de vista:** encreuament (la vella surt mentre la nova entra), la closca no es mou. **Una sola entrada per contenidor**: si el panell entra, el seu contingut ja hi és. Primera càrrega: KPI amb *stagger* de 30–80 ms no uniforme i total <300 ms; mai en canvis repetits. Res bloqueja els clics durant una animació. [COR]
7. Els números que canvien (comptadors, KPI) es poden interpolar ≤400 ms només quan canvia l'escenari; durant la reproducció s'actualitzen sense animació (si no, no es llegeixen). [EMIL]
8. **`prefers-reduced-motion: reduce`:** treure desplaçaments, *stagger*, auto-rotació i vol de càmera; mantenir fades curts i canvis de color; la reproducció comença en pausa. [EMIL] [COR]

## 6. Escena 3D llegible sobre fons clar

1. Fons de l'escena = color del panell (`--card` o `--soft`), no gris ni degradat. [REC §5.3]
2. **Llum:** `HemisphereLight` (cel blanc, terra `#D8D2C4`, 0,9–1,2) + una `DirectionalLight` (sol) amb ombra. Ombres suaus i clares (`shadow.intensity` ≈ 0,5 si la versió ho admet; si no, pujar la hemisfèrica), `normalBias ≈ 0,02` contra l'acne, càmera d'ombra ajustada al terreny, `mapSize` 2048. Sense HDR ni `RoomEnvironment`. [3DL] [REC §5.3]
3. **Ombres estàtiques:** `renderer.shadowMap.autoUpdate = false` i `needsUpdate = true` només quan el sol canvia d'hora. Sota la bateria i els edificis, una taca de contacte (pla amb degradat radial) per «assentar-los». [3DL] [3DP]
4. **Materials** mats: `MeshStandardMaterial({ roughness: .85–.95, metalness: 0 })`, colors de maqueta (paper/argila); el color fort només per al que té significat (fluxos, nivell de bateria, cable de xarxa per CO₂). [REC §5.3]
5. **Contorns:** `EdgesGeometry` + `LineSegments` d'1 px en un gris una mica més fosc que l'objecte (p. ex. `#BDB6A9`) als edificis: dona forma sobre fons clar sense post-procés. Res d'`OutlinePass` ni *bloom*. [3DL] (ús propi)
6. **Partícules sobre fons clar:** blending normal i colors saturats (Okabe-Ito); el *glow* additiu desapareix sobre blanc. [REC §5.3] adaptat
7. Color: `renderer.outputColorSpace = SRGBColorSpace`; si el to queda apagat, `NeutralToneMapping` o cap, **no ACES** (enfosqueix i dessatura el paper). [3DL]
8. **Etiquetes** en HTML sobre el canvas (posició amb `vector.project(camera)`), estil de tooltip (fons blanc, vora `--line`, `--r-xs`, xifres en mono). Màxim 3–4 visibles alhora; la resta al hover. [3DI] [REC §5.3]
9. Rendiment: `setPixelRatio(Math.min(devicePixelRatio, 2))`, una partícula = un `InstancedMesh` per flux, cap `new Vector3()` dins el bucle, pausar quan la pestanya no és visible, mesurar amb `renderer.info` (objectiu <100 crides de dibuix, 60 FPS). [3DP]
10. Càmera ortogràfica isomètrica, `OrbitControls` amb `enableDamping`, sense pan, angles i zoom limitats, botó «Vista inicial». Auto-rotació desactivada per defecte. [REC §5.3] [3DI]

## 7. Interacció

1. **Hover = detall, clic = selecció.** Raycast només contra una llista explícita d'objectes, punter relatiu al rectangle del canvas, cursor `pointer` quan hi ha alguna cosa a sota. [3DI] [3DP]
2. **Tooltip** igual a tot arreu (3D i gràfics): títol, valor + unitat, hora/període i comparació. Primer tooltip amb ~250 ms de retard; els següents instantanis mentre el ratolí es mou entre elements. [EMIL] [REC §5.3]
3. **Vinculació:** l'hora seleccionada (scrubber) mou alhora l'escena, la franja de 24 h i el cursor dels gràfics. Seleccionar un actor (bateria, xarxa…) el ressalta a tot arreu i atenua la resta a ~30 %. [REC §5.4]
4. Controls de reproducció: play/pausa (espai), velocitat (1×, 4×, 24×), salts a «següent pic de CO₂» i «següent càrrega». [REC §5.4]
5. Estats de focus visibles (`:focus-visible` amb anell d'accent de 2 px), tots els controls amb teclat, objectiu de clic ≥32 px. [VDF] [IMP]
6. Estat sense dades / sense WebGL: missatge clar i el *fallback* 2D, mai un panell buit. [REC §5.6]

## 8. Llista abans d'entregar

- [ ] Cada vista cap a 1280×720 sense scroll i respon una pregunta amb una frase i una xifra.
- [ ] Les mateixes xifres (CO₂, €, kWh) coincideixen a KPI, gràfics, 3D i presentació (font: simulador oficial).
- [ ] Cada KPI té unitat, comparació i període; cap vermell/verd per bo/dolent.
- [ ] Cap text en `--dim` ni en `--solar`; contrast revisat (4,5:1 text, 3:1 gràfics).
- [ ] Radis de l'escala, ombra única, un sol accent, zero emojis, títols-conclusió.
- [ ] Cap `transition: all`, cap `ease-in`, cap animació a la tecla espai; `prefers-reduced-motion` provat (DevTools → Rendering).
- [ ] Escena 3D: 60 FPS al portàtil de la demo, pausa en pestanya oculta, *fallback* 2D provat desactivant WebGL.
- [ ] Tooltips coherents a 3D i gràfics; scrubber sincronitza tot.
- [ ] Provat a Chrome i Edge (Windows) i Safari (Mac); consola sense errors.
- [ ] Passada final amb `review-animations` i amb la rúbrica de `impeccable-lite` (crítica).
