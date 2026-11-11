"""
compute_D.py — Transparent D operationalization for SRM
Politomorphism Research Project | Serban Gabriel Florin
License: CC BY 4.0 | github.com/profserbangabriel-del/politomorphism

D = alpha * PE + (1 - alpha) * ICI

PE  = Polysemy Entropy via LDA + Jensen-Shannon Divergence
ICI = Intra-contextual Incoherence via sentence embeddings
"""

import numpy as np
import json
import os
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.utils import resample
from scipy.spatial.distance import jensenshannon
from sentence_transformers import SentenceTransformer

_model = None

def get_model():
    global _model
    if _model is None:
        print("Loading sentence model (first run only)...")
        _model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    return _model


def compute_PE(texts: list, n_topics: int = 10) -> float:
    """
    Polysemy Entropy — topical breadth across domains.
    Returns value in [0, 1].
    """
    if len(texts) < 5:
        print(f"  WARNING: Only {len(texts)} texts — PE may be unreliable.")

    vec = TfidfVectorizer(
        max_features=5000,
        min_df=1,      # min_df=1 for small corpora
        max_df=0.95,
        ngram_range=(1, 2)
    )
    X = vec.fit_transform(texts)

    # Adjust n_topics if corpus is very small
    n_topics = min(n_topics, len(texts) - 1, 10)
    n_topics = max(n_topics, 2)

    lda = LatentDirichletAllocation(
        n_components=n_topics,
        random_state=42,
        max_iter=20,
        learning_method="batch"
    )
    td = lda.fit_transform(X) + 1e-10
    td /= td.sum(axis=1, keepdims=True)

    centroid = td.mean(axis=0)
    centroid /= centroid.sum()

    pe = float(np.mean([jensenshannon(d, centroid, base=2) for d in td]))
    return round(pe, 4)


def compute_ICI(titles: list) -> float:
    """
    Intra-contextual Incoherence — framing divergence across outlets.
    Returns value in [0, 1].
    """
    if len(titles) < 2:
        return 0.0

    model = get_model()
    emb = model.encode(
        titles,
        batch_size=64,
        show_progress_bar=False,
        normalize_embeddings=True
    )
    # Mean pairwise cosine similarity (dot product for L2-normalized vectors)
    cos_sim = (emb @ emb.T).mean()
    ici = float(1.0 - cos_sim)
    return round(ici, 4)


def compute_D(
    texts: list,
    titles: list,
    alpha: float = 0.5,
    bootstrap_n: int = 500,
    n_topics: int = 10
) -> dict:
    """
    Compute D with bootstrap confidence interval.

    Parameters
    ----------
    texts    : list of str — article bodies (or first paragraphs)
    titles   : list of str — article titles (used for ICI)
    alpha    : float — weight of PE (1-alpha = weight of ICI). Default 0.5
    bootstrap_n : int — number of bootstrap samples for CI
    n_topics : int — number of LDA topics. Default 10

    Returns
    -------
    dict with keys:
        PE, ICI, D, alpha,
        D_std, D_ci_low, D_ci_high,
        n_docs, bootstrap_n
    """
    print(f"  Computing PE on {len(texts)} texts...")
    PE = compute_PE(texts, n_topics=n_topics)

    print(f"  Computing ICI on {len(titles)} titles...")
    ICI = compute_ICI(titles)

    D = round(alpha * PE + (1 - alpha) * ICI, 4)
    print(f"  PE={PE}  ICI={ICI}  D={D}")

    # Bootstrap confidence interval
    print(f"  Bootstrap CI ({bootstrap_n} samples)...")
    boot = []
    for i in range(bootstrap_n):
        idx = resample(range(len(texts)), random_state=i)
        t_b = [texts[j] for j in idx]
        ti_b = [titles[j] for j in idx]
        pe_b = compute_PE(t_b, n_topics=n_topics)
        ici_b = compute_ICI(ti_b)
        boot.append(alpha * pe_b + (1 - alpha) * ici_b)

    D_std = float(np.std(boot))
    D_ci_low  = round(max(0.0, D - 1.96 * D_std), 4)
    D_ci_high = round(min(1.0, D + 1.96 * D_std), 4)

    return {
        "PE":         PE,
        "ICI":        ICI,
        "D":          D,
        "alpha":      alpha,
        "D_std":      round(D_std, 4),
        "D_ci_low":   D_ci_low,
        "D_ci_high":  D_ci_high,
        "n_docs":     len(texts),
        "bootstrap_n": bootstrap_n
    }


def propagate_to_srm(V, A, N, lam, result: dict) -> dict:
    """
    Propagate D uncertainty to SRM confidence interval.

    Parameters
    ----------
    V, A, N : float — SRM variables
    lam     : float — lambda (empirical or default)
    result  : dict — output of compute_D()

    Returns
    -------
    dict with SRM_point, SRM_low, SRM_high, SRM_interval_pct
    """
    D      = result["D"]
    D_low  = result["D_ci_low"]
    D_high = result["D_ci_high"]

    SRM_point = round(V * A * np.exp(-lam * D)      * N, 6)
    SRM_low   = round(V * A * np.exp(-lam * D_high) * N, 6)
    SRM_high  = round(V * A * np.exp(-lam * D_low)  * N, 6)

    if SRM_point > 0:
        interval_pct = round(((SRM_high - SRM_low) / SRM_point) * 100, 1)
    else:
        interval_pct = None

    return {
        "SRM_point":       SRM_point,
        "SRM_low":         SRM_low,
        "SRM_high":        SRM_high,
        "SRM_interval_pct": interval_pct,
        "lambda_used":     lam
    }


def load_texts_from_csv(csv_path: str,
                         text_col: str = "title",
                         body_col: str = None) -> tuple:
    """
    Load titles and texts from a Media Cloud CSV export.

    Returns (texts, titles) where texts = bodies if body_col provided,
    else texts = titles (acceptable fallback for PE).
    """
    import csv
    titles = []
    texts  = []
    with open(csv_path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t = row.get(text_col, "").strip()
            if t:
                titles.append(t)
                if body_col and row.get(body_col, "").strip():
                    texts.append(row[body_col].strip())
                else:
                    texts.append(t)  # fallback: use title as text
    return texts, titles


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Compute D (Semantic Drift) for SRM pipeline"
    )
    parser.add_argument("--csv",      required=True,  help="Path to Media Cloud CSV")
    parser.add_argument("--symbol",   required=True,  help="Symbol name (for output)")
    parser.add_argument("--V",        type=float,     help="Viral Velocity (optional, for SRM propagation)")
    parser.add_argument("--A",        type=float,     help="Affective Weight (optional)")
    parser.add_argument("--N",        type=float,     help="Network Coverage (optional)")
    parser.add_argument("--lam",      type=float, default=7.0, help="Lambda (default=7)")
    parser.add_argument("--alpha",    type=float, default=0.5, help="PE weight (default=0.5)")
    parser.add_argument("--bootstrap",type=int,   default=500, help="Bootstrap samples (default=500)")
    parser.add_argument("--out",      default=None,   help="Output JSON path (optional)")
    args = parser.parse_args()

    print(f"\n=== compute_D.py — {args.symbol} ===")
    texts, titles = load_texts_from_csv(args.csv)
    print(f"Loaded {len(texts)} articles from {args.csv}")

    result = compute_D(
        texts=texts,
        titles=titles,
        alpha=args.alpha,
        bootstrap_n=args.bootstrap
    )

    print(f"\n--- Results for {args.symbol} ---")
    print(f"  PE  = {result['PE']}")
    print(f"  ICI = {result['ICI']}")
    print(f"  D   = {result['D']}  (α={result['alpha']})")
    print(f"  95% CI: [{result['D_ci_low']}, {result['D_ci_high']}]  ±{result['D_std']}")

    output = {"symbol": args.symbol, "D_result": result}

    if args.V and args.A and args.N:
        srm = propagate_to_srm(args.V, args.A, args.N, args.lam, result)
        output["SRM"] = srm
        print(f"\n  SRM({args.lam}) = {srm['SRM_point']}")
        print(f"  SRM interval: [{srm['SRM_low']}, {srm['SRM_high']}]  (±{srm['SRM_interval_pct']}%)")

    out_path = args.out or f"D_result_{args.symbol.replace(' ','_')}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to {out_path}")
