"""
calibrate_alpha.py — Calibrate alpha (PE/ICI weight) for SRM D operationalization
Politomorphism Research Project | Serban Gabriel Florin
License: CC BY 4.0

Uses the 12 validated SRM cases to find the optimal alpha that minimizes
the difference between D_new = alpha*PE + (1-alpha)*ICI and D_legacy.

Run AFTER compute_D.py has produced PE/ICI values for all 12 cases.
Until then, uses estimated PE/ICI from structural analysis.
"""

import numpy as np
import json
from scipy.optimize import minimize_scalar, minimize
from scipy.stats import pearsonr, spearmanr


# ── DATASET ──────────────────────────────────────────────────────────────────
# D_legacy: values from validated SRM pipeline
# PE_est, ICI_est: estimated from structural analysis (replace with real values
# once compute_D.py has been run on all 12 corpora)

CASES = [
    # name,                  D_legacy,  PE_est,  ICI_est,  lambda,  typology
    ("Sunflower Movement",   0.774,     0.72,    0.83,     None,    "Civic Mobilization"),
    ("Călin Georgescu",      0.881,     0.65,    0.97,     65.33,   "Flash Viral"),
    ("Marcel Ciolacu",       0.841,     0.78,    0.88,     6.57,    "Campaign/Ascension"),
    ("Donald Trump",         0.734,     0.75,    0.71,     7.01,    "Campaign/Ascension"),
    ("Volodymyr Zelensky",   0.680,     0.60,    0.74,     5.11,    "Institutionally Durable"),
    ("Vladimir Putin",       0.847,     0.80,    0.89,     4.90,    "Institutionally Durable"),
    ("George Simion",        0.812,     0.70,    0.86,     12.41,   "Electorally Volatile"),
    ("Viktor Orbán",         0.798,     0.82,    0.77,     2.31,    "Institutionally Durable"),
    ("Nelson Mandela",       0.742,     0.68,    0.79,     19.66,   "Electorally Volatile"),
    ("Emmanuel Macron",      0.810,     0.77,    0.84,     12.53,   "Electorally Volatile"),
    ("Hugo Chávez (sust.)",  0.720,     0.71,    0.73,     16.67,   "Electorally Volatile"),
    ("Hugo Chávez (acute)",  0.380,     0.30,    0.44,     16.67,   "Electorally Volatile"),
]

NAMES    = [c[0] for c in CASES]
D_legacy = np.array([c[1] for c in CASES])
PE_est   = np.array([c[2] for c in CASES])
ICI_est  = np.array([c[3] for c in CASES])
LAMBDAS  = [c[4] for c in CASES]
TYPES    = [c[5] for c in CASES]


# ── GLOBAL ALPHA CALIBRATION ─────────────────────────────────────────────────

def D_new(alpha, PE, ICI):
    return alpha * PE + (1 - alpha) * ICI

def rmse(alpha):
    pred = D_new(alpha, PE_est, ICI_est)
    return float(np.sqrt(np.mean((pred - D_legacy) ** 2)))

def mae(alpha):
    pred = D_new(alpha, PE_est, ICI_est)
    return float(np.mean(np.abs(pred - D_legacy)))

def calibrate_global():
    result = minimize_scalar(rmse, bounds=(0.0, 1.0), method="bounded")
    alpha_opt = round(result.x, 4)
    rmse_opt  = round(result.fun, 4)

    # Also report at alpha=0.5 (default)
    rmse_05 = round(rmse(0.5), 4)
    mae_05  = round(mae(0.5), 4)
    mae_opt = round(mae(alpha_opt), 4)

    pred_opt = D_new(alpha_opt, PE_est, ICI_est)
    r_pearson, p_pearson  = pearsonr(pred_opt, D_legacy)
    r_spearman, p_spearman = spearmanr(pred_opt, D_legacy)

    return {
        "alpha_optimal":   alpha_opt,
        "RMSE_at_alpha_opt": rmse_opt,
        "MAE_at_alpha_opt":  mae_opt,
        "RMSE_at_alpha_05":  rmse_05,
        "MAE_at_alpha_05":   mae_05,
        "pearson_r":     round(r_pearson, 4),
        "pearson_p":     round(p_pearson, 4),
        "spearman_r":    round(r_spearman, 4),
        "spearman_p":    round(p_spearman, 4),
        "verdict": "Use alpha=0.5" if abs(alpha_opt - 0.5) < 0.05
                   else f"Consider updating to alpha={alpha_opt}"
    }


# ── PER-TYPOLOGY ALPHA CALIBRATION ───────────────────────────────────────────

def calibrate_by_typology():
    typologies = list(set(TYPES))
    results = {}

    for typ in typologies:
        idx = [i for i, t in enumerate(TYPES) if t == typ]
        if len(idx) < 2:
            results[typ] = {
                "n": len(idx),
                "note": "Insufficient cases for calibration (n<2)"
            }
            continue

        PE_t  = PE_est[idx]
        ICI_t = ICI_est[idx]
        D_t   = D_legacy[idx]

        def rmse_t(alpha):
            pred = D_new(alpha, PE_t, ICI_t)
            return float(np.sqrt(np.mean((pred - D_t) ** 2)))

        res = minimize_scalar(rmse_t, bounds=(0.0, 1.0), method="bounded")
        alpha_t = round(res.x, 4)
        rmse_t_val = round(res.fun, 4)

        # Interpretation
        if alpha_t < 0.35:
            interpretation = "ICI-dominant: framing contestation drives D in this category"
        elif alpha_t > 0.65:
            interpretation = "PE-dominant: topical breadth drives D in this category"
        else:
            interpretation = "Balanced: PE and ICI contribute equally"

        results[typ] = {
            "n":             len(idx),
            "cases":         [NAMES[i] for i in idx],
            "alpha_optimal": alpha_t,
            "RMSE":          rmse_t_val,
            "PE_mean":       round(float(PE_t.mean()), 4),
            "ICI_mean":      round(float(ICI_t.mean()), 4),
            "D_legacy_mean": round(float(D_t.mean()), 4),
            "interpretation": interpretation
        }

    return results


# ── PER-CASE DECOMPOSITION ────────────────────────────────────────────────────

def per_case_decomposition(alpha: float = 0.5):
    rows = []
    for i, name in enumerate(NAMES):
        d_new = round(D_new(alpha, PE_est[i], ICI_est[i]), 4)
        delta = round(d_new - D_legacy[i], 4)
        dominant = "PE" if PE_est[i] > ICI_est[i] else "ICI"
        rows.append({
            "symbol":      name,
            "typology":    TYPES[i],
            "D_legacy":    D_legacy[i],
            "PE_est":      PE_est[i],
            "ICI_est":     ICI_est[i],
            "D_new":       d_new,
            "delta":       delta,
            "dominant":    dominant,
            "H1_support":  TYPES[i] == "Flash Viral" and ICI_est[i] > PE_est[i],
        })
    return rows


# ── H1 TEST ───────────────────────────────────────────────────────────────────

def test_H1():
    """H1: Flash Viral symbols are ICI-dominant (ICI >> PE)."""
    flash = [i for i, t in enumerate(TYPES) if t == "Flash Viral"]
    non_flash = [i for i, t in enumerate(TYPES) if t != "Flash Viral"]

    flash_ici_pe_ratio    = np.mean([ICI_est[i] / PE_est[i] for i in flash])
    nonflash_ici_pe_ratio = np.mean([ICI_est[i] / PE_est[i] for i in non_flash])

    return {
        "hypothesis": "H1: Flash Viral symbols are ICI-dominant (ICI > PE)",
        "flash_viral_cases": [NAMES[i] for i in flash],
        "flash_ICI_mean":    round(float(np.mean([ICI_est[i] for i in flash])), 4),
        "flash_PE_mean":     round(float(np.mean([PE_est[i] for i in flash])), 4),
        "flash_ICI_PE_ratio": round(float(flash_ici_pe_ratio), 4),
        "nonflash_ICI_PE_ratio": round(float(nonflash_ici_pe_ratio), 4),
        "supported": bool(flash_ici_pe_ratio > nonflash_ici_pe_ratio and
                         all(ICI_est[i] > PE_est[i] for i in flash)),
        "note": "Based on estimated PE/ICI. Replace with compute_D.py output for definitive test."
    }


# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== calibrate_alpha.py ===")
    print("NOTE: Using estimated PE/ICI values. Run compute_D.py on all 12 corpora")
    print("      and update CASES table for definitive calibration.\n")

    print("--- Global alpha calibration ---")
    global_result = calibrate_global()
    for k, v in global_result.items():
        print(f"  {k}: {v}")

    print("\n--- Per-typology calibration ---")
    typo_result = calibrate_by_typology()
    for typ, res in typo_result.items():
        print(f"\n  [{typ}]")
        for k, v in res.items():
            print(f"    {k}: {v}")

    print("\n--- Per-case decomposition (alpha=0.5) ---")
    cases = per_case_decomposition(0.5)
    print(f"  {'Symbol':<30} {'D_leg':>6} {'PE':>6} {'ICI':>6} {'D_new':>6} {'Δ':>6} {'Dom':>4}")
    print("  " + "-"*70)
    for c in cases:
        print(f"  {c['symbol']:<30} {c['D_legacy']:>6.3f} {c['PE_est']:>6.3f} "
              f"{c['ICI_est']:>6.3f} {c['D_new']:>6.3f} {c['delta']:>+6.3f} {c['dominant']:>4}")

    print("\n--- H1 preliminary test ---")
    h1 = test_H1()
    for k, v in h1.items():
        print(f"  {k}: {v}")

    # Save full output
    output = {
        "note": "Estimated values — replace PE_est/ICI_est with compute_D.py output",
        "global_calibration":      global_result,
        "typology_calibration":    typo_result,
        "per_case_decomposition":  cases,
        "H1_test":                 h1
    }
    with open("alpha_calibration_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print("\nSaved: alpha_calibration_results.json")
