"""
compute_V_A_N.py — Compute V, A, N components for SRM
Politomorphism Research Project | Serban Gabriel Florin
License: CC BY 4.0 | github.com/profserbangabriel-del/politomorphism

V (Viral Velocity)    : log-normalized escalation ratio peak/avg from Google Trends
A (Affective Weight)  : mean absolute VADER compound sentiment on article titles
N (Network Coverage)  : proportion of days with at least one article in window

Usage:
    python scripts/compute_V_A_N.py \
        --csv Trump-DATA.csv \
        --symbol Trump \
        --lam 7.01 \
        --start 2015-11-01 \
        --end 2016-11-30

Output:
    V_A_N_Trump.json
"""

import argparse
import csv
import json
import math
import os
from datetime import datetime, timedelta
from collections import defaultdict


# ── A: VADER Sentiment ────────────────────────────────────────────────────────

def compute_A(titles: list) -> float:
    """
    Affective Weight — mean absolute VADER compound sentiment on titles.
    Returns value in [0, 1].
    Installs vaderSentiment if not present.
    """
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    except ImportError:
        print("  Installing vaderSentiment...", flush=True)
        os.system("pip install vaderSentiment --quiet")
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

    analyzer = SentimentIntensityAnalyzer()
    scores = []
    for title in titles:
        if title and title.strip():
            score = analyzer.polarity_scores(title)["compound"]
            scores.append(abs(score))

    if not scores:
        return 0.0

    A = round(sum(scores) / len(scores), 4)
    print(f"  A = {A} (mean |VADER compound| on {len(scores)} titles)", flush=True)
    return A


# ── N: Network Coverage ───────────────────────────────────────────────────────

def compute_N(dates: list, start_date: datetime, end_date: datetime) -> float:
    """
    Network Coverage — proportion of days in window with at least one article.
    Returns value in [0, 1].
    """
    total_days = (end_date - start_date).days + 1
    if total_days <= 0:
        return 0.0

    days_with_articles = set()
    for d in dates:
        if d:
            try:
                # Handle various date formats
                for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                    try:
                        parsed = datetime.strptime(str(d)[:10], "%Y-%m-%d")
                        days_with_articles.add(parsed.date())
                        break
                    except ValueError:
                        continue
            except Exception:
                continue

    N = round(len(days_with_articles) / total_days, 4)
    print(f"  N = {N} ({len(days_with_articles)} active days / {total_days} total days)", flush=True)
    return N


# ── V: Viral Velocity ─────────────────────────────────────────────────────────

def compute_V_from_lambda(lam: float, T: float) -> float:
    """
    Viral Velocity derived analytically from lambda.

    Lambda is solved from: avg/peak = (1 - e^(-lT)) / (lT)
    This ratio gives us the shape of the Trends curve.

    V = log(1 + peak/avg) / log(2)  normalized to [0, 1]

    For lambda calibration: higher lambda = sharper peak = higher V.
    Uses the inverse: peak/avg = lT / (1 - e^(-lT))
    """
    if lam <= 0 or T <= 0:
        return 0.5

    lT = lam * T
    try:
        # avg/peak ratio from lambda formula
        avg_over_peak = (1 - math.exp(-lT)) / lT
        # peak/avg = inverse
        peak_over_avg = 1.0 / avg_over_peak
    except (ZeroDivisionError, OverflowError):
        peak_over_avg = 1.0

    # Log-normalize to [0, 1]: V = log(peak/avg) / log(max_possible)
    # max_possible peak/avg empirically ~20 (extreme flash viral)
    max_ratio = 20.0
    V = round(min(1.0, math.log(max(1.0, peak_over_avg)) / math.log(max_ratio)), 4)
    print(f"  V = {V} (from lambda={lam}, T={T:.2f}yr, peak/avg={peak_over_avg:.2f})", flush=True)
    return V


def compute_V_from_articles(dates: list, start_date: datetime, end_date: datetime) -> float:
    """
    Alternative V: from article count time series (if Trends not available).
    V = log(peak_week / avg_week) / log(max_observed)
    """
    # Build weekly counts
    week_counts = defaultdict(int)
    for d in dates:
        if d:
            try:
                parsed = datetime.strptime(str(d)[:10], "%Y-%m-%d")
                # Week number from start
                week = (parsed - start_date).days // 7
                if 0 <= week:
                    week_counts[week] += 1
            except Exception:
                continue

    if not week_counts:
        return 0.5

    counts = list(week_counts.values())
    peak = max(counts)
    avg = sum(counts) / len(counts)

    if avg == 0:
        return 0.5

    ratio = peak / avg
    # Normalize: log scale, cap at 20x
    V = round(min(1.0, math.log(max(1.0, ratio)) / math.log(20.0)), 4)
    print(f"  V = {V} (article-based: peak={peak}, avg={avg:.1f}, ratio={ratio:.2f})", flush=True)
    return V


# ── SRM Computation ───────────────────────────────────────────────────────────

def compute_SRM(V: float, A: float, N: float, lam: float, D: float) -> dict:
    """
    SRM = V * A * e^(-lambda * D) * N
    """
    srm = round(V * A * math.exp(-lam * D) * N, 6)
    return {
        "V": V,
        "A": A,
        "N": N,
        "lambda": lam,
        "D": D,
        "SRM": srm
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def load_csv(csv_path: str) -> tuple:
    """Load titles and dates from Media Cloud CSV."""
    titles = []
    dates = []
    with open(csv_path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row.get("title", "").strip()
            date = row.get("publish_date", "").strip()
            if title:
                titles.append(title)
                dates.append(date)
    return titles, dates


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compute V, A, N for SRM pipeline"
    )
    parser.add_argument("--csv",    required=True,            help="Path to Media Cloud CSV")
    parser.add_argument("--symbol", required=True,            help="Symbol name")
    parser.add_argument("--lam",    type=float, required=True, help="Lambda (from compute_lambda.py)")
    parser.add_argument("--start",  required=True,            help="Start date YYYY-MM-DD")
    parser.add_argument("--end",    required=True,            help="End date YYYY-MM-DD")
    parser.add_argument("--D",      type=float, default=None, help="D value (from compute_D.py)")
    parser.add_argument("--out",    default=None,             help="Output JSON path")
    parser.add_argument("--v-method", choices=["lambda", "articles"], default="lambda",
                        help="V computation method: 'lambda' (default) or 'articles'")
    args = parser.parse_args()

    print(f"\n=== compute_V_A_N.py — {args.symbol} ===", flush=True)

    # Parse dates
    start_date = datetime.strptime(args.start, "%Y-%m-%d")
    end_date   = datetime.strptime(args.end,   "%Y-%m-%d")
    T = (end_date - start_date).days / 365.25
    print(f"  Window: {args.start} → {args.end} ({T:.3f} years)", flush=True)

    # Load CSV
    titles, dates = load_csv(args.csv)
    print(f"  Loaded {len(titles)} articles from {args.csv}", flush=True)

    # Compute components
    if args.v_method == "lambda":
        V = compute_V_from_lambda(args.lam, T)
    else:
        V = compute_V_from_articles(dates, start_date, end_date)

    A = compute_A(titles)
    N = compute_N(dates, start_date, end_date)

    # Compute SRM if D provided
    result = {
        "symbol": args.symbol,
        "V": V,
        "A": A,
        "N": N,
        "lambda": args.lam,
        "start": args.start,
        "end": args.end,
        "n_articles": len(titles)
    }

    if args.D is not None:
        srm_val = round(V * A * math.exp(-args.lam * args.D) * N, 6)
        result["D"] = args.D
        result["SRM"] = srm_val
        print(f"\n  SRM = {srm_val}", flush=True)
        print(f"       V={V} × A={A} × e^(-{args.lam}×{args.D}) × N={N}", flush=True)

    # Save
    out_path = args.out or f"V_A_N_{args.symbol}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n  Saved to {out_path}", flush=True)
    print(f"\n  Summary: V={V}, A={A}, N={N}", flush=True)
