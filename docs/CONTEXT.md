# Context complet del repte (resum de TOT el que sabem)

Fonts: web https://repteupc.datathon.cat/ (5 pestanyes + FAQ), `docs/repte/` (enunciat oficial,
guia de variables, presentació PDF) i el codi oficial `starter_kit/environment.py`.
**Si hi ha contradiccions, mana `environment.py`** (és el que puntua).

## El problema
Bateria de 2.000 kWh, ±500 kW, rendiment 90 % (η_c = η_d = √0,9 ≈ 0,9487), SOC inicial 50 %,
sense degradació. Cada hora `act(obs)` retorna una potència en kW (+ carrega, − descarrega).
Xarxa: `grid = max(0, consum − solar + P_bateria)`. L'excedent exportat **no compta** (preu 0, CO₂ 0).

## Puntuació (environment.py)
```
Score = 100 · max(0, 0,7·ΔCO2 + 0,3·ΔCost − 0,002·Infraccions)
```
- ΔCO2 i ΔCost són relatius al campus SENSE bateria, sumats sobre tot el test.
- Cada infracció (demanar >500 kW o sortir de [0, 2000] kWh) = **−0,20 punts**.
  (L'enunciat .md i el PDF diuen −1,00; la web i el codi diuen −0,20. Igualment: 0 infraccions sempre.)
- Desempat: 1) score, 2) menys infraccions, 3) qui va enviar abans.
- **El jurat també valora la presentació, el raonament tècnic, l'anàlisi de dades i la justificació.**

## Què rep l'agent (obs)
`timestamp, hour, day_of_week, soc_kwh, soc_pct, soc_percent, preu_actual, co2_actual,
preus_properes_24h, co2_properes_24h` (24 valors **exactes**, comencen per l'hora actual),
`noves_dades_5min = {ultim_consum_kw, ultima_solar_kw}` (de l'hora anterior).
NO rep el consum ni la solar futurs.

## Test
- Últims 7 dies de cada mes (Set 2025 – Ago 2026), 12 setmanes ≈ 2.016 h, **concatenades** en una
  sola simulació (el SOC NO es reinicia entre setmanes; hi ha salts a `timestamp`).
- Leaderboard públic = 50 % de cada setmana; l'altre 50 % és privat i decideix al final.
- Al final de la simulació el vector de 24 h ve més curt (<24 valors) → senyal que s'acaba.

## Normes de lliurament
- `agent.py` sol, o `submission.zip` amb `agent.py` + fitxers (.pkl/.json/.py) **a l'arrel**.
- Màx 10 enviaments/dia, timeout 60 s, 25 MB. Nom d'equip + PIN (≥4 caràcters) + noms dels integrants.
- "Validació Ràpida" a la web és gratis (48 h de prova): fer-la servir sempre abans.
- Llibreries: numpy, pandas, scipy, scikit-learn, joblib, xgboost, lightgbm + stdlib de càlcul.
- **Prohibit** (escàner AST, veure `starter_kit/check_submission.py`): `os`, `sys`, `shutil`,
  `subprocess`, `socket`, `urllib`, `requests`, `http`, `importlib`, `inspect`, `threading`,
  `multiprocessing`, `eval`, `exec`, `compile`, `globals`, `__import__`... Carregar fitxers amb
  `Path(__file__).parent / "fitxer"`.

## Dades de train (data/raw/train)
~6.000 h (≈3 primeres setmanes de cada mes). Pipeline oficial a `src/data.py`.
- Consum = −`Contador - POTENCIA ACTIVA EXPORTADA (kW)`, clip [0, 5000], mitjana horària.
- Solar = suma dels 3 inversors (`POTENCIA ACTIVA`), mitjana horària.
- Preu PVPC (€/kWh) i CO₂ (kg/kWh) horaris.

## Fets que hem descobert analitzant les dades (veure DECISIONS.md)
1. Consum mitjà ≈ 1.120 kW; solar màx ≈ 145 kW (molt petita). **Consum net ≥ 500 kW el 99,5 % de les hores**
   → tot el que descarreguem es consumeix al campus; predir el consum gairebé no importa.
2. Preu i CO₂ correlacionen 0,58: el CO₂ és baix al migdia (solar peninsular) i alt a la nit/vespre;
   el preu és alt a les 19–22 h.
3. El consum de 0 h a 5 h és constant cada nit (artefacte del comptador). Hi ha forats de sensors
   (p. ex. 17/06/2026 amb consum 0).
4. Com que preu i CO₂ futurs són coneguts i el problema és lineal → **programació lineal (LP) + MPC**
   és pràcticament òptima: 6,08 al nostre VALID, igual que l'oracle amb informació perfecta.
