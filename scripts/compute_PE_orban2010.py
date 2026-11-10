#!/usr/bin/env python3
"""
compute_PE_orban2010.py - Polysemy Entropy (PE) for the Orban-2010 Media Cloud titles,
following Section 3.1-3.2 of "Operationalizing Semantic Drift (D) in the Social
Resonance Model" (SSRN 6583879) as literally as the text allows.

NOT in the paper's text (choices made here and recorded in the output JSON):
  - corpus: the paper uses title + first paragraph; only titles exist in the data file.
  - spaCy filtering: "stopword removal and lemmatization" -> keep tokens that are not
    stop words, not punctuation/space, and alphabetic; use token.lemma_.lower().
  - language detection: the paper says to FLAG articles whose language differs; here
    they are flagged and counted, not removed.
  - PE definition: the paper's text says "mean Jensen-Shannon Divergence" while its code
    calls scipy's jensenshannon, which returns the DISTANCE (square root of the
    divergence). Both are computed and reported; the code-faithful one is
    PE_js_distance (as published code), the text-faithful one is PE_js_divergence.
  - LDA input: the paper fits LDA on the TF-IDF matrix (as published); all other LDA
    parameters are scikit-learn defaults of the recorded version.
No embeddings are used here, so ICI and D are NOT computed by this script.

Usage (from the repository root):
    python scripts/compute_PE_orban2010.py
Writes: disinformation_paper/orban2010_data/pe_orban2010_generated.json
"""
import hashlib, json, os, platform, subprocess, sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import scipy, sklearn
import spacy
from langdetect import DetectorFactory, detect
from scipy.spatial.distance import jensenshannon
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import TfidfVectorizer

DATA = "data/orban2010_content.csv"
OUT = "disinformation_paper/orban2010_data/pe_orban2010_generated.json"
SEED = 42
N_TOPICS, MAX_ITER = 10, 20
TFIDF = dict(max_features=5000, min_df=2, max_df=0.95)


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def git(*args):
    try:
        return subprocess.run(["git", *args], capture_output=True, text=True, check=False).stdout.strip()
    except OSError:
        return "unavailable"


def main():
    DetectorFactory.seed = SEED
    raw = open(DATA, "rb").read()
    df = pd.read_csv(DATA)
    # same filter as the ICI workflow (orban2010_D.yml): strings longer than 10 characters
    titles = [str(t).strip() for t in df["title"].tolist()
              if isinstance(t, str) and len(str(t).strip()) > 10]
    corpus_hash = sha256_bytes("\n".join(titles).encode("utf-8"))

    # language flags (flag only)
    langs = []
    for t in titles:
        try:
            langs.append(detect(t))
        except Exception:
            langs.append("unknown")
    lang_counts = pd.Series(langs).value_counts().to_dict()
    expected = "en"
    n_flagged = sum(1 for l in langs if l != expected)

    nlp = spacy.load("en_core_web_sm")
    docs = []
    for d in nlp.pipe(titles, batch_size=64):
        toks = [t.lemma_.lower() for t in d if t.is_alpha and not t.is_stop and not t.is_space]
        docs.append(" ".join(toks))
    n_empty = sum(1 for d in docs if not d)

    vec = TfidfVectorizer(**TFIDF)
    X = vec.fit_transform(docs)

    lda = LatentDirichletAllocation(n_components=N_TOPICS, random_state=SEED, max_iter=MAX_ITER)
    topic_dist = lda.fit_transform(X)
    topic_dist = topic_dist + 1e-10
    topic_dist = topic_dist / topic_dist.sum(axis=1, keepdims=True)
    centroid = topic_dist.mean(axis=0)
    centroid = centroid / centroid.sum()

    dist = np.array([jensenshannon(d, centroid, base=2) for d in topic_dist])   # as published code
    div = dist ** 2                                                              # per-document divergence
    result = {
        "PE_js_distance_published_code": float(dist.mean()),
        "PE_js_divergence_text_definition": float(div.mean()),
    }

    # fixed-seed repeat inside the script (determinism check on the same process inputs)
    lda2 = LatentDirichletAllocation(n_components=N_TOPICS, random_state=SEED, max_iter=MAX_ITER)
    td2 = lda2.fit_transform(X)
    td2 = td2 + 1e-10; td2 = td2 / td2.sum(axis=1, keepdims=True)
    c2 = td2.mean(axis=0); c2 = c2 / c2.sum()
    pe2 = float(np.mean([jensenshannon(d, c2, base=2) for d in td2]))

    out = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "script": "scripts/compute_PE_orban2010.py",
        "script_sha256": sha256_bytes(open(__file__, "rb").read()),
        "code_commit": git("rev-parse", "HEAD"),
        "working_tree_clean": git("status", "--porcelain") == "",
        "command": "python scripts/compute_PE_orban2010.py",
        "input_file": DATA,
        "input_file_sha256": sha256_bytes(raw),
        "effective_corpus": {"n_titles": len(titles), "sha256_of_titles_joined_by_newline": corpus_hash,
                             "empty_after_preprocessing": n_empty},
        "language_detection": {"expected": expected, "counts": lang_counts, "flagged_not_removed": n_flagged,
                               "langdetect_seed": SEED},
        "parameters": {"seed": SEED, "n_topics": N_TOPICS, "max_iter": MAX_ITER, "tfidf": TFIDF,
                       "lda_input": "TF-IDF matrix (as published)", "jensenshannon_base": 2,
                       "tfidf_vocabulary_size": int(X.shape[1])},
        "versions": {"python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__,
                     "scikit-learn": sklearn.__version__, "pandas": pd.__version__,
                     "spacy": spacy.__version__, "spacy_model": nlp.meta.get("name") + " " + nlp.meta.get("version", ""),
                     "langdetect": "see pip freeze", "platform": platform.platform()},
        "result": result,
        "determinism_check_same_process": {"PE_js_distance_second_fit": pe2,
                                           "identical": abs(pe2 - result["PE_js_distance_published_code"]) < 1e-12},
        "deviations_from_paper": [
            "titles only (paper: title + first paragraph)",
            "spaCy token filter (alpha, non-stop, non-space; lemma lowercased) is not specified in the paper",
            "language flagged, not removed (paper: flag)",
            "PE reported both as JS distance (published code) and JS divergence (published text)",
        ],
        "not_computed": "ICI and D (need sentence embeddings, unavailable in this environment)",
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(json.dumps({"PE_distance": result["PE_js_distance_published_code"],
                      "PE_divergence": result["PE_js_divergence_text_definition"],
                      "n_titles": len(titles)}, indent=2))


if __name__ == "__main__":
    main()
