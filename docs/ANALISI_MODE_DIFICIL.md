# Mode Difícil: anàlisi de dades i estratègia

Document per entendre (i explicar al jurat) com funciona el nostre agent del Mode Difícil i per què és així.
Totes les xifres es poden reproduir amb les comandes del final.

## 1. El problema
Al Mode Difícil la bateria és 3 vegades més gran (6.000 kWh, ±1.500 kW), hi ha 12 vegades més solar i de preu i CO₂
només sabem les 3 hores següents. L'agent decideix cada hora quanta energia carrega o descarrega per reduir
el CO₂ (70 % del pes) i la factura (30 %) del campus respecte de no tenir bateria.

## 2. Què diuen les dades
**El consum net canvia de signe al migdia** (`docs/figures/hard_01_consum_net.png`). Amb 12× solar, un 9 % de les hores
hi ha excedent (fins a 1.117 kW) que es pot guardar gratis. A la nit el consum net és ~1.000 kW, menys que la potència
de la bateria (1.500 kW): si descarreguem més del que consumeix el campus, l'energia sobrant es perd.
→ L'agent ha de saber **quant consumirà el campus aquesta hora**, no només quan és bruta la xarxa.

**La solar d'una hora la diu la irradiància de la mateixa hora** (`hard_02_solar_irradiancia.png`): correlació 0,995 i
error de 33 kW. Amb la irradiància de l'hora anterior l'error és de 192 kW (els núvols canvien d'una hora a l'altra).
→ Saber de quina hora és la irradiància que rep l'agent val molts punts (secció 5).

**El CO₂ té una forma diària clara però un nivell que canvia molt** (`hard_03_co2_hores.png`): baixa al migdia (solar
peninsular) i puja al vespre; la diferència entre l'hora més bruta i la més neta d'un dia és de 70 g/kWh de mediana.
→ Cal preveure el CO₂ més enllà de les 3 hores conegudes per saber quan descarregar.

## 3. Com mesurem sense enganyar-nos
Validar amb les mateixes dades amb què s'entrena dona xifres massa bones (20,9 en lloc de 18,9). Per això
`tests/bench_hard.py`:
- fa servir com a test l'última setmana de cada mes (F0), la d'abans (F1) i la d'abans encara (F2), com el test oficial;
- **entrena tots els models sense aquestes setmanes**;
- calcula l'òptim teòric (programació lineal sabent tot el futur) de les mateixes setmanes.

Regla: **un canvi només es queda si millora F0 i F1**, i F2 no es fa servir per decidir, només per comprovar al final.
Així evitem quedar-nos amb millores que només funcionen en unes setmanes concretes.

## 4. On són els punts (`hard_04_on_son_els_punts.png`)
Hem donat a l'agent `hard_final` informació perfecta peça a peça (validació F0):

| Què sabem perfecte | Puntuació | Guany |
|---|---|---|
| Res (agent real) | 18,80 | |
| CO₂ de les properes 24 h | 19,44 | +0,64 |
| Preu de les properes 24 h | 19,07 | +0,27 |
| Consum net de l'hora actual | 19,31 | +0,51 |
| Totes les previsions | 20,18 | +1,38 |
| Òptim teòric | 20,28 | |

**Conclusió:** amb previsions perfectes el mateix mètode arriba al 99,5 % de l'òptim. El mètode és bo; tot el que falta
és **error de previsió**, sobretot del CO₂ a +3..+8 h i de la solar de l'hora actual. Els marges de seguretat ja són als
millors valors (cap altre valor millora F0 i F1 alhora).

## 5. L'agent (`agents/hard_v3`) pas a pas
1. **Previsions.** Preu, CO₂, consum i solar de les properes 24 h amb una previsió senzilla (dies anteriors a la mateixa
   hora i perfils del train) corregida amb models LightGBM a les hores properes (feina de l'Ivan, `hard_final`).
2. **CO₂ +3..+12 h (nou).** Un model directe que mira la corba de les últimes 48 h, relativa a l'última hora coneguda
   (aprèn la forma, no el nivell). Es barreja meitat i meitat amb la previsió anterior: error −5/−6 %.
3. **Irradiància de l'hora actual (nou).** La web no diu si la irradiància de `obs` és de l'hora que comença o de la
   que acaba de passar. L'agent ho comprova sol comparant-la amb la solar de l'hora passada. Si és de l'hora actual,
   la solar d'ara = 1,629 × irradiància (ajustat amb el train) i el marge de seguretat baixa al 70 %.
   Si no ho és, l'agent fa exactament el mateix que abans: no hi perdem res.
4. **Pla.** Programació lineal de 24 h amb la xarxa dins del problema (aprofita l'excedent solar i no descarrega més del
   que es consumeix) i aplica només la primera hora; a l'hora següent torna a planificar.
5. **Seguretat.** No descarrega més del consum net que esperem amb un marge per a l'error de previsió de cada hora,
   i mai demana més potència ni energia de la que la bateria pot donar (0 infraccions a totes les validacions).

## 6. Resultats (banc honest)
| | F0 | F1 | F2 (reservada) |
|---|---|---|---|
| `hard_final` | 18,80 | 17,36 | 17,75 |
| `hard_v3`, si la irradiància és de l'hora passada | 18,88 | 17,42 | 17,92 |
| `hard_v3`, si la irradiància és de l'hora actual | 19,02 | 17,55 | 18,20 |
| Òptim teòric | 20,28 | 18,75 | – |

## 7. Què hem provat i descartat
| Idea | Per què no |
|---|---|
| Model de CO₂ fins a +18 h | millora F0 però empitjora F2 |
| CO₂ d'ahir i de fa una setmana a l'hora objectiu | +0,08 a F1 però −0,08 a F0 |
| Model directe de preu | +0,02, massa poc |
| Decidir amb escenaris (mitjana de diversos plans) | empitjora (18,68–18,85) |
| Donar valor a l'energia que queda al final del pla | no canvia res |
| Model propi de la solar de l'hora actual | −3/−6 % d'error, +0,03 |
| Dades de REE dels dies de test | prohibit: les previsions han de sortir de `data/train/` |
(L'Ivan en va provar més: veure `docs/DIARI.md`, 14/11 vespre i nit.)

## 8. Límits i generalització
- El sostre real a la web és ~24,7 (el nostre 22,96 era el 92,7 % de l'òptim): arribar a 25 no és possible ni sabent el futur.
- El rànquing públic fa servir la meitat de les setmanes de test; el privat, l'altra meitat. Ajustar-se al públic amb molts
  enviaments no generalitza. Nosaltres decidim només amb el banc honest.

## 9. Com reproduir-ho
```
python scripts/train_hard_v3.py        # entrena l'agent amb tot el train
python tests/bench_hard.py 0,1,2       # validació honesta i òptim teòric
python scripts/analysis_hard.py        # figures d'aquest document
python scripts/make_submission.py agents/hard_v3
```
