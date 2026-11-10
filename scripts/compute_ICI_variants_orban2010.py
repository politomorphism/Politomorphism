#!/usr/bin/env python3
"""
compute_ICI_variants_orban2010.py - ICI variants and labelled D table for the Orban-2010 titles.
Run in GitHub Actions (sentence embeddings need the model download).

ICI variants (all on the same 270 title embeddings, model paraphrase-multilingual-MiniLM-L12-v2):
  ICI_upper_no_diag   : 1 - mean of upper-triangle cosine similarities (i<j)   [committed repo code]
  ICI_full_with_diag  : 1 - mean of the full n x n cosine matrix incl. diagonal [paper text]
  ICI_bootstrap_mean  : mean over 200 subsamples of size 100 drawn with replacement, upper
                        triangle (seed 42)  [workflow estimator; reported separately]
D = alpha*PE + (1-alpha)*ICI with alpha = 0.5 only (0.351/0.649 has no identified source).
PE values are read from the PE result file (never recomputed here).
Writes disinformation_paper/orban2010_data/ici_variants_and_D_table.json
"""
import hashlib, json, os, platform, subprocess, sys
from datetime import datetime, timezone
import numpy as np, pandas as pd, sklearn
from sklearn.metrics.pairwise import cosine_similarity

DATA = "data/orban2010_content.csv"
PE_FILE = "disinformation_paper/orban2010_data/pe_orban2010_generated.json"
OUT = "disinformation_paper/orban2010_data/ici_variants_and_D_table.json"
MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
SEED, B, SZ, ALPHA = 42, 200, 100, 0.5

def sha(b): return hashlib.sha256(b).hexdigest()
def git(*a):
    try: return subprocess.run(["git", *a], capture_output=True, text=True).stdout.strip()
    except OSError: return "unavailable"

df = pd.read_csv(DATA)
titles = [str(t).strip() for t in df["title"].tolist() if isinstance(t, str) and len(str(t).strip()) > 10]
n = len(titles)
corpus_hash = sha("\n".join(titles).encode("utf-8"))

from sentence_transformers import SentenceTransformer
import sentence_transformers, torch
emb = SentenceTransformer(MODEL).encode(titles, show_progress_bar=False, batch_size=32)
S = cosine_similarity(emb)
iu = np.triu_indices(n, k=1)
ici_upper = 1.0 - float(S[iu].mean())
ici_full = 1.0 - float(S.mean())

rng = np.random.RandomState(SEED)
samples = []
for _ in range(B):
    idx = rng.choice(n, SZ, replace=True)
    sm = cosine_similarity(emb[idx])
    k = len(sm)
    samples.append(1.0 - float(sm[np.triu_indices(k, k=1)].mean()))
arr = np.array(samples)
ici_boot = {"mean": float(arr.mean()), "ci_low": float(np.percentile(arr, 2.5)),
            "ci_high": float(np.percentile(arr, 97.5))}

pe = json.load(open(PE_FILE, encoding="utf-8"))
if pe["effective_corpus"]["sha256_of_titles_joined_by_newline"] != corpus_hash:
    raise SystemExit("corpus hash mismatch between PE file and this run")
pes = {"PE_js_distance (published code)": pe["result"]["PE_js_distance_published_code"],
       "PE_js_divergence (paper text)": pe["result"]["PE_js_divergence_text_definition"]}
icis = {"ICI_upper_no_diag (repo code)": ici_upper,
        "ICI_full_with_diag (paper text)": ici_full,
        "ICI_bootstrap_mean (workflow estimator)": ici_boot["mean"]}
table = [{"PE_variant": pk, "PE": pv, "ICI_variant": ik, "ICI": iv, "alpha": ALPHA,
          "D": ALPHA * pv + (1 - ALPHA) * iv}
         for pk, pv in pes.items() for ik, iv in icis.items()]

out = {"generated_utc": datetime.now(timezone.utc).isoformat(),
       "script": "scripts/compute_ICI_variants_orban2010.py",
       "script_sha256": sha(open(__file__, "rb").read()),
       "code_commit": git("rev-parse", "HEAD"), "input_file_sha256": sha(open(DATA, "rb").read()),
       "corpus_sha256": corpus_hash, "n_titles": n, "embedding_model": MODEL,
       "bootstrap": {"n": B, "sample_size": SZ, "replace": True, "seed": SEED, "rng": "np.random.RandomState"},
       "versions": {"python": sys.version.split()[0], "numpy": np.__version__, "sklearn": sklearn.__version__,
                    "sentence_transformers": sentence_transformers.__version__, "torch": torch.__version__,
                    "platform": platform.platform()},
       "ICI": {"upper_no_diag": ici_upper, "full_with_diag": ici_full, "bootstrap": ici_boot},
       "D_table_alpha_0.5": table,
       "notes": ["titles only (paper: title + first paragraph)",
                 "bootstrap uses a local RandomState, so it is NOT bit-identical to the earlier 0.7102 run (global np.random state); compare as estimator, not as replication",
                 "alpha=0.351/0.649 not computed: no source identified",
                 "no SRM: lambda, V, A, N lack verifiable provenance"]}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w", encoding="utf-8"), indent=2)
print(json.dumps({"ICI": out["ICI"], "D": [(t["PE_variant"][:14], t["ICI_variant"][:14], round(t["D"], 4)) for t in table]}, indent=1))
