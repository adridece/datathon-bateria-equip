# Guia pas a pas per a Linux (des de zero)

Versió de `docs/GUIA_EQUIP.md` només per a Linux (Ubuntu / Debian).

Aquesta guia suposa que **no saps res**. Segueix els passos en ordre i no te'n saltis cap.
Si alguna cosa falla, copia el missatge d'error i passa'l al teu assistent de codi, o pregunta al grup.

---

## 0. Què estem fent (en 1 minut)
El campus té una bateria gegant. Cada hora hem de decidir si **carrega**, **descarrega** o **no fa res**.
- Carregar quan l'electricitat és **neta i barata**.
- Descarregar quan és **bruta i cara** (així el campus compra menys de la xarxa en aquelles hores).

El nostre programa (l'"agent") pren aquesta decisió cada hora. La web del repte el prova amb dades
secretes i ens dona una puntuació. Com més CO₂ i diners estalviem, més punts.

---

## 1. Instal·lar els programes (només el primer cop)

1. Obre la **Terminal** (Ctrl + Alt + T).
2. Instal·la Python, l'entorn virtual i Git:
   ```
   sudo apt update
   sudo apt install python3 python3-venv python3-pip git
   ```
3. Comprova: `python3 --version` (ha de ser 3.10 o més nou) i `git --version`.
   > Serveix el Python 3.10, 3.11 o 3.12 que porta el sistema; no cal instal·lar-ne cap altre.
4. **Editor recomanat:** Visual Studio Code → https://code.visualstudio.com/ (paquet `.deb`).

---

## 2. Acceptar la invitació i baixar el projecte (només el primer cop)
1. Mira el correu: t'ha arribat una invitació de GitHub al repo `datathon-bateria-equip`. Accepta-la
   (si no tens compte de GitHub, crea-te'n un amb el mateix correu).
2. A la Terminal, ves a on vulguis guardar el projecte (p. ex. Documents) i clona'l:
   ```
   cd Documents
   git clone https://github.com/adridece/datathon-bateria-equip.git
   cd datathon-bateria-equip
   ```
   La primera vegada et demanarà iniciar sessió a GitHub (s'obre el navegador).
3. Digues-li a git qui ets (perquè els teus canvis surtin amb el teu nom):
   ```
   git config user.name "El Teu Nom i Cognom"
   git config user.email "el-teu-correu@exemple.com"
   ```

---

## 3. Preparar l'entorn de Python (només el primer cop)
Un "entorn virtual" (`.venv`) és una carpeta amb les llibreries del projecte, separades de la resta.

**Linux (Terminal, dins la carpeta del projecte):**
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/setup.py
```

Sabràs que l'entorn està actiu perquè a l'inici de la línia surt `(.venv)`.
**Cada cop que obris una terminal nova** has de tornar a activar-lo (`source .venv/bin/activate`).

La clau de l'API d'OpenCode: fes `cp .env.example .env`, obre `.env` i enganxa-hi la clau
(és al Discord). **Mai la pugis a GitHub** (el `.env` ja està ignorat).

---

## 4. Comprovar que tot funciona
```
python -m src.evaluate agents/mpc_lp
```
Ha de sortir alguna cosa com `VALID (7d/mes) ... 'score': 6.08 ... 'infraccions': 0`. Si és així, ja ho tens tot a punt.

---

## 4b. Provar el dashboard (ARA: abans d'ajuntar-lo a `main`)
```
git fetch
git checkout dashboard
pip install -r requirements.txt
streamlit run dashboard/app.py
```
S'obre sol al navegador (http://localhost:8501). El primer cop tarda ~2 minuts (fa els càlculs).
Què has de mirar:
- Les 5 pàgines de dalt: Resum, Operació en directe, Estratègia, Dimensionament i Fiabilitat.
- A **Operació en directe**, la vista 3D: gira la càmera arrossegant amb el ratolí, prem **Reproduir**,
  prem **Presentació guiada** (o la tecla P) i passa el ratolí per sobre dels edificis.
- Si el 3D no es veu, desactiva "Vista 3D" i comprova que l'esquema 2D funciona.

Per parar-lo: `Ctrl + C`. Després torna a la teva branca: `git checkout analisi` (Jesús) o
`git checkout presentacio` (Martí). Si alguna cosa falla, envia una captura o l'error de la terminal pel grup.

---

## 5. Com treballem cada dia: les BRANQUES (el cicle)
Una **branca** és una còpia del projecte on pots treballar sense espatllar la dels altres.
- `main` = la versió **bona i estable**. Ningú hi treballa directament.
- Cada bloc té la seva branca: `dashboard` (Adrià), `agent` (Ivan), `analisi` (Jesús), `presentacio` (Martí).

**Primer cop** (canviar a la teva branca, p. ex. `analisi`):
```
git fetch
git checkout analisi
```
**Cada vegada que treballis:**
1. Comprova que ets a la teva branca: `git branch` (la teva té un `*` al davant).
2. Porta't les novetats de `main` (perquè no et quedis enrere):
   ```
   git pull origin main
   ```
3. Treballa, prova (`python -m src.evaluate ...`) i apunta-ho a `docs/DIARI.md` / `docs/DECISIONS.md`.
4. Desa i puja **a la teva branca**:
   ```
   git add .
   git commit -m "Explicació curta del que has fet"
   git push
   ```
**Quan una cosa ja funciona bé i la vols passar a `main`:**
1. Ves a https://github.com/adridece/datathon-bateria-equip → surt un botó groc **"Compare & pull request"**
   (o pestanya *Pull requests* → *New pull request* → base: `main`, compare: la teva branca).
2. Escriu què has fet i crea-la. L'Adrià o l'Ivan la revisen i premen **"Merge"**.
3. Aviseu pel grup: "he passat X a main". Els altres fan `git pull origin main` a la seva branca.

> Si surt un **conflicte** (dues persones han canviat la mateixa línia): no t'espantis, no esborris res i
> demana ajuda al grup o al teu assistent: "tinc un conflicte de git, ajuda'm a resoldre'l pas a pas".

## 6. Com enviar un agent a la web (puntuació oficial)
1. Crea el zip i valida'l: `python scripts/make_submission.py agents/mpc_lp`
   → ha de dir **"LA SOLUCIÓ ÉS VÀLIDA"**. El zip queda a la carpeta `submissions/`.
2. Obre https://repteupc.datathon.cat/ → pestanya **"Lliurament de Solucions"**.
3. Omple: **Nom de l'equip** (sempre el mateix!), **PIN** (el de l'equip, el guarda l'Adrià; no el
   poseu a GitHub) i, només el primer cop, els **noms dels 4 integrants**.
4. A "Arxiu de la solució" → **Browse files** → tria el zip de `submissions/`.
5. Prem **"🧪 Validació Ràpida"** (gratis). Si surt bé →
6. Prem **"🚀 Trametre al Leaderboard"** (gasta 1 dels 10 intents diaris de TOT l'equip:
   **aviseu al grup abans d'enviar**).
7. Mira la nota a "Classificació General (Leaderboard)" i apunta-la a `docs/DIARI.md`.

---

## 7. Com fer servir el teu assistent de codi (Claude, Gemini, OpenCode...)
- Obre'l **dins la carpeta del projecte**. Llegirà sol el fitxer `AGENTS.md` (Claude i Gemini també,
  a través de `CLAUDE.md` / `GEMINI.md`), on hi ha les normes i tot el context.
- Primer missatge recomanat: *"Llegeix AGENTS.md i tots els documents de docs/ i explica'm on estem
  i què queda per fer."*
- Demana-li sempre que t'**expliqui** el que fa i per què, i que ho apunti a `docs/`.

---

## 8. On és cada cosa
| Vull... | Mira... |
|---|---|
| Entendre el repte | `docs/CONTEXT.md` |
| Saber per què hem fet les coses | `docs/DECISIONS.md` |
| Veure resultats i enviaments | `docs/DIARI.md` |
| Saber què queda per fer | `docs/PLA.md` |
| El nostre agent | `agents/mpc_lp/agent.py` |
| Material oficial (no tocar) | `starter_kit/`, `docs/repte/` |

## 9. Glossari ràpid
- **SOC**: quanta energia té la bateria (0 a 2.000 kWh).
- **kW / kWh**: potència (velocitat) / energia (quantitat). 500 kW durant 1 h = 500 kWh.
- **PVPC**: preu de la llum per hores (€/kWh).
- **CO₂ (kg/kWh)**: quanta contaminació fa cada kWh de la xarxa aquella hora.
- **LP (programació lineal)**: mètode matemàtic que troba la millor decisió possible quan tot és "lineal".
- **MPC**: planificar les properes 24 h, fer només la primera hora i tornar a planificar.
- **Oracle**: agent "trampós" que coneix tot el futur; serveix per saber el màxim possible.
