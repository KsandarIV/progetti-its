import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix
from pipeline import process_email, ticket_to_dict
from taxonomy import TAXONOMY, FALLBACK


def run_corpus(corpus_path: str, version: str, out_path: str) -> pd.DataFrame:
    """Corpus CSV columns: id, email, categoria, sottocategoria, difficile"""
    df = pd.read_csv(corpus_path)
    df = df[~df["id"].isin(["E058", "E066"])].reset_index(drop=True)
    preds = [ticket_to_dict(process_email(e, version)) for e in df["email"]]
    pred_df = pd.DataFrame(preds).add_prefix("pred_")
    out = pd.concat([df, pred_df], axis=1)
    out.to_csv(out_path, index=False)
    return out


def metrics(out: pd.DataFrame) -> dict:
    return {
        "acc_categoria": accuracy_score(out["categoria"], out["pred_categoria"]),
        "acc_sottocategoria": accuracy_score(out["sottocategoria"], out["pred_sottocategoria"]),
        "tasso_fallback": (out["pred_categoria"] == FALLBACK).mean(),
        "tot_errori_validazione": int(out["pred_errori_validazione"].sum()),
        "email_con_pii_nell_output": int((out["pred_pii_nell_output"].astype(str) != "[]").sum()),
    }


def confusion(out: pd.DataFrame) -> pd.DataFrame:
    labels = list(TAXONOMY) + [FALLBACK]
    cm = confusion_matrix(out["categoria"], out["pred_categoria"], labels=labels)
    return pd.DataFrame(cm, index=labels, columns=labels)


def top_confusions(cm: pd.DataFrame, n: int = 5):
    pairs = [(r, c, int(cm.loc[r, c])) for r in cm.index for c in cm.columns if r != c and cm.loc[r, c] > 0]
    return sorted(pairs, key=lambda x: -x[2])[:n]


def errors(out: pd.DataFrame) -> pd.DataFrame:
    """Rows to comment in the error analysis."""
    return out[out["categoria"] != out["pred_categoria"]][
        ["id", "email", "categoria", "pred_categoria", "sottocategoria", "pred_sottocategoria", "pred_confidenza"]
    ]


def sample_for_manual_scoring(out: pd.DataFrame, n: int = 20, path: str = "data/quality_sample.csv"):
    """Fill the empty columns by hand (1-5)."""
    s = out.sample(n=min(n, len(out)), random_state=42)[["id", "email", "pred_titolo", "pred_descrizione"]].copy()
    for col in ("chiarezza", "fedelta", "assenza_dati_personali"):
        s[col] = ""
    s.to_csv(path, index=False)
