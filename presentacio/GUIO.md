 # Guió de la Presentació - Datathon FME 2026

**Durada estimada:** 5 - 7 minuts
**Ponent:** Marti Montemayor (amb suport visual de l'equip)
**To:** Segur, tècnic però entenedor, natural (estudiants de 2n).

---

## Diapositiva 1: Títol i Equip (0:30 minuts)
**Objectiu:** Trencar el gel i marcar la nostra filosofia.

"Bona tarda a tothom. Som l'Adrià, l'Iván, el Jesús i jo. Avui us presentem la nostra proposta per a l'optimització intel·ligent de les bateries del campus de la UPC. Des del minut u, la nostra filosofia ha estat prioritzar la seguretat, l'eficiència i la transparència matemàtica per sobre de la complexitat innecessària. Us expliquem com ho hem fet."

---

## Diapositiva 2: El Repte i la Realitat (1:00 minut)
**Objectiu:** Demostrar que hem analitzat les dades abans de picar codi.

"El nostre objectiu era clar: reduir l'impacte ambiental (un 70% de la nota) i minimitzar la factura elèctrica (un 30%). 

Abans de programar res, el Jesús va analitzar l'històric de dades i va detectar una realitat clau, que podeu veure en aquest gràfic: el consum net del campus pràcticament sempre supera els 500 kW. Com que la nostra bateria té una potència màxima de 500 kW, això va canviar les regles del joc. Ens vam adonar que no necessitàvem models complexos per predir el consum exacte del campus, perquè pràcticament tota l'energia que la bateria pugui descarregar, el campus se l'empassarà sense abocar-la a la xarxa."

---

## Diapositiva 3: L'Estratègia: IA vs Matemàtiques (1:00 minut)
**Objectiu:** Justificar per què NO fem servir Machine Learning, demostrant criteri.

"Amb aquesta informació, ens vam plantejar com atacar el problema. L'impuls inicial en una Datathon sol ser llançar-hi Xarxes Neuronals o *Reinforcement Learning*. Però vam pensar: per què fer servir models opacs i caixes negres quan les dades de preus i el CO2 ja ens les donen oficialment amb 24 hores d'antelació?

Vam descartar la IA i vam apostar per la Programació Lineal (LP). Com que tenim les dades, es converteix en un problema determinista. Les matemàtiques pures ens donen el que la IA no pot garantir en un entorn crític: solucions 100% òptimes, traçables i explicables."

---

## Diapositiva 4: L'Arquitectura i el MPC (1:15 minuts)
**Objectiu:** Explicar el "core" del codi (LP + MPC + max_dis_now) de forma molt senzilla.

"El cervell del nostre agent funciona com el GPS del cotxe, usant una estratègia anomenada MPC (Control Predictiu Basat en Model). Funciona així: cada hora, el nostre optimitzador matemàtic calcula el pla perfecte per a les properes 24 hores. Però nosaltres **només executem la decisió de la primera hora**. A l'hora següent, ho tornem a recalcular tot des de zero amb dades fresques.

A més, l'Iván va dissenyar un escut de seguretat fonamental al codi: la variable `max_dis_now`. Abans de moure un sol kilowatt, l'agent llegeix el consum net instantani del campus. Si per casualitat un diumenge el consum és molt baix, bloqueja la descàrrega per assegurar-nos que no regalem ni una gota d'energia gratuïtament a la xarxa elèctrica."

---

## Diapositiva 5: Resultats: 0 Infraccions (0:45 minuts)
**Objectiu:** Treure pit dels resultats i de la robustesa del sistema.

"I tota aquesta estratègia ha donat els seus fruits. A la simulació final, el nostre agent assoleix una puntuació de 6.08, aconseguint un empat tècnic absolut amb el model teòric perfecte (l'Oracle). 

Però el que ens fa estar més orgullosos com a equip no és només l'estalvi, sinó la fiabilitat: hem comès **0 infraccions**. Hem implementat uns topalls físics al codi (uns *safety clamps*) que fan que sigui matemàticament impossible que la bateria intenti descarregar quan està buida o carregar quan està plena, evitant qualsevol penalització."

---

## Diapositiva 6: Demo en Directe (1:00 minut)
**Objectiu:** Mostrar la feina del dashboard i que el codi és usable.

"Per a nosaltres, un bon algorisme de res serveix si no és usable. L'Adrià ha muntat aquest dashboard interactiu perquè els gestors energètics de la UPC puguin veure l'agent treballant en temps real. 

*(Assenyalar la pantalla / fer que l'Adrià mogui el ratolí)* 
Com podeu veure aquí, comprovem visualment com la bateria es carrega de nit o a les hores de vall de CO2, i com es buida estratègicament en els pics, mostrant-nos en tot moment l'estat de càrrega de manera intuïtiva."

---

## Diapositiva 7: Impacte Real i Next Steps (0:30 minuts)
**Objectiu:** Tancar la presentació amb visió de futur.

"En conclusió, avui no us entreguem una 'caixa negra' experimental, sinó un sistema robust, segur i matemàticament òptim que la UPC podria posar en producció demà mateix sense risc de trencar cap bateria. 

Si haguéssim tingut més temps, el nostre següent pas (els *Next Steps*) seria connectar l'agent a una API meteorològica pròpia per hiper-localitzar la previsió de generació solar del campus i refinar encara més aquell límit de seguretat del consum net.

Moltes gràcies per la vostra atenció. Som tot orelles per a qualsevol pregunta que ens vulgueu fer."

