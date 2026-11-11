"""
PREPARAZIONE (una volta sola)
  
   pip install -r requirements.txt
   python -m spacy download it_core_news_sm
   
   PROVA VELOCE SU UNA SOLA EMAIL ("single")
   Serve per controllare che tutto funzioni prima di lanciare le prove lunghe.
   Il risultato è il ticket in formato JSON: titolo, descrizione, categoria,
   sottocategoria, confidenza.
 
   python run.py single "Ho dimenticato la password"
       # versione v1 (è quella di default)
   python run.py single "Ho dimenticato la password" --version v2
       # stessa email con la versione v2 (regole e esempi nel prompt)
   python run.py single "Il paziente RSSMRA80A01H501U non riesce a cambiare medico, errore E542"
       # email con codice fiscale: nel ticket non deve comparire
   python run.py single "non funziona niente"
       # email troppo generica: ci aspettiamo "Da verificare"
 
. COMANDI COMPLETI (nell'ordine consigliato)
   python test_classification.py v1           # 20 casi di test
   python test_classification.py v2
   python test_privacy.py v1                  # controllo privacy (mascheramento + output)
   python run.py eval --version v1            # valutazione completa (67 email)
   python run.py eval --version v2
   python run.py compare                      # tabella v1 vs v2
 
. DOVE VANNO I RISULTATI (cartella data/)
   results_v1.csv, results_v2.csv            # una riga per email con la predizione
   confusion_v1.csv, confusion_v2.csv        # matrice di confusione (solo con "eval")
   errors_v1.csv, errors_v2.csv              # email classificate male (solo con "eval")
   quality_sample.csv                        # 20 email da valutare a mano (voti 1-5)
   compare_results.csv                       # confronto v1 vs v2
   test_classificazione_v1.csv, _v2.csv      # risultati dei 20 casi di test
 
NOTE
   - Lancia sempre i comandi dalla cartella del progetto (serve data/tassonomia.json).
   - Se non imposti LLM_MODEL, il programma usa qwen2.5:3b. Sul PC principale
     imposta sempre LLM_MODEL=gemma4-coder:latest, altrimenti i risultati
     sono di qwen anche se pensi di usare gemma.
   - Per confrontare v1 e v2 usa lo STESSO modello e scrivilo nel report.
   - Se cambi modello, rilancia entrambe le versioni e salva i risultati a parte.
   - "compare" riscrive results_v1/v2.csv ma NON confusion ed errors: per avere file
     coerenti tra loro usa "eval" per v1 e v2 e non mescolarli con "compare".
   - Se una email viene classificata "Da verificare" con confidenza 0.0, di solito
     l'AI ha sbagliato il formato della risposta per 3 volte di fila.
"""
import argparse, json
import pandas as pd
from pipeline import process_email, ticket_to_dict
from evaluate import run_corpus, metrics, confusion, top_confusions, errors, sample_for_manual_scoring

CORPUS = "data/corpus_email.csv"


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("single"); s.add_argument("email"); s.add_argument("--version", default="v1")
    e = sub.add_parser("eval"); e.add_argument("--version", default="v1")
    sub.add_parser("compare")
    a = p.parse_args()

    if a.cmd == "single":
        print(json.dumps(ticket_to_dict(process_email(a.email, a.version)), ensure_ascii=False, indent=2))
    elif a.cmd == "eval":
        out = run_corpus(CORPUS, a.version, f"data/results_{a.version}.csv")
        print(json.dumps(metrics(out), indent=2))
        cm = confusion(out); cm.to_csv(f"data/confusion_{a.version}.csv")
        print("Top confusions:", top_confusions(cm))
        errors(out).to_csv(f"data/errors_{a.version}.csv", index=False)
        sample_for_manual_scoring(out)# ...
    elif a.cmd == "compare":
        rows = {v: metrics(run_corpus(CORPUS, v, f"data/results_{v}.csv")) for v in ("v1", "v2")}
        df = pd.DataFrame(rows).round(3)
        df.to_csv("data/compare_results.csv", index=False)
        print("Risultati salvati in: data/compare_results.csv")
        print(df)
    


if __name__ == "__main__":
    main()
