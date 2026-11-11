# Bot investigatore (LLM + RAG)

Progetto di gruppo dell'ITS (gruppo di 4): un assistente che aiuta a condurre un'indagine sui documenti di un caso, con LLM e RAG in locale.

Il codice è nella repository del gruppo: **[MatCur997/Lazarus_Protocol](https://github.com/MatCur997/Lazarus_Protocol)**

## Il mio contributo — Aleksandar Savov
Ho proposto nuove funzionalità al gruppo. Due sono state tenute nella versione finale, sviluppate con un'impostazione diversa da quella che avevo proposto:
- l'estrazione di entità (persone, luoghi, eventi) dai documenti;
- la bacheca investigativa, che collega gli elementi emersi dalle domande al chatbot.

Tecnologie del progetto: Python, Ollama (gemma4, bge-m3), RAG ibrido (BM25 + embedding, fusione RRF, HyDE).
