import json

FALLBACK = "Da verificare"

with open("data/tassonomia.json", encoding="utf-8") as f:
    _T = json.load(f)

TAXONOMY = {c: list(d["sottocategorie"]) for c, d in _T["categorie"].items()}
DEFINITIONS = {c: d["descrizione"] for c, d in _T["categorie"].items()}
TIE_BREAK_RULES = _T["regole_priorita"]


def valid_pair(categoria: str, sottocategoria: str) -> bool:
    if categoria == FALLBACK:
        return sottocategoria == FALLBACK
    return categoria in TAXONOMY and sottocategoria in TAXONOMY[categoria]
