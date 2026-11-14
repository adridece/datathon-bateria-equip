# Com treballem en equip (llegiu-ho tots)

## La idea
No ens repartim "trossos" d'una mateixa cosa: **cadascú porta un bloc sencer i independent**, a la
seva pròpia carpeta, perquè puguem avançar tots alhora sense trepitjar-nos. Les feines més difícils
les porten l'Adrià i l'Ivan (tenen l'assistent més potent); les altres són igual d'importants per
guanyar, perquè **el jurat decideix amb la presentació i l'anàlisi**.

Tot el que fem va al mateix repo privat. El que s'entrega acaba al repo públic al final.

## Rols i blocs (cadascú, la seva carpeta)
| Qui | Bloc | Carpeta | Què ha de quedar fet |
|---|---|---|---|
| **Adrià** | Dashboard en temps real (web amb 3D) | `dashboard/` | App que reprodueix l'agent hora a hora: fletxes d'energia, bateria omplint-se, gràfics, comptadors d'estalvi, comparativa i "què passaria si" |
| **Ivan** | Agent perfecte i robust + imprevistos | `agents/` + `tests/` | Agent final sense cap error possible (veure `docs/RISCOS.md`), proves automàtiques, ajust de paràmetres sense sobreajustar, enviament a la web |
| **Jesús** | Anàlisi de dades i resultats per a la presentació | `notebooks/` + `docs/figures/` | Notebook d'EDA amb gràfics nets, frontera CO₂ vs cost, sensibilitat de la mida de la bateria, xifres reals (tones CO₂/any, €/any) |
| **Martí** | Presentació i història | `presentacio/` | Guió + diapositives, explicació senzilla de l'estratègia, pràctica de la defensa, preguntes probables del jurat, revisió del repo públic |

Si algú acaba, ajuda el bloc que vagi més endarrerit (pregunteu-ho pel grup).

## Normes per no fer-nos nosa
0. **Cadascú a la seva branca** (`dashboard`, `agent`, `analisi`, `presentacio`); `main` només rep el que ja funciona,
   via *Pull Request* a GitHub (pas a pas a `docs/GUIA_EQUIP.md`, secció 5).
1. **`git pull origin main` abans de començar** i **`git push` sovint** (cada cop que una cosa funciona).
2. **Només toqueu la vostra carpeta.** Si cal canviar alguna cosa compartida (`src/`, `docs/`, el README),
   aviseu pel grup abans.
3. Tota decisió → `docs/DECISIONS.md`. Tot resultat → `docs/DIARI.md`. Escriviu-hi a sota de tot,
   amb el vostre nom.
4. **Enviaments a la web: només l'Ivan** (i avisant el grup), per no gastar els 10 intents diaris.
   L'agent `agents/mpc_lp` ja està validat a la web (dry-run OK, 0 infraccions).
5. Cap rastre d'assistents de codi enlloc (normes a `AGENTS.md`).

## Punts de control (24 h)
| Quan | Què ha d'estar fet |
|---|---|
| +3 h | Tothom amb l'entorn funcionant i el seu bloc començat |
| +8 h | Primera versió de cada bloc (fea però funcional) |
| +14 h | Agent final congelat. Dashboard i gràfics complets |
| +18 h | Diapositives acabades. Assaig de la presentació |
| +21 h | Repo públic generat i revisat (`scripts/export_public.py`) |
| +23 h | Res de nou: només repassar i arreglar errors |

## Side challenges
Veure `docs/SIDE_CHALLENGES.md` (Tukey Commission = dashboard; Tinybird/RawTree = agent d'IA).
**Recordeu: per recollir premis cal anar com a mínim a una xerrada.**
