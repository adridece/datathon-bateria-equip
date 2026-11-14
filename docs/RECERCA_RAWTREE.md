# Recerca: side challenge "Best agentic use of RawTree" (Tinybird) — i pla per guanyar-lo

Data: 14/11/2026. Autor: recerca automàtica (fonts al final). Tot el que és **[verificat]** s'ha comprovat
llegint la documentació oficial o fent una crida real; el que és **[suposició]** cal confirmar-ho a l'estand.

---

## 0. Resum en 30 segons

- **RawTree és de Tinybird [verificat]**: és la seva nova base de dades OLAP *schema-free* per a dades
  semiestructurades, "built for agents". És un fork de ClickHouse: envies JSON, consultes amb SQL, sense
  definir esquemes. Web: https://rawtree.com · docs per a agents: https://rawtree.com/llms.txt
- La web que van ensenyar a l'obertura (fitxer de Drive "Còpia de index.html") s'ha pogut descarregar: és la
  presentació "RawTree Challenge · Datathon FME 2026" (repte principal de recomanació en temps real + aquest
  side challenge). El contingut útil està resumit a la secció 1.
- 4 superfícies: **API** `https://api.rawtree.com`, **CLI** `rtree`, **MCP** `https://mcp.rawtree.com/mcp`,
  **SDK TypeScript** `@rawtree/sdk` (no hi ha SDK de Python oficial → farem servir l'API REST amb `requests`).
- LLM: **HelmCode** és OpenAI-compatible [verificat]: `base_url = https://api.helmcode.com/v1`, clau a
  `HELMCODE_API_KEY` (a `.env`). Hem provat *tool calling* real amb `deepseek-v4-flash` i `glm5.3-flash`: tots
  dos retornen `tool_calls` correctes en format OpenAI.
- **Proposta guanyadora:** "**L'Operador del Campus**" — un agent LLM que gestiona l'energia de la UPC Campus Nord
  fent servir RawTree com a memòria i cervell analític: decideix què ingerir, es fa preguntes en SQL, detecta
  anomalies, fa *what-ifs*, decideix el pla de bateria de demà (amb el nostre LP com a eina), escriu
  l'informe/alerta i **l'endemà s'autoavalua** comparant pla vs realitat dins de RawTree.
- Repo **separat** del repte principal. Pla de construcció de ~5 h a la secció 7.

---

## 1. Què és RawTree exactament

### 1.1 Qui i què
- Producte de **Tinybird** (empresa de dades en temps real sobre ClickHouse; "8 anys, >1 PB/dia" segons la
  presentació). El canal de Discord "tinybird" quadra. [verificat a la presentació i a la web]
- Definició oficial: *"RawTree is the cloud database for raw analytical data. A schema-free OLAP database that
  adapts to your workloads. Send raw events or telemetry as JSON, query with SQL."*
- Punts clau:
  1. **Schema-free sense perdre rendiment**: insereixes JSON i consultes a l'instant. Les taules es creen soles
     amb el primer insert. Cada camp és de tipus `Dynamic` (cada valor guarda el seu tipus).
  2. **S'adapta a la càrrega**: claus d'ordenació i projeccions automàtiques segons les consultes reals.
  3. **Compatible amb ClickHouse**: SQL de ClickHouse (funcions de finestra, `quantile`, `toStartOfHour`...).
  4. Extres: **Handlers** (endpoints HTTP definits amb SQL), **SQL workflows** (consultes programades amb cron i
     *sinks* HTTP / taula / Slack), connectors (Kafka, OTLP/OpenTelemetry, Prometheus, Splunk, CDC), logs d'API.
- Servei: RawTree Cloud i BYOC. Jerarquia: organització → clúster → base de dades → taula.
- **Preu / free tier:** no hi ha pàgina de preus pública llegible (la web és una SPA amb login). A la Datathon
  **cada equip rep una clau gratuïta a l'estand de RawTree** (`TEAM_ID` + `RAWTREE_API_KEY`), que pot llegir
  la base `shop` i **llegir/escriure la seva base `team_NN`**. Per al side challenge: demanar a l'estand si podem
  fer servir aquesta clau (o un compte propi a https://rawtree.com/login) per a dades d'energia. [suposició: sí]

### 1.2 Autenticació
- Capçalera `Authorization: Bearer rt_...` (API, CLI, MCP local, MCP hostatjat amb clau).
- Variables d'entorn recomanades per la doc: `RAWTREE_API_KEY`, `RAWTREE_DATABASE`, `RAWTREE_ORG`.
  Al nostre repo nou: `RAWTREE_API_KEY`, `RAWTREE_DATABASE=team_NN` (o la que ens donin), `HELMCODE_API_KEY`.
- Permisos de clau: `read_only`, `write_only`, `read_write`, `admin`. **Crear handlers i workflows requereix
  `admin`** → probablement la clau d'equip NO ho permet (veure riscos).

### 1.3 CLI (`rtree`)
```bash
curl -fsSL https://rawtree.com/install.sh | bash      # instal·lar
rtree login                                           # OAuth (o: rtree login --api-key rt_...)
rtree status --json                                   # comprovar org/clúster/base
rtree insert --table events --data '[{"a":1},{"a":2}]' --json
rtree insert --table events --file ./events.jsonl     # també --url https://...
rtree query --json "SELECT count() FROM events"
# amb la clau d'equip de la Datathon (exemple del README oficial):
rtree query --api-key $RAWTREE_API_KEY --database $TEAM_ID "SELECT count() FROM shop.requests"
rtree feedback --category bug --actor-type agent ...  # l'agent pot enviar feedback (punt de "story")
```

### 1.4 API REST (base `https://api.rawtree.com`)
| Acció | Endpoint |
|---|---|
| Ingerir JSON (objecte o array) | `POST /v1/tables/{table}?database=team_NN` |
| Consultar SQL | `POST /v1/query?database=team_NN` cos `{"sql": "...", "format": "JSON"}` |
| Formatar/validar SQL sense executar | `POST /v1/query-format` |
| Llistar / crear handlers (endpoints SQL) | `GET/POST /v1/handlers` · invocar `GET /v1/handlers/{url}?param=...` |
| Workflows programats | `POST /v1/workflows?organization=..&cluster=..` · run `POST /v1/workflows/{id}/runs` |
| Logs de peticions | `GET /v1/logs?start_time=..&end_time=..&limit=50` |
| OpenAPI completa | https://rawtree.com/openapi.json |

Resposta de query (format JSON per defecte): `{"meta":[...], "data":[{...}], "rows":N, "statistics":{...}}`.
Resposta d'insert: `{"read_rows":"2","written_rows":"2", ...}` (comptadors com a string).
Límits: insert ≤100 MiB i 1.000 req/s per taula; query ≤30 s d'execució per defecte, resultat ≤100 MiB; `429`
amb `retry-after`.

**SQL amb camps `Dynamic` (important!)**: per fer joins, agregats o comparacions fiables cal fer *cast*:
`load_kw::Float64`, `accurateCastOrNull(x,'Float64')`, `parseDateTimeBestEffort(ts::String)`,
`product_id::String`. Per auditar tipus: `SELECT dynamicType(x), count() ... GROUP BY 1`.

### 1.5 Exemple mínim en Python (ingest + query) — `requests`
```python
import os, requests
API = "https://api.rawtree.com"
H = {"Authorization": f"Bearer {os.environ['RAWTREE_API_KEY']}", "Content-Type": "application/json"}
DB = os.environ.get("RAWTREE_DATABASE", "team_NN")

def insert(table, rows):
    r = requests.post(f"{API}/v1/tables/{table}", params={"database": DB}, headers=H, json=rows, timeout=30)
    r.raise_for_status(); return r.json()["written_rows"]

def query(sql):
    r = requests.post(f"{API}/v1/query", params={"database": DB}, headers=H, json={"sql": sql}, timeout=60)
    if r.status_code >= 400: return {"error": r.text[:2000]}   # retornar l'error a l'LLM perquè corregeixi
    return r.json()["data"]

insert("telemetry", [{"ts": "2026-06-17T10:00:00", "load_kw": 1130.5, "pv_kw": 98.2}])
print(query("SELECT toHour(parseDateTimeBestEffort(ts::String)) h, avg(load_kw::Float64) "
            "FROM telemetry GROUP BY h ORDER BY h LIMIT 24"))
```

### 1.6 MCP
- Hostatjat: `https://mcp.rawtree.com/mcp` (Streamable HTTP, OAuth o Bearer).
  - Claude Code: `claude mcp add --transport http rawtree https://mcp.rawtree.com/mcp --header "Authorization: Bearer rt_xxx"`
  - Codex: `codex mcp add rawtree --url https://mcp.rawtree.com/mcp`
- Local: `npx -y @rawtree/mcp` amb `RAWTREE_API_KEY` (repo `rawtreedb/rawtree-mcp`).
- Eines: `run-query`, `insert-json`, `insert-from-url`, `list-tables`, `create-table`, `describe-table`,
  `delete-table`, `list-logs`, `list-databases`, + gestió d'org/clústers/apps/claus.
- Skill per a agents: `npx skills add rawtreedb/agent-skills` (SKILL.md amb patrons de CLI/API/SQL/Dynamic).

### 1.7 SDK
- Només TypeScript: `@rawtree/sdk` (`new RawTree({apiKey}).insert({table, values})`, `.query({sql})`).
  Python → API REST directa (molt simple, secció 1.5).

---

## 2. Exemples públics d'agents amb RawTree / Tinybird MCP
- `rawtreedb/examples` (carpetes `open-agents`, `otel`, `sandboxes`, `postgres`): exemples oficials.
- `rawtreedb/pi-observability`: exporta les traces d'un agent (model, tool calls) a RawTree via OTLP →
  idea que reaprofitem: **l'agent guarda la seva pròpia traça a RawTree**.
- `rawtreedb/rawtree-showroom`, `rawtree-web-analytics`, `jev-pr-quality` (dashboard multi-repo).
- `rawtreedb/datathon-fme-2026`: starter kit del repte principal (bucle *pull → predict → push* en Python).
- Tinybird (producte germà): snippets d'agents amb MCP (OpenAI Agents SDK, Pydantic AI, Agno), "10 analytics
  agents examples you can copy", agent amb OpenAI Agent Builder + MCP. Mateixa filosofia: agent + SQL + MCP.

---

## 3. El nostre context i l'LLM (HelmCode)
- Projecte principal: controlador de bateria (2 MWh, ±500 kW, η=0,9) per a la UPC Campus Nord amb dades horàries
  de consum, solar, preu PVPC i CO₂ (`data/processed/hourly.csv`, ~6.000 h, columnes
  `Fecha, load_kw, pv_kw, precio_eur_per_kwh, co2_kg_per_kwh, irr_wm2, temp_c`) i un agent LP-MPC
  (`agents/estandard_lp/agent.py`, `params.json`). Fets útils per a la història: consum nocturn 0–5 h constant
  (artefacte del comptador), forats de sensor (p. ex. 17/06/2026 amb consum 0), CO₂ baix al migdia, preu alt
  19–22 h, consum net ≥500 kW el 99,5 % de les hores.
- **HelmCode** [verificat]:
  - Base URL `https://api.helmcode.com/v1`, OpenAI-compatible (`/chat/completions`, `/models`, `/embeddings`),
    capçalera `Authorization: Bearer $HELMCODE_API_KEY`. Variable al `.env`: **`HELMCODE_API_KEY`** (no copiar-la).
  - Models que retorna `/v1/models` amb la nostra clau: `deepseek-v4-flash`, `glm5.3-flash`, `glm5.3`, `qwen3.6`,
    `gemma4`, `qwen3-embedding`, `rerank`, `kokoro` (TTS), `whisper`, i frontier (Claude/GPT/Gemini, de pagament
    amb crèdit — no fer-los servir).
  - Recomanació: **`deepseek-v4-flash`** (agentic, tool calling natiu, 1M context) amb `reasoning_effort:"low"`
    per velocitat; alternativa `glm5.3-flash`. `qwen3.6`/`gemma4` fan tool calling en XML → evitar.
  - Prova feta: amb una eina `run_sql`, tots dos models han retornat `tool_calls` vàlids.
  - Extra per a la demo: `kokoro` pot llegir en veu alta l'informe final (efecte "operador que parla").
- Snippet:
```python
from openai import OpenAI   # o requests directe
llm = OpenAI(base_url="https://api.helmcode.com/v1", api_key=os.environ["HELMCODE_API_KEY"])
resp = llm.chat.completions.create(model="deepseek-v4-flash", messages=msgs, tools=TOOLS,
                                   reasoning_effort="low")
```

---

## 4. Idees de projecte

### Idea A — "L'Operador del Campus" (RECOMANADA)
Un agent que fa de **cap de sala d'operacions energètiques** del Campus Nord. Cada "nit" (en mode replay, un dia
del 2026 rere l'altre) arriba nova telemetria a una *landing zone* (fitxers crus: comptador, inversors, PVPC,
CO₂, meteo). L'agent decideix què ingerir a RawTree i com, interroga les dades en SQL, detecta anomalies,
compara escenaris, **decideix el pla de bateria de demà** (cridant el nostre LP com a eina) i publica un informe +
alertes. L'endemà llegeix de RawTree què va passar de veritat i **aprèn** (escriu lliçons a `agent_memory`).

### Idea B — "Científic de bateries"
Agent que fa recerca autònoma sobre el repte principal: llança simulacions (estratègies, pesos CO₂/cost, mida de
bateria), ingereix cada resultat a RawTree, formula hipòtesis en SQL ("quines setmanes perd l'LP vs l'oracle?") i
decideix el següent experiment. Bona ciència, però és més "AutoML amb base de dades" i menys "operador real".

### Idea C — "Auditor de comptadors"
Agent de qualitat de dades: ingereix les sèries crues 5-min, troba artefactes (consum nocturn constant, zeros,
salts), crea vistes netes i endpoints (handlers) i obre "tiquets" a una taula. Petit i útil però amb poca acció.

**Elecció: A**, absorbint el millor de B (what-ifs) i C (anomalies) com a eines/passos de l'operador. Motius:
encaixa literalment amb "store, analyse **and act**", té protagonista clar, un bucle temporal que es pot ensenyar
en 2 minuts i un final emocional (diners i CO₂ estalviats, alerta real del 17/06/2026).

---

## 5. Disseny de la Idea A

### 5.1 Arquitectura
```
 landing/ (fitxers crus del dia D)          ┌──────────────────── RawTree (base team_NN) ───────────────────┐
  meter_5min.csv  inverters.csv             │ telemetry_raw   telemetry_hourly   market (preu, CO2 24h)     │
  pvpc_D+1.json   co2_D+1.json  meteo.json  │ anomalies       battery_plan       outcomes (pla vs real)     │
        │                                   │ agent_memory    agent_trace (cada tool call)  reports         │
        ▼                                   └──────────────▲──────────────────────────────▲─────────────────┘
 ┌──────────────┐  tool calls (JSON)  ┌──────────────────┐ │ POST /v1/tables, /v1/query  │ (opcional)
 │ LLM HelmCode │◀───────────────────▶│ Runtime de l'agent│─┘                              │ MCP a Claude Code
 │ deepseek-v4- │   respostes/errors  │ (Python, ~300 l.) │──▶ plan_battery() = el nostre LP (scipy)
 │ flash        │                     │ guardrails SQL    │──▶ reports/D.md + alerta (stdout/Slack/TTS)
 └──────────────┘                     └──────────────────┘
        ▲                                     │
        └──── replay clock: "avui és D 23:00" ─┘  (simulator.py avança un dia i deixa fitxers nous a landing/)
```

### 5.2 Eines que l'agent pot cridar (function calling)
| Eina | Què fa | Superfície RawTree |
|---|---|---|
| `list_landing()` | Llista fitxers nous amb mida, columnes i 3 files de mostra | — |
| `ingest(file, table, transform)` | Ingesta un fitxer (o un subconjunt/agregat que l'agent tria: `raw`, `hourly_mean`, `drop_zeros`) a la taula que l'agent decideix | `POST /v1/tables/{t}` |
| `list_tables()` / `describe(table)` | Què hi ha a la base i quins tipus | `SHOW TABLES`, `DESCRIBE` via `/v1/query` |
| `sql(query)` | Consulta de lectura (SELECT/WITH/DESCRIBE), `LIMIT` obligatori, errors retornats a l'LLM | `POST /v1/query` |
| `plan_battery(date, w_co2, reserve_kwh)` | Executa el nostre LP amb preus/CO₂ de demà llegits **de RawTree** i el consum previst que l'agent ha calculat en SQL; retorna potència horària, SOC i estalvi esperat | lectura RawTree + scipy |
| `commit_plan(plan_id)` | Guarda el pla escollit a `battery_plan` | `POST /v1/tables/battery_plan` |
| `raise_alert(severity, msg, evidence_sql)` | Insereix a `anomalies` i ho mostra (opcional Slack/TTS) | insert |
| `remember(lesson)` | Escriu una lliçó a `agent_memory` (es llegeix al començament de cada dia) | insert |
| `publish_endpoint(name, sql)` (opcional) | Crea un *handler* `/v1/handlers/...` p. ex. `/campus/plan-dema` | `POST /v1/handlers` (cal admin) |
| `write_report(markdown)` | Informe diari a `reports/` i a la taula `reports` | insert |

Totes les crides es registren a `agent_trace` (ts, dia, pas, eina, arguments, ms, ok) → **la traça de l'agent
també és una taula de RawTree** que es pot consultar a la demo ("què ha fet l'agent avui?").

### 5.3 El bucle de l'agent (per dia simulat D)
1. **Recordar**: llegeix `agent_memory` i el resultat d'ahir (`outcomes`) amb SQL.
2. **Decidir què ingerir**: `list_landing()` → tria fonts i granularitat (p. ex. no ingereix 5-min de meteo
   perquè mai l'ha fet servir; agrega el comptador a horari; manté cru el dia que veu zeros per tenir evidència).
3. **Preguntar** (3–8 SQL lliures que decideix ell): perfil d'avui vs mitjana del mateix dia de la setmana,
   detecció de consum 0 o pla nocturn, hores més netes i més cares de demà, error de previsió d'ahir.
4. **What-if**: crida `plan_battery` amb 2–3 configuracions (p. ex. pes CO₂ 0,7 vs 1,0; reserva si hi ha dubte
   de sensor) i compara l'estalvi esperat.
5. **Actuar**: `commit_plan`, `raise_alert` si cal (p. ex. "el comptador marca 0 kW de 10 a 14 h: dada
   impossible, el pla de demà fa servir la previsió de dimarts passat"), `write_report`, `remember`.
6. **Tancar el dia**: el simulador revela la realitat de D+1, el runtime calcula `outcomes` (cost i CO₂ reals
   amb el pla vs sense bateria) i passa al dia següent.
Límits: màx. 20 tool calls per dia, només SELECT a `sql()`, timeouts, i un *fallback* determinista (LP per
defecte) si l'LLM falla → el campus mai queda sense pla.

### 5.4 Per què "l'agent és el protagonista, no un embolcall"
- El codi **no** té un pipeline fix: l'agent tria fonts, taules, consultes i paràmetres; el runtime només
  executa eines. Ho demostrem a la demo mostrant dos dies diferents amb decisions diferents (traça a RawTree).
- L'LP és una eina (com una calculadora), però **quina** configuració s'aplica, amb **quines** dades i què es
  comunica ho decideix l'agent a partir del que ha preguntat a RawTree.
- Memòria persistent i autoavaluació a RawTree: l'agent millora d'un dia a l'altre.

### 5.5 Guió de la demo (2 minuts)
- **0:00–0:15 — Ganxo**: "La UPC té una bateria de 2 MWh. Qui la decideix cada nit? Un operador. Nosaltres
  l'hem substituït per un agent que viu dins de RawTree." Pantalla: dashboard RawTree buit.
- **0:15–0:45 — Dia 1 en directe** (terminal a l'esquerra, consultes a la dreta): l'agent llista fitxers,
  decideix ingerir-ne 3 de 5 i explica per què; fa 4 SQL; crida 2 what-ifs; tria el pla.
- **0:45–1:10 — El moment "wow"**: dia 17/06/2026, el comptador marca 0. L'agent ho detecta amb SQL, aixeca
  una alerta amb l'evidència (la consulta exacta) i protegeix el pla. (Opcional: la veu `kokoro` llegeix l'alerta.)
- **1:10–1:35 — Aprèn**: l'endemà llegeix `outcomes`, veu que va sobreestimar la solar i escriu una lliçó a
  `agent_memory`; el pla següent ja la fa servir.
- **1:35–2:00 — Tancament**: una consulta a `agent_trace` + `outcomes`: "en 14 dies l'agent ha fet N consultes,
  M ingestes, X € i Y kg CO₂ estalviats; tot és SQL, tot és a RawTree". Opcional: en Claude Code amb el MCP de
  RawTree preguntem "per què va canviar el pla el 17/06?" i respon llegint `agent_trace`.
Gravar-lo (QuickTime/OBS) com a vídeo de seguretat i enllaçar-lo al README.

### 5.6 Esquema del README
1. Títol + una frase: "An AI energy operator that runs a 2 MWh campus battery on top of RawTree."
2. GIF/vídeo de 2 min.
3. La història (UPC Campus Nord, per què importa: CO₂ i diners).
4. Com funciona: diagrama + bucle de 6 passos + taula d'eines → quina superfície RawTree fa servir cadascuna.
5. Què decideix l'agent (exemples reals de la traça, dos dies diferents).
6. Taules a RawTree i 5 consultes per explorar-les (copiar/enganxar).
7. Resultats: € i kg CO₂ vs sense bateria, nombre d'anomalies trobades.
8. Execució: `cp .env.example .env`, `pip install -r requirements.txt`, `python run.py --days 2026-06-15..2026-06-20`.
9. Seguretat i límits (només SELECT, budget de passos, fallback determinista).
10. Crèdits: equip, Datathon FME 2026, RawTree/Tinybird, HelmCode, dades UPC.

### 5.7 Angle de la història
"**De les dades crues a la decisió, sense humans al mig.**" RawTree diu ser "la base de dades per a dades crues
pensada per a agents"; nosaltres ho portem a un sistema físic real: un campus universitari i una bateria
d'1 M€. L'agent no només consulta: **decideix què guardar, desconfia de les dades, actua i aprèn**, i tota la
seva vida (dades, decisions, errors, lliçons) queda a RawTree consultable en SQL. Petit (≈400 línies), honest,
amb impacte mesurable (€ i CO₂).

### 5.8 Riscos i mitigacions
| Risc | Mitigació |
|---|---|
| La clau d'equip només permet escriure a taules existents (`scratch`) | Provar en 1 min `insert` a una taula nova. Si falla: tot a `team_NN.scratch` amb camp `kind` (schema-free ho fa trivial) o demanar compte propi a l'estand |
| Handlers/workflows requereixen `admin` | Són opcionals; si no, "endpoint" = taula `reports` + consulta guardada a `agent_memory` |
| Barrejar dades d'energia amb el repte de recomanació / compartir clau | Preguntar a l'estand si podem usar la clau per al side challenge; base/taules amb prefix `energy_`; la clau no surt mai del `.env` |
| L'LLM fa SQL incorrecte amb camps `Dynamic` | Prompt de sistema amb les regles de cast (`::Float64`, `parseDateTimeBestEffort(ts::String)`), retornar l'error a l'LLM, 2 reintents |
| LLM lent o caigut durant la demo | `reasoning_effort:"low"`, timeout 60 s, vídeo pregravat, mode `--replay-trace` que reprodueix una traça guardada |
| Bucle infinit / massa crides | Màx. 20 tool calls/dia i 3 what-ifs |
| Sembla un "wrapper" | Mostrar dos dies amb decisions diferents i la traça a `agent_trace`; el codi no té ordre fix d'eines |
| Temps (només ~5 h) | Retallar: sense handlers, sense TTS, 5 dies de replay |
| Fuita de claus al repo públic | `.env` a `.gitignore`, `.env.example` amb noms buits, `git grep rt_ sk-` abans de publicar |
| Confusió amb el repte principal (normes AST) | Repo separat; aquí sí es permeten `requests`/`openai`/`os` |

---

## 6. Estructura del repo nou (separat!) — p. ex. `campus-operator-rawtree`
```
campus-operator-rawtree/
  README.md  .env.example  .gitignore  requirements.txt   # requests, openai (opcional), pandas, numpy, scipy
  rawtree.py       # insert(), query(), describe(), log_trace() — ~60 línies
  tools.py         # eines + esquemes JSON per a function calling + guardrails SQL
  planner.py       # LP de bateria (copiat/adaptat de agents/estandard_lp/agent.py)
  simulator.py     # rellotge de replay: genera landing/ del dia D a partir de hourly.csv (+ 5-min crus si cal)
  agent.py         # bucle LLM (HelmCode) amb tool calling, prompt de sistema
  run.py           # CLI: --days, --model, --replay-trace
  prompts/system.md
  reports/         # informes diaris generats
  demo/            # vídeo/GIF + consultes de la demo
```
Prompt de sistema (resum): rol d'operador, objectiu (0,7·CO₂ + 0,3·cost), regles de RawTree (casts, `LIMIT`,
només lectura via `sql`), límits físics de la bateria, "explica cada decisió en una frase", "si una dada és
impossible, aixeca una alerta amb la consulta com a evidència".

---

## 7. Pla de construcció (~5 h, 2 persones en paral·lel)

| Hora | Persona 1 (infra + RawTree) | Persona 2 (agent + història) |
|---|---|---|
| 0:00–0:20 | Estand RawTree: onboarding, confirmar ús de la clau i si es poden crear taules/handlers. `rtree` instal·lat, `rtree status --json` | Crear repo, `.env.example`, `.gitignore`, `requirements.txt` |
| 0:20–1:00 | `rawtree.py` (insert/query/trace) + prova d'insert de `hourly.csv` d'una setmana; consulta de comprovació amb casts | `simulator.py`: dia D → `landing/` (meter, pv, preus/CO₂ D+1, meteo) i revelació de la realitat de D+1 |
| 1:00–2:00 | `planner.py`: adaptar el nostre LP (scipy `linprog`) com a funció pura `plan(prices, co2, load_fc, pv_fc, soc0, w_co2, reserve)` | `tools.py` + `agent.py`: bucle OpenAI-compatible amb HelmCode (`deepseek-v4-flash`), 6 eines bàsiques, límit de passos, guardrail SQL |
| 2:00–2:45 | Taules `outcomes` (càlcul pla vs real vs sense bateria) i `agent_memory`; fallback determinista | Prompt de sistema; primer dia complet de punta a punta; corregir errors de casts |
| 2:45–3:30 | Escollir 5–7 dies de replay que incloguin el 17/06/2026 (anomalia); executar-los | `raise_alert`, `write_report`, `remember`; comprovar que l'agent canvia de decisió entre dies |
| 3:30–4:15 | (Opcional) `publish_endpoint` si la clau és admin; (opcional) MCP a Claude Code per a la pregunta final de la demo | README complet amb resultats reals i consultes d'exemple |
| 4:15–5:00 | Gravar la demo de 2 min + `--replay-trace` de seguretat | Assajar el guió; revisar que no hi ha claus al repo; publicar el repo |

Definició de "fet": `python run.py --days 2026-06-15..2026-06-19` funciona sol, deixa 6+ taules a RawTree,
informes a `reports/`, una alerta el 17/06 i una lliçó a `agent_memory`; README + vídeo enllaçats.

---

## 8. Fonts
- Presentació de l'obertura (Drive, "Còpia de index.html"): https://drive.google.com/file/d/1t8RDXXDl62aPnBZZcW-rer1sU-kKSSkA/
- RawTree (web): https://rawtree.com · docs per a agents: https://rawtree.com/llms.txt · corpus: https://rawtree.com/docs/llms.txt
- Introducció: https://rawtree.com/docs.md
- Quickstart agents: https://rawtree.com/docs/quickstart/agents.md
- Quickstart API: https://rawtree.com/docs/quickstart/api.md
- Quickstart CLI: https://rawtree.com/docs/quickstart/cli.md
- MCP: https://rawtree.com/docs/reference/mcp.md
- Autenticació per a agents: https://rawtree.com/auth.md · https://rawtree.com/docs/reference/authentication.md
- Query API (+ handlers SQL): https://rawtree.com/docs/reference/api/query.md
- Handlers: https://rawtree.com/docs/reference/api/handlers.md
- Tables API: https://rawtree.com/docs/reference/api/tables.md
- Ingest: https://rawtree.com/docs/guides/ingest/ingest-data.md
- SQL workflows: https://rawtree.com/docs/concepts/sql-workflows.md · https://rawtree.com/docs/guides/transform/workflows.md
- Límits: https://rawtree.com/docs/reference/limits.md
- OpenAPI: https://rawtree.com/openapi.json
- Skill per a agents: https://github.com/rawtreedb/agent-skills/blob/main/skills/rawtree/SKILL.md
- CLI: https://github.com/rawtreedb/rawtree-cli · MCP: https://github.com/rawtreedb/rawtree-mcp · SDK TS: https://github.com/rawtreedb/rawtree-sdk-typescript
- Exemples: https://github.com/rawtreedb/examples · https://github.com/rawtreedb/pi-observability · https://github.com/rawtreedb/rawtree-showroom
- Starter kit Datathon: https://github.com/rawtreedb/datathon-fme-2026 · pàgina: https://datathon.rawtree.dev
- Menció prèvia de RawTree (Tinybird): https://nl.linkedin.com/in/maksim-kita
- Tinybird MCP / agents: https://guides.tinybird.co/docs/analytics-agents/mcp-server-snippets · https://guides.tinybird.co/blog/10-analytics-agents-examples-you-can-copy · https://www.tinybird.co/blog/how-to-build-an-analytics-agent-with-agno-and-tinybird-step-by-step · https://guides.tinybird.co/blog/openai-agent-builder-tinybird-mcp-building-a-data-driven-agent-workflow
- HelmCode: https://helmcode.com/docs · models: https://helmcode.com/docs/models · autenticació: https://helmcode.com/docs/authentication · exemples: https://helmcode.com/docs/examples
