"""
georgescu_temporal_ici.py — Politomorphism Research Project
=============================================================
Calculează ICI temporal pentru Călin Georgescu
Perioada: 1 septembrie 2024 — 30 noiembrie 2024
"""

import os
import sys
import json
import time
import random
import logging
from datetime import datetime, timedelta, date
from typing import List, Dict

import numpy as np
import pandas as pd

SYMBOL          = "Călin Georgescu"
QUERY           = '"Calin Georgescu"'
START_DATE      = "2024-09-01"
END_DATE        = "2024-11-30"
WINDOW_DAYS     = 14
STEP_DAYS       = 7
N_ARTICLES_MAX  = 300
BOOTSTRAP_N     = 200
RANDOM_SEED     = 42
MODEL_NAME      = "paraphrase-multilingual-MiniLM-L12-v2"
OUTPUT_DIR      = "results"

COLLECTION_IDS  = [34412234]

EXTERNAL_EVENTS = [
    {"date": "2024-10-15", "label": "Spike TikTok coordonat (EUvsDisinfo)", "type": "campaign_start"},
    {"date": "2024-11-01", "label": "Peak campanie dezinformare (ANCOM)",    "type": "campaign_peak"},
    {"date": "2024-11-15", "label": "Amplificare pre-electorală (CNA)",      "type": "campaign_peak"},
    {"date": "2024-11-24", "label": "Primul tur prezidențiale",              "type": "election"},
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger(__name__)


def fetch_articles_window(api_key, query, start_date_str, end_date_str, collection_ids, max_articles=300):
    try:
        import mediacloud.api as mc_api
        search = mc_api.SearchApi(api_key)
    except ImportError:
        log.error("mediacloud nu e instalat")
        sys.exit(1)

    # CRITIC: API-ul vrea date, nu datetime
    start_dt = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_dt   = datetime.strptime(end_date_str,   "%Y-%m-%d").date()

    all_stories = []
    pagination_token = None

    try:
        while len(all_stories) < max_articles:
            if pagination_token:
                page, pagination_token = search.story_list(
                    query,
                    start_date=start_dt,
                    end_date=end_dt,
                    collection_ids=collection_ids,
                    pagination_token=pagination_token
                )
            else:
                page, pagination_token = search.story_list(
                    query,
                    start_date=start_dt,
                    end_date=end_dt,
                    collection_ids=collection_ids
                )

            if not page:
                break

            all_stories.extend(page)
            log.info(f"  +{len(page)} articole (total: {len(all_stories)})")

            if not pagination_token:
                break

            time.sleep(0.3)

    except Exception as e:
        log.warning(f"  Media Cloud error: {e}")

    log.info(f"  Fetched: {len(all_stories)} articole ({start_date_str} → {end_date_str})")
    return all_stories[:max_articles]


def extract_texts(stories):
    texts, sources = [], []
    for s in stories:
        title = (s.get("title", "") or "").strip()
        if len(title) > 10:
            texts.append(title)
            sources.append(s.get("media_name", "unknown") or "unknown")
    return texts, sources


def compute_ici_from_embeddings(embeddings):
    from sklearn.metrics.pairwise import cosine_similarity
    if len(embeddings) < 2:
        return float('nan')
    sim_matrix = cosine_similarity(embeddings)
    n = len(sim_matrix)
    upper = [sim_matrix[i][j] for i in range(n) for j in range(i+1, n)]
    if not upper:
        return float('nan')
    return 1.0 - float(np.mean(upper))


def compute_ici_bootstrap(texts, model, bootstrap_n=200, sample_size=100, seed=42):
    random.seed(seed)
    np.random.seed(seed)
    n = len(texts)
    if n < 5:
        return {"ici_mean": float('nan'), "ici_ci_low": float('nan'),
                "ici_ci_high": float('nan'), "n_texts": n,
                "n_bootstrap": 0, "status": "insufficient_data"}
    actual_sample = min(sample_size, n)
    log.info(f"  Encoding {n} texte...")
    all_embeddings = model.encode(texts, show_progress_bar=False, batch_size=32)
    ici_samples = []
    for b in range(bootstrap_n):
        indices = np.random.choice(n, size=actual_sample, replace=True)
        ici_b = compute_ici_from_embeddings(all_embeddings[indices])
        if not np.isnan(ici_b):
            ici_samples.append(ici_b)
    if len(ici_samples) < 5:
        return {"ici_mean": float('nan'), "ici_ci_low": float('nan'),
                "ici_ci_high": float('nan'), "n_texts": n,
                "n_bootstrap": len(ici_samples), "status": "bootstrap_failed"}
    ici_arr = np.array(ici_samples)
    return {
        "ici_mean":    float(np.mean(ici_arr)),
        "ici_ci_low":  float(np.percentile(ici_arr, 2.5)),
        "ici_ci_high": float(np.percentile(ici_arr, 97.5)),
        "ici_std":     float(np.std(ici_arr)),
        "n_texts":     n,
        "n_bootstrap": len(ici_samples),
        "status":      "ok"
    }


def generate_windows(start, end, window_days=14, step_days=7):
    windows = []
    current = datetime.strptime(start, "%Y-%m-%d")
    end_dt  = datetime.strptime(end,   "%Y-%m-%d")
    while current <= end_dt:
        window_end = min(current + timedelta(days=window_days - 1), end_dt)
        windows.append({
            "start_date": current.strftime("%Y-%m-%d"),
            "end_date":   window_end.strftime("%Y-%m-%d"),
            "midpoint":   (current + timedelta(days=window_days // 2)).strftime("%Y-%m-%d"),
            "label":      f"{current.strftime('%d %b')}–{window_end.strftime('%d %b %Y')}"
        })
        current += timedelta(days=step_days)
    return windows


def run_pipeline():
    api_key = os.environ.get("MEDIACLOUD_API_KEY", "")
    if not api_key:
        log.error("MEDIACLOUD_API_KEY nu e setat.")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    log.info(f"Loading embedding model: {MODEL_NAME}")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(MODEL_NAME)
    log.info("Model loaded.")

    windows = generate_windows(START_DATE, END_DATE, WINDOW_DAYS, STEP_DAYS)
    log.info(f"Generated {len(windows)} ferestre temporale")

    results = []
    for i, window in enumerate(windows):
        log.info(f"\n[{i+1}/{len(windows)}] Fereastră: {window['label']}")
        stories = fetch_articles_window(
            api_key, QUERY,
            window["start_date"], window["end_date"],
            COLLECTION_IDS, N_ARTICLES_MAX
        )
        texts, sources = extract_texts(stories)
        log.info(f"  Texte valide: {len(texts)}")

        if len(texts) >= 5:
            ici_result = compute_ici_bootstrap(
                texts, model, BOOTSTRAP_N, min(100, len(texts)), RANDOM_SEED + i
            )
        else:
            ici_result = {"ici_mean": float('nan'), "ici_ci_low": float('nan'),
                          "ici_ci_high": float('nan'), "n_texts": len(texts),
                          "n_bootstrap": 0, "status": "skipped"}

        results.append({**window, **ici_result,
                        "n_articles_fetched": len(stories),
                        "n_sources_unique": len(set(sources)),
                        "sources_sample": list(set(sources))[:10]})

        if ici_result["status"] == "ok":
            log.info(f"  ICI = {ici_result['ici_mean']:.4f} "
                     f"[{ici_result['ici_ci_low']:.4f}, {ici_result['ici_ci_high']:.4f}]")
        time.sleep(0.5)

    valid = [r for r in results if r.get("status") == "ok"]

    summary = {
        "symbol": SYMBOL, "query": QUERY,
        "period": f"{START_DATE} → {END_DATE}",
        "window_days": WINDOW_DAYS, "step_days": STEP_DAYS,
        "bootstrap_n": BOOTSTRAP_N,
        "n_windows_total": len(results), "n_windows_valid": len(valid),
        "model": MODEL_NAME,
        "run_timestamp": datetime.now().isoformat(),
        "benchmark_ici_georgescu_aggregate": 0.634,
        "ici_temporal_mean": float(np.mean([r["ici_mean"] for r in valid])) if valid else None,
        "ici_temporal_max":  float(np.max([r["ici_mean"] for r in valid])) if valid else None,
        "ici_temporal_min":  float(np.min([r["ici_mean"] for r in valid])) if valid else None,
        "external_events": EXTERNAL_EVENTS,
        "windows": results
    }

    if valid:
        peak_window = max(valid, key=lambda x: x["ici_mean"])
        campaign_start = datetime(2024, 10, 15)
        peak_midpoint  = datetime.strptime(peak_window["midpoint"], "%Y-%m-%d")
        delta_days = (campaign_start - peak_midpoint).days
        summary["peak_ici_window"] = {
            "label":       peak_window["label"],
            "midpoint":    peak_window["midpoint"],
            "ici_mean":    peak_window["ici_mean"],
            "ici_ci_low":  peak_window["ici_ci_low"],
            "ici_ci_high": peak_window["ici_ci_high"],
        }
        summary["peak_ici_days_before_campaign"]  = delta_days
        summary["peak_ici_weeks_before_campaign"] = round(delta_days / 7, 1)
        log.info(f"\n{'='*60}")
        log.info(f"Peak ICI: {peak_window['ici_mean']:.4f} — {peak_window['label']}")
        log.info(f"Precede campania cu: {delta_days} zile ({round(delta_days/7,1)} săpt.)")
        log.info(f"{'='*60}")

    with open(os.path.join(OUTPUT_DIR, "georgescu_ici_temporal.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)

    df = pd.DataFrame([{
        "window_label":  r["label"],
        "start_date":    r["start_date"],
        "end_date":      r["end_date"],
        "midpoint":      r["midpoint"],
        "ici_mean":      r.get("ici_mean", ""),
        "ici_ci_low":    r.get("ici_ci_low", ""),
        "ici_ci_high":   r.get("ici_ci_high", ""),
        "n_articles":    r.get("n_articles_fetched", ""),
        "n_texts_valid": r.get("n_texts", ""),
        "status":        r.get("status", "")
    } for r in results])
    df.to_csv(os.path.join(OUTPUT_DIR, "georgescu_ici_temporal.csv"), index=False)

    log.info("Pipeline complet. Rezultate în: results/")
    return summary


if __name__ == "__main__":
    log.info("="*60)
    log.info("GEORGESCU TEMPORAL ICI PIPELINE")
    log.info("Politomorphism Research Project — Serban Gabriel Florin")
    log.info("="*60)
    run_pipeline()
