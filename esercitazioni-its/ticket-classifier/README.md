# Ticket Classifier con LLM locale

Project work del modulo "Applicazioni dell'intelligenza artificiale" (Exprivia), ITS. **Lavoro di gruppo (6 persone).**

## Il problema
Un ente sanitario regionale riceve dagli utenti email di assistenza. Il sistema legge l'email e apre un ticket IT strutturato in JSON (titolo, descrizione, categoria, sottocategoria, confidenza). Se l'email non è classificabile, il ticket va in "Da verificare" invece di inventare una categoria.

## Come funziona
| File | Ruolo |
|---|---|
| `privacy.py` | Anonimizza l'email **prima** di passarla all'LLM: 18 pattern regex (codice fiscale, IBAN, telefono, indirizzo, targa...) e nomi di persona con spaCy |
| `taxonomy.py`, `data/tassonomia.json` | 8 categorie con sottocategorie, definizioni e regole per i casi ambigui |
| `prompts.py` | Prompt con schema JSON e regole contro il prompt injection; due versioni (la v2 aggiunge regole di priorità ed esempi) |
| `pipeline.py` | Mascheramento → LLM → validazione del JSON → fino a 2 nuovi tentativi → fallback; controlla che nell'output non ci siano dati personali |
| `evaluate.py`, `run.py` | Valutazione sul corpus di 67 email: accuratezza, matrice di confusione, analisi degli errori, confronto v1/v2 |
| `test_*.py` | Test di classificazione e di mascheramento |

Modello: LLM locale tramite Ollama, temperatura 0.

## Risultati (file in `data/`)
| | v1 | v2 |
|---|---|---|
| Accuratezza sulla categoria (67 email) | 80,6% | 77,6% |
| Email rinviate a "Da verificare" | 20,9% | 20,9% |
| Accuratezza sulle email non rinviate | 96,2% | 92,5% |
| Errori di formato dell'output | 90 | 45 |
| Dati personali negli output | 0 | 0 |

La v2 dimezza gli errori di formato ma non migliora l'accuratezza. Il punto forte è la privacy: nessun dato personale nei 134 output.

## Il mio contributo — Aleksandar Savov
- Ho aiutato a generare le email del corpus di prova (`data/corpus_email.csv`).
- Ho fatto revisioni del codice per trovare bug e ho aiutato a risolverli.

## Come avviarlo
```bash
pip install -r requirements.txt
python -m spacy download it_core_news_sm
python run.py single "Ho dimenticato la password"
```
Serve [Ollama](https://ollama.com) in locale con il modello indicato in `llm_client.py`.

Le email del corpus sono inventate: non contengono dati reali.
