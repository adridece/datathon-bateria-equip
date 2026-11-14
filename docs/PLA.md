# Pla de treball (24 h) i idees per destacar

El score del leaderboard ja és pràcticament el màxim teòric (MPC-LP ≈ oracle). Com que **el jurat
decideix amb la presentació i el raonament**, la diferència la farem amb l'anàlisi i les idees.

## Feina pendent (repartiu-vos-la i marqueu qui la fa)
- [ ] Enviar `agents/mpc_lp` a la web (primer "Validació Ràpida") i apuntar el score a DIARI.md
- [ ] Ajustar `terminal` i `co2_ref/preu_ref` (validació creuada per mesos, sense sobreajustar)
- [ ] Cas consum net < 500 kW (caps de setmana assolellats): limitar la descàrrega amb una
      predicció del consum (LightGBM/estadística per hora i dia) → guanys petits però reals
- [ ] Frontera de Pareto CO₂ vs cost variant el pes (0,7/0,3 → 1/0 … 0/1): gràfic per a la presentació
- [ ] Anàlisi de sensibilitat de la bateria (capacitat 1–8 MWh, potència 250–1000 kW): quant CO₂ i €
      estalvia cada MWh extra → recomanació d'inversió per a UPC Sostenible
- [ ] Traduir els resultats a món real: tones de CO₂/any, € / any, equivalències (arbres, cotxes)
- [ ] Explicar per què el CO₂ és baix al migdia (solar peninsular) i com la bateria "trasllada" energia
- [ ] Notebook net d'EDA amb gràfics bonics (`notebooks/`)
- [ ] Presentació (diapositives) + guió
- [ ] Repo públic final amb `scripts/export_public.py`

## Idees "extra" per diferenciar-nos
- Dashboard interactiu (web) per simular la bateria amb diferents mides i pesos.
- Demostrar que el nostre agent és **òptim** (gap amb l'oracle ≈ 0 %) i explicar per què.
- Robustesa: què passa si les previsions de preu/CO₂ tinguessin error (soroll) → MPC segueix bé?
