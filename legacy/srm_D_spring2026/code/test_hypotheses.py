"""
test_hypotheses.py — Formal testing of H1, H2, H3 for SRM D operationalization
Politomorphism Research Project | Serban Gabriel Florin
License: CC BY 4.0

Tests three falsifiable hypotheses derived from the PE/ICI decomposition:
  H1: Flash Viral symbols are ICI-dominant
  H2: Romanian media ecosystem imposes a structural ICI ceiling (correlated ICI, uncorrelated PE)
  H3: Zelensky's low D reflects ICI suppression, not PE suppression

Run after compute_D.py has produced real PE/ICI values.
Currently uses estimated values — replace DATA dict entries with real output.
"""

import numpy as np
import json
from scipy.stats import pearsonr, spearmanr, ttest_ind, mannwhitneyu


# ── DATA ──────────────────────────────────────────────────────────────────────
# Replace PE and ICI with real values from compute_D.py output
# Format: symbol_key: {PE, ICI, D_legacy, lambda, typology, country}

DATA = {
    "georgescu": {
        "name": "Călin Georgescu", "country": "RO",
        "PE": 0.65, "ICI": 0.97, "D_legacy": 0.881,
        "lambda": 65.33, "typology": "Flash Viral",
        "real_values": False  # set True when compute_D.py output available
    },
    "charlie_hebdo": {
        "name": "Charlie Hebdo", "country": "FR",
        "PE": 0.58, "ICI": 0.94, "D_legacy": None,
        "lambda": 104.66, "typology": "Flash Viral",
        "real_values": False
    },
    "ciolacu": {
        "name": "Marcel Ciolacu", "country": "RO",
        "PE": 0.78, "ICI": 0.88, "D_legacy": 0.841,
        "lambda": 6.57, "typology": "Campaign/Ascension",
        "real_values": False
    },
    "simion": {
        "name": "George Simion", "country": "RO",
        "PE": 0.70, "ICI": 0.86, "D_legacy": 0.812,
        "lambda": 12.41, "typology": "Electorally Volatile",
        "real_values": False
    },
    "zelensky": {
        "name": "Volodymyr Zelensky", "country": "UA",
        "PE": 0.60, "ICI": 0.74, "D_legacy": 0.680,
        "lambda": 5.11, "typology": "Institutionally Durable",
        "real_values": False
    },
    "putin": {
        "name": "Vladimir Putin", "country": "RU",
        "PE": 0.80, "ICI": 0.89, "D_legacy": 0.847,
        "lambda": 4.90, "typology": "Institutionally Durable",
        "real_values": False
    },
    "orban": {
        "name": "Viktor Orbán", "country": "HU",
        "PE": 0.82, "ICI": 0.77, "D_legacy": 0.798,
        "lambda": 2.31, "typology": "Institutionally Durable",
        "real_values": False
    },
    "trump": {
        "name": "Donald Trump", "country": "US",
        "PE": 0.75, "ICI": 0.71, "D_legacy": 0.734,
        "lambda": 7.01, "typology": "Campaign/Ascension",
        "real_values": False
    },
    "macron": {
        "name": "Emmanuel Macron", "country": "FR",
        "PE": 0.77, "ICI": 0.84, "D_legacy": 0.810,
        "lambda": 12.53, "typology": "Electorally Volatile",
        "real_values": False
    },
    "mandela": {
        "name": "Nelson Mandela", "country": "SA",
        "PE": 0.68, "ICI": 0.79, "D_legacy": 0.742,
        "lambda": 19.66, "typology": "Electorally Volatile",
        "real_values": False
    },
    "chavez_sust": {
        "name": "Hugo Chávez (sustained)", "country": "VE",
        "PE": 0.71, "ICI": 0.73, "D_legacy": 0.720,
        "lambda": 16.67, "typology": "Electorally Volatile",
        "real_values": False
    },
    "chavez_acute": {
        "name": "Hugo Chávez (acute)", "country": "VE",
        "PE": 0.30, "ICI": 0.44, "D_legacy": 0.380,
        "lambda": 16.67, "typology": "Electorally Volatile",
        "real_values": False
    },
    "sunflower": {
        "name": "Sunflower Movement", "country": "TW",
        "PE": 0.72, "ICI": 0.83, "D_legacy": 0.774,
        "lambda": None, "typology": "Civic Mobilization",
        "real_values": False
    },
}

all_estimated = not any(v["real_values"] for v in DATA.values())


# ── H1: Flash Viral symbols are ICI-dominant ─────────────────────────────────

def test_H1():
    """
    H1: Flash Viral symbols have ICI >> PE.
    Mechanism: media polarization (not topical breadth) drives high D.
    Falsification: H1 is false if PE(flash) >= ICI(flash).
    """
    flash_keys    = [k for k, v in DATA.items() if v["typology"] == "Flash Viral"]
    nonflash_keys = [k for k, v in DATA.items() if v["typology"] != "Flash Viral"
                     and v["D_legacy"] is not None]

    flash_PE  = [DATA[k]["PE"]  for k in flash_keys]
    flash_ICI = [DATA[k]["ICI"] for k in flash_keys]
    nf_PE     = [DATA[k]["PE"]  for k in nonflash_keys]
    nf_ICI    = [DATA[k]["ICI"] for k in nonflash_keys]

    # ICI/PE ratio comparison
    flash_ratio = np.mean([DATA[k]["ICI"] / DATA[k]["PE"] for k in flash_keys])
    nf_ratio    = np.mean([DATA[k]["ICI"] / DATA[k]["PE"] for k in nonflash_keys])

    # All flash cases: ICI > PE?
    all_ici_dominant = all(DATA[k]["ICI"] > DATA[k]["PE"] for k in flash_keys)

    # Mann-Whitney test: ICI_flash vs ICI_nonflash
    if len(flash_ICI) >= 2 and len(nf_ICI) >= 2:
        stat, p = mannwhitneyu(flash_ICI, nf_ICI, alternative="greater")
    else:
        stat, p = None, None

    supported = all_ici_dominant and flash_ratio > nf_ratio

    return {
        "hypothesis": "H1: Flash Viral symbols are ICI-dominant (ICI > PE)",
        "flash_cases": [DATA[k]["name"] for k in flash_keys],
        "flash_PE_values":  flash_PE,
        "flash_ICI_values": flash_ICI,
        "flash_ICI_PE_ratio":    round(float(flash_ratio), 4),
        "nonflash_ICI_PE_ratio": round(float(nf_ratio), 4),
        "all_flash_ICI_dominant": all_ici_dominant,
        "mannwhitney_stat": stat,
        "mannwhitney_p":    round(p, 4) if p is not None else None,
        "supported":        supported,
        "confidence":       "LOW (estimated values)" if all_estimated else "HIGH (real values)",
        "falsification_condition": "H1 false if PE(Georgescu) >= ICI(Georgescu)"
    }


# ── H2: Romanian structural ICI ceiling ──────────────────────────────────────

def test_H2():
    """
    H2: Romanian Triad has correlated ICI (shared ecosystem ceiling)
        but uncorrelated PE (individual diffusion patterns).
    Falsification: H2 false if ICI variance == PE variance for Romanian symbols.
    """
    ro_keys = [k for k, v in DATA.items() if v["country"] == "RO"]

    ro_PE  = np.array([DATA[k]["PE"]  for k in ro_keys])
    ro_ICI = np.array([DATA[k]["ICI"] for k in ro_keys])

    pe_var  = round(float(np.var(ro_PE)),  6)
    ici_var = round(float(np.var(ro_ICI)), 6)
    pe_std  = round(float(np.std(ro_PE)),  4)
    ici_std = round(float(np.std(ro_ICI)), 4)

    # Compare variance: low ICI variance = structural ceiling
    ici_ceiling = ici_std < pe_std

    # For n=3, Pearson is not meaningful — report raw values only
    ro_names = [DATA[k]["name"] for k in ro_keys]

    return {
        "hypothesis": "H2: Romanian media ecosystem imposes structural ICI ceiling",
        "romanian_triad": ro_names,
        "PE_values":  list(ro_PE),
        "ICI_values": list(ro_ICI),
        "PE_variance":  pe_var,
        "ICI_variance": ici_var,
        "PE_std":  pe_std,
        "ICI_std": ici_std,
        "ICI_ceiling_detected": ici_ceiling,
        "supported": ici_ceiling,
        "confidence": "LOW (estimated values, n=3)" if all_estimated else "MEDIUM (real values, n=3)",
        "note": "n=3 limits statistical power. Consistent direction required for support.",
        "falsification_condition": "H2 false if ICI variance >= PE variance for Romanian symbols"
    }


# ── H3: Zelensky wartime coherence is ICI suppression ────────────────────────

def test_H3():
    """
    H3: Zelensky's low D=0.680 reflects low ICI (wartime convergence),
        not PE suppression. Zelensky PE should be moderate-to-high.
    Falsification: H3 false if PE(Zelensky) < ICI(Zelensky).
    """
    z  = DATA["zelensky"]
    pu = DATA["putin"]

    # Compare Zelensky to dataset means
    all_PE  = np.array([v["PE"]  for v in DATA.values()])
    all_ICI = np.array([v["ICI"] for v in DATA.values()])

    z_pe_percentile  = round(float(np.mean(all_PE  < z["PE"]))  * 100, 1)
    z_ici_percentile = round(float(np.mean(all_ICI < z["ICI"])) * 100, 1)

    # Mechanism test: ICI < PE means ICI suppression
    ici_suppression = z["ICI"] < z["PE"]

    # Compare to Putin (same conflict, opposite framing)
    putin_delta_ici = round(pu["ICI"] - z["ICI"], 4)
    putin_delta_pe  = round(pu["PE"]  - z["PE"],  4)

    return {
        "hypothesis": "H3: Zelensky's lower D reflects ICI suppression (wartime media convergence)",
        "zelensky_PE":  z["PE"],
        "zelensky_ICI": z["ICI"],
        "zelensky_D":   z["D_legacy"],
        "mechanism_test": "ICI < PE → ICI suppression" if ici_suppression
                          else "PE < ICI → PE suppression (H3 contradicted)",
        "ICI_suppression_detected": ici_suppression,
        "zelensky_PE_percentile":  z_pe_percentile,
        "zelensky_ICI_percentile": z_ici_percentile,
        "putin_comparison": {
            "putin_PE":  pu["PE"],
            "putin_ICI": pu["ICI"],
            "delta_ICI": putin_delta_ici,
            "delta_PE":  putin_delta_pe,
            "interpretation": "Putin higher ICI = divergent international framing" if putin_delta_ici > 0
                              else "Putin lower ICI (unexpected)"
        },
        "supported": ici_suppression,
        "confidence": "LOW (estimated values)" if all_estimated else "HIGH (real values)",
        "falsification_condition": "H3 false if PE(Zelensky) < ICI(Zelensky)"
    }


# ── SENSITIVITY ANALYSIS ──────────────────────────────────────────────────────

def sensitivity_table():
    """Reproduce SRM confidence intervals for key cases."""
    key_cases = [
        ("Trump",     0.958, 0.580, 0.734, 0.720,  7.01),
        ("Ciolacu",   0.720, 0.420, 0.841, 0.650,  6.57),
        ("Zelensky",  0.873, 0.640, 0.680, 0.781,  5.11),
        ("Georgescu", 0.750, 0.398, 0.881, 0.600, 65.33),
        ("Chávez",    0.186, 0.290, 0.720, 0.941, 16.67),
    ]
    eps = 0.05
    rows = []
    for name, V, A, D, N, lam in key_cases:
        srm       = V * A * np.exp(-lam * D)      * N
        srm_low   = V * A * np.exp(-lam * (D+eps)) * N
        srm_high  = V * A * np.exp(-lam * (D-eps)) * N
        interval  = ((srm_high - srm_low) / srm * 100) if srm > 0 else None
        multiplier = np.exp(2 * lam * eps)
        rows.append({
            "symbol":     name,
            "lambda":     lam,
            "D":          D,
            "SRM_point":  round(srm, 5),
            "SRM_low":    round(srm_low, 5),
            "SRM_high":   round(srm_high, 5),
            "interval_pct": round(interval, 1) if interval else None,
            "multiplier": round(multiplier, 2)
        })
    return rows


# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== test_hypotheses.py ===")
    if all_estimated:
        print("⚠  WARNING: All PE/ICI values are estimates.")
        print("   Run compute_D.py on all 12 corpora and update DATA dict.\n")

    print("--- H1: Flash Viral symbols are ICI-dominant ---")
    h1 = test_H1()
    for k, v in h1.items():
        print(f"  {k}: {v}")

    print("\n--- H2: Romanian structural ICI ceiling ---")
    h2 = test_H2()
    for k, v in h2.items():
        print(f"  {k}: {v}")

    print("\n--- H3: Zelensky wartime coherence is ICI suppression ---")
    h3 = test_H3()
    for k, v in h3.items():
        print(f"  {k}: {v}")

    print("\n--- Sensitivity analysis (eps=0.05) ---")
    sens = sensitivity_table()
    print(f"  {'Symbol':<12} {'λ':>6} {'D':>6} {'SRM':>8} {'Low':>8} {'High':>8} {'±%':>6} {'×':>6}")
    print("  " + "-"*64)
    for r in sens:
        print(f"  {r['symbol']:<12} {r['lambda']:>6.2f} {r['D']:>6.3f} "
              f"{r['SRM_point']:>8.4f} {r['SRM_low']:>8.4f} {r['SRM_high']:>8.4f} "
              f"{r['interval_pct']:>5.0f}% {r['multiplier']:>6.1f}×")

    # Save
    output = {
        "note": "Replace estimated PE/ICI with compute_D.py output for definitive results",
        "H1": h1,
        "H2": h2,
        "H3": h3,
        "sensitivity_analysis": sens
    }
    with open("hypothesis_test_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print("\nSaved: hypothesis_test_results.json")

    # Summary
    print("\n=== SUMMARY ===")
    for label, h in [("H1", h1), ("H2", h2), ("H3", h3)]:
        status = "SUPPORTED ✓" if h["supported"] else "NOT SUPPORTED ✗"
        conf   = h["confidence"]
        print(f"  {label}: {status}  [{conf}]")
