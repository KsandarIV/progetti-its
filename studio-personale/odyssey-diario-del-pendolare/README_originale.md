# DEFINIZIONI GENERALI

## Progetto

Applicazione web su google app script (.html e .gs (javascript)) che interagisce con un foglio (google fogli >! d'ora in poi quando scrivo foglio indicherò sempre il file in questione <

### 1. Google Fogli

Abbiamo 3 fogli:  >! **nomi case sensitive, cioè scritti esattamente come sono sul foglio**<

- dataset → il database, con tutte le colonne e i dati che ci interessano
- PALETTE → la palette che ci interessa ed è la base su cui lavorare (sia dataset che webapp, per ora contiene solo la palette usata nel google fogli)
- definizioni

### 2. Web App

Gestione di backend e frontend

#### 2.1. BACKEND

- Gestione calcoli colonne automatiche (vedi punti successivi per la definizione del dataset)
- Gestione foglio PALETTE → In una futura release/versione dovremmo creare una palette per il dataset e una per la web app, cambiando il foglio PALETTE, si modificano anche i css e vari .html
- Gestione di un foglio per una futura release/versione per calcolare i vari totali, fare grafici etc → DATA ANALYSIS
- Gestione degli inserimenti automatizzati
- Gestione degli inserimenti derivati dalla web app

#### 2.2. FRONTEND

- 2 modalità diverse

  - VISUALIZZAZIONE E MODIFICA DATASET (modalità da implementare nella v4 stabile)
    - > fin quando non verrà realizzata questa parte stabile dell'app non possiamo considerarci nella v4
      >
  - INSERIMENTO DATI (BASEdella web app)
- Grafica DARK/NEON
- Schermate semplici e intuitive che rendono le interazioni minimali ma efficaci, per gli inserimenti/modifiche

> RIF.: DiarioDelPendolare\docs\IADependencies\UI_STORYBOARD.md

##### 2.2.1 INSERIMENTO DATI → ODYSSEY EPI >!EPI == episodio< [da rivalutare bene i nomi]

2.2.1.1 Livello grafico (.html)

- Schermata Home → due bottoni per le due modalità, qui si documenta solo la **modalità EPI**
- Schermata con griglia dei giorni, clicco un giorno →
- Schermata viaggi
  - Viaggi frequenti, mappati con le tratte →
  - Viaggio personalizzato, avvia un'inserimento più particolare delle varie tratte →
- Schermata tratte con i vari bottoni, all'ultima tratta → RIPETI DA CAPO
- In qualsiasi momento si può:
  - uscire dalla tratta corrente o viaggio corrente;
  - accedere alla Home;
  - accedere alla modalità HIS;
  - salvare lo stato corrente della tratta/viaggio per poterlo riprendere

2.2.1.2 Livello Computazionale (.gs/.html)

- Mappature:

  - viaggi;
  - tratte;
  - mezzo - tratta;
  - valori - valori (esempio mezzo:piedi→isseduta e seduta disp: vuoto)
- Servizi di chaching e salvataggi locali temporanei, per quando non c'è la connessione o la si perde

##### 2.2.2 VISUALIZZAZIONE E MODIFICA DATASET → ODYSSEY HIS >!HIS == history< [da rivalutare bene i nomi]
