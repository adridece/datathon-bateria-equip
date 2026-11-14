 # Preguntes del Jurat i Respostes - Datathon FME 2026

Aquest document conté les 15 preguntes més difícils o "trampa" que ens pot fer el jurat, juntament amb la resposta ideal que qualsevol membre de l'equip hauria de saber defensar.

### 1. Per què vau triar Programació Lineal (LP) i no Machine Learning o Aprenentatge per Reforç (RL)?
**Resposta:** Perquè l'enunciat ens diu que els preus i el CO2 es coneixen amb 24 hores d'antelació de forma determinista. El Machine Learning serveix per deduir patrons ocults o predir el futur, i l'Aprenentatge per Reforç necessita explorar i sovint comet errors per aprendre. Com que aquí no hem d'endevinar el preu (ja ens el donen), és un problema purament matemàtic on la LP ens garanteix l'òptim global sense efectes "caixa negra".

### 2. Què passa si les previsions oficials de preu o CO2 canvien o s'equivoquen a meitat del dia?
**Resposta:** Exactament per això utilitzem l'enfocament MPC (Control Predictiu Basat en Model). Si féssim un pla a les 00:00 per a tot el dia, ens menjaríem l'error. Però com que recalculem les 24 hores següents *a cada hora*, l'agent llegeix les dades actualitzades i reajusta la decisió de la bateria instantàniament.

### 3. Com esteu tan segurs que el vostre model és realment "òptim"?
**Resposta:** Ho sabem empíricament i matemàticament. Empíricament, perquè la nostra simulació treu un 6.08, que és un empat tècnic absolut amb el teòric Oracle. Matemàticament, perquè utilitzem l'algorisme HiGHS (Mètode del Punt Interior / Simplex) de SciPy, que demostrablement troba el mínim global absolut per a problemes lineals convexos com aquest.

### 4. Per què calculeu 24 hores d'optimització (LP) si després llenceu 23 hores i només executeu la primera (MPC)? No és ineficient?
**Resposta:** Computacionalment no és ineficient perquè optimitzar 48 variables lineals triga només uns mil·lisegons. Necessitem mirar 24 hores cap endavant per evitar que l'agent sigui "miop". Si només miréssim 2 hores endavant, l'agent podria descarregar la bateria ara perquè el preu és alt, ignorant que d'aquí a 10 hores hi haurà un pic de preu/CO2 encara pitjor on realment faria falta la bateria.

### 5. Què passaria si el mètode matemàtic `linprog` falla per un error de llibreria o falta de memòria en el servidor?
**Resposta:** L'Iván va preveure aquest risc dissenyant un sistema de *fallback*. El codi està dins d'un bloc `try/except`. Si falla l'optimitzador matemàtic, l'agent no peta (el que ens donaria un 0), sinó que executa la `backup_rule`, una regla senzilla basada en els percentils del dia: càrrega en el 25% de les hores més barates/netes, i descarrega en el 25% de les més cares/brutes.

### 6. Heu parlat de 0 infraccions. Python és conegut per tenir problemes d'arrodoniment amb els decimals (precisió de punt flotant). Com eviteu que la bateria marqui 2000.0001 kWh i us penalitzin?
**Resposta:** Tenim un *safety clamp* al codi just abans de retornar la potència. A més d'imposar uns límits estrictes entre 0 i PMAX, fem servir una variable de marge minúscula anomenada `EPS = 1e-3`. A l'hora de calcular els límits de capacitat, obliguem l'agent a aturar-se una mil·lèsima per sota de la capacitat màxima, per evitar l'error de punt flotant de Python.

### 7. Com gestioneu els valors nuls o erronis (NaNs) que poden arribar dels sensors?
**Resposta:** Tenim la funció `clean_list`. Quan arriba la llista de dades externes, si detecta un valor buit, NaN, o infinit, el descarta i fa el que s'anomena un *forward fill*: arrossega l'últim valor numèric vàlid que teníem. Creiem que en inèrcia tèrmica i mercats elèctrics és l'enfocament més realista de recuperar un sensor caigut.

### 8. El consum net del campus decau dràsticament a l'agost. Com es comportaria l'agent si gairebé no hi ha consum?
**Resposta:** Aquesta és la funció estrella de la nostra estratègia: el `max_dis_now`. A cada hora, mesurem el consum net de la UPC (Consum - Solar). Si a l'agost és només de 150 kW, aquest valor passa a ser el límit de descàrrega de la bateria en aquella hora. L'agent es bloqueja a si mateix per no donar 500 kW, evitant abocar energia a la xarxa, cosa que no puntua.

### 9. Què és exactament la variable ETA i com heu modelat el rendiment del 90%?
**Resposta:** L'enunciat deia que un cicle complet (carregar i descarregar) té una eficiència del 90%. Per fer-ho matemàticament just i simètric, la nostra constant `ETA` és l'arrel quadrada de 0.9. Multipliquem per aquest factor al carregar (perdem una mica), i dividim per aquest factor al descarregar (tornem a perdre una mica). Això suma exactament la pèrdua del 10% per cicle complet.

### 10. Heu tingut en compte la degradació física de la bateria a base de fer cicles complets diàriament?
**Resposta:** En aquesta competició, l'enunciat no penalitzava la degradació de la bateria, només l'eficiència, per tant no ho hem limitat per maximitzar la nota. En un entorn de producció real, simplement afegiríem una petita penalització econòmica al cost d'ús a la funció objectiu per evitar cicles innecessaris en hores on el guany econòmic/ambiental és gairebé zero.

### 11. Com es combinava la reducció del 70% de CO2 i el 30% del cost en el vostre algorisme matemàtic?
**Resposta:** Vam normalitzar les dues mètriques. Com que el preu va en euros (ex: 0.15) i el CO2 en kg (ex: 0.09), sumats directament tenen pesos asimètrics. Els dividim per les seves mitjanes històriques per convertir-los en índexs relatius, i llavors multipliquem l'índex de CO2 per 0.7 i el del preu per 0.3. Això crea un sol vector (el vector `w`, o *cost*), i el nostre optimitzador es limita a minimitzar aquest número.

### 12. Què passaria si la universitat instal·la moltes més plaques solars i el consum net passa a ser negatiu molt sovint, fins i tot a l'hivern?
**Resposta:** El nostre model sobreviuria sense tocar ni una línia de codi. La variable de bloqueig `max(net, 0.0)` forçaria que les descàrregues fossin de 0.0 kW a totes aquelles hores diürnes de gran producció. L'agent aprendria ell sol, gràcies a l'optimitzador, a carregar als migdies i a guardar la bateria exclusivament per a les nits, quan el consum net tornés a ser positiu.

### 13. El vostre codi podria funcionar bé instal·lat directament en el maquinari d'una bateria (al costat del quadre elèctric)?
**Resposta:** Sí, i tant. No necessitem superordinadors ni targetes gràfiques per executar xarxes neuronals gegants. L'optimitzador HiGHS està escrit en C++ i Python només actua de pont. Podríem tenir el nostre agent funcionant en una simple Raspberry Pi connectada al router de la bateria, reaccionant en mil·lisegons.

### 14. Què ha aportat l'Adrià amb el Dashboard si ja teníeu el codi d'optimització resolt a la terminal?
**Resposta:** Ha aportat la capa de negoci i usabilitat. Treballar a cegues al terminal fa difícil detectar patrons. El dashboard ens va permetre, durant la fase de desenvolupament, veure en directe els gràfics de l'Estat de Càrrega (SOC) per validar que la teoria matemàtica s'aplicava correctament. A més, és l'eina definitiva que entregaries a un gestor de la universitat; ells no llegiran codi, faran servir el dashboard.

### 15. Com podeu assegurar que al descarregar a l'hora següent, l'energia no anirà destinada a despeses fútils de la universitat?
**Resposta:** No ho podem garantir físicament (no controlem si algú es deixa l'aire condicionat encès), però ens enfoquem en l'origen de la generació. Si no usem la bateria, aquesta energia provindria del mix elèctric de la xarxa durant les hores de major contaminació o preu (centrals de cicle combinat, carbó a països veïns, etc.). El nostre objectiu és desplaçar el consum per consumir més energia verda, sigui pel que sigui que s'estigui gastant.

