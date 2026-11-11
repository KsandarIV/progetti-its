import pandas as pd
import re
import spacy

PATTERNS = [
    # --- DATI DI CONTATTO E IDENTIFICATIVI ---
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    ("TELEFONO", re.compile(r"(?<!\w)(?:(?:\+|00)39[\s.-]?)?(?:3\d{2}[\s.-]?\d{6,7}|0\d{1,3}[\s.-]?\d{5,8})(?!\w)")),
    ("DATA_NASCITA", re.compile(r"\b(?:0?[1-9]|[12]\d|3[01])[\/\.-](?:0?[1-9]|1[0-2])[\/\.-](?:19|20)\d{2}\b")),

    # --- DOCUMENTI D'IDENTITÀ E CODICI FISCALI (ITALIA) ---
    ("CODICE_FISCALE", re.compile(r"\b[A-Z]{6}\d{2}[A-EHLMPR-T]\d{2}[A-Z]\d{3}[A-Z]\b", re.I)),
    ("PARTITA_IVA", re.compile(r"\b(?:IT)?\d{11}\b", re.I)),
    ("CARTA_IDENTITA", re.compile(r"\b(?:[A-Z]{2}\d{7}|[A-Z]{2}\d{5}[A-Z]{2})\b", re.I)),
    ("PASSAPORTO", re.compile(r"\b[A-Z]{2}\d{7}\b", re.I)),
    ("PATENTE", re.compile(r"\b(?:U1[A-Z0-9]{7}|[A-Z]{2}\d{7}[A-Z])\b", re.I)),
    ("TESSERA_SANITARIA", re.compile(r"\b80380\d{15}\b")),

    # --- DATI FINANZIARI E BANCARI ---
    ("IBAN", re.compile(r"\bIT\d{2}[A-Z]\d{10}[A-Z0-9]{12}\b", re.I)),
    ("IBAN", re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b", re.I)),
    ("CARTA_CREDITO", re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|(?:5[1-5][0-9]{2}|222[1-9]|22[3-9][0-9]|2[3-6][0-9]{2}|27[01][0-9]|2720)[0-9]{12}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12})[ -]?\b")),

    # --- DATI DIGITALI ED HARDWARE ---
    ("INDIRIZZO_IPV4", re.compile(r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b")),
    ("INDIRIZZO_IPV6", re.compile(r"\b(?:[a-fA-F0-9]{1,4}:){7}[a-fA-F0-9]{1,4}\b")),
    ("MAC_ADDRESS", re.compile(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b")),
    ("URL", re.compile(r"https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/\/=]*)")),

    # --- ALTRI IDENTIFICATIVI ---
    ("TARGA_VEICOLO", re.compile(r"\b[A-Z]{2}\d{3}[A-Z]{2}\b", re.I)),
    ("INDIRIZZO", re.compile(r"\b(?:via|piazza|corso|viale|vicolo|largo|piazzale|strada|vico|vicoletto|salita|discesa|rampa|contrada|frazione|località|sestiere|calle|campo|fondamenta|riva)\s+[A-Za-zÀ-ù0-9'\s\.\-]+?\s+(?:\d+|snc|S\.N\.C\.)\b", re.I)),
    ("CODICE_POSTALE", re.compile(r"\b\d{5}\b")),
]

# Carichiamo il modello spaCy una volta sola all'esterno per efficienza
nlp = spacy.load("it_core_news_sm")

def mask(text: str) -> str:
    if not isinstance(text, str):
        return text

    replacements = []

    # 1. Trova i match delle espressioni regolari
    for label, pattern in PATTERNS:
        for match in pattern.finditer(text):
            replacements.append((match.start(), match.end(), f"<{label}>"))

    # 2. Trova le entità persona (PER) tramite spaCy
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "PER":
            replacements.append((ent.start_char, ent.end_char, "<NOME_COGNOME>"))

    # 3. Ordina tutte le sostituzioni per posizione d'inizio
    replacements = sorted(replacements, key=lambda x: x[0])

    # 4. Risolve le sovrapposizioni mantenendo la prima sostituzione ed escludendo i conflitti successivi
    clean_replacements = []
    last_end = 0
    for start, end, label in replacements:
        if start >= last_end:
            clean_replacements.append((start, end, label))
            last_end = end

    # 5. Applica le sostituzioni partendo dalla fine della stringa verso l'inizio per non alterare gli indici precedenti
    clean_replacements = sorted(clean_replacements, key=lambda x: x[0], reverse=True)
    masked_text = text
    for start, end, label in clean_replacements:
        masked_text = masked_text[:start] + label + masked_text[end:]

    return masked_text

def find_pii(text: str) -> list[str]:
    return [label for label, pattern in PATTERNS if pattern.search(text)]