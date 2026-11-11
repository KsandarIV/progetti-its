# ML per la cybersicurezza: "Operazione Nebbia"

Challenge del modulo "AI 4 Security" (Leonardo), ITS. **Lavoro di gruppo (3 persone).**

## Il compito
Un'azienda simulata ha 8 server. Bisognava consegnare:
1. un **detector di anomalie** sulla telemetria CPU/RAM al minuto (14 giorni di storico);
2. un **piano di patch** che ordina le vulnerabilità aperte (CVSS, EPSS, criticità del server) entro un budget di 20 ore.

Il notebook di partenza, con le parti da completare, era fornito dal docente. La consegna è stata provata su un incidente di 48 ore mai visto dalla squadra.

## Cosa contiene il notebook
- Esplorazione degli episodi storici, confronto feriali/weekend e fasce orarie; i deploy delle 10:00 non vanno segnalati come anomalie.
- Detector: z-score robusto (mediana e MAD) per server, tipo di giorno e fascia oraria, finestre mobili, poi Isolation Forest.
- Soglia scelta come compromesso: al massimo 9 allarmi al giorno (media 4,1, budget 30), nessun allarme sui deploy, tutti e 6 gli episodi storici rilevati.
- Piano di patch con regressione logistica sulla probabilità di sfruttamento, ordinato per rischio atteso per ora di lavoro.

Limite: soglia e addestramento sono stati scelti sugli stessi dati del kit, senza una validazione esterna.

## Il mio contributo — Aleksandar Savov
Nel gruppo non c'erano ruoli netti. Io mi sono occupato soprattutto di:
- coordinare il team;
- capire gli esercizi e spiegarli al gruppo;
- coinvolgere tutti e chiedere una partecipazione attiva.

Tecnologie: Python, pandas, NumPy, matplotlib, scikit-learn.
