import json
import re
from dataclasses import dataclass, asdict, field

from llm_client import call_llm
from privacy import mask, find_pii
from prompts import build_system_prompt, build_messages
from taxonomy import FALLBACK, valid_pair

MAX_RETRIES = 2
MIN_CONFIDENCE = 0.0  # raise (e.g. 0.4) to route low-confidence outputs to FALLBACK


@dataclass
class Ticket:
    titolo: str = ""
    descrizione: str = ""
    categoria: str = FALLBACK
    sottocategoria: str = FALLBACK
    confidenza: float = 0.0
    errori_validazione: int = 0
    fallback_forzato: bool = False
    pii_nell_output: list = field(default_factory=list)


def extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError("Nessun oggetto JSON trovato")
    return json.loads(match.group(0))


def validate(data: dict) -> dict:
    for key in ("titolo", "descrizione", "categoria", "sottocategoria", "confidenza"):
        if key not in data:
            raise ValueError(f"Campo mancante: {key}")
    if not valid_pair(data["categoria"], data["sottocategoria"]):
        raise ValueError(f"Coppia non ammessa: {data['categoria']} / {data['sottocategoria']}")
    conf = float(data["confidenza"])
    if not 0.0 <= conf <= 1.0:
        raise ValueError("confidenza fuori da [0, 1]")
    data["confidenza"] = conf
    if len(str(data["titolo"]).split()) > 15:
        raise ValueError("Titolo troppo lungo")
    return data


def process_email(email: str, version: str = "v1") -> Ticket:
    masked = mask(email)
    system = build_system_prompt(version)
    messages = build_messages(masked, version)
    errors = 0

    for _ in range(MAX_RETRIES + 1):
        raw = ""
        try:
            raw = call_llm(system, messages)
            data = validate(extract_json(raw))
            ticket = Ticket(**{k: data[k] for k in ("titolo", "descrizione", "categoria", "sottocategoria", "confidenza")})
            ticket.errori_validazione = errors
            if ticket.confidenza < MIN_CONFIDENCE:
                ticket.categoria = ticket.sottocategoria = FALLBACK
                ticket.fallback_forzato = True
            ticket.pii_nell_output = find_pii(ticket.titolo + " " + ticket.descrizione)
            return ticket
        except Exception as exc:  # invalid JSON, bad category, API hiccup...
            errors += 1
            print(f"[tentativo {errors}] errore: {type(exc).__name__}: {exc}")
            print(f"[tentativo {errors}] raw: {raw[:300]!r}")
            messages = messages + [
                {"role": "assistant", "content": raw or "(vuoto)"},
                {"role": "user", "content": f"Output non valido: {exc}. Rispondi di nuovo SOLO con il JSON corretto."},
            ]

    return Ticket(errori_validazione=errors, fallback_forzato=True)


def ticket_to_dict(t: Ticket) -> dict:
    return asdict(t)


