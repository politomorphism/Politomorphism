"""
Politomorphism Social Resonance Model — Full Pipeline
Pre-registration: github.com/politomorphing
ORCID: 0009-0000-2266-3356 | DOI: 10.17605/OSF.IO/HYDNZ
Locked: 2026-06-10T18:00:00Z
SHA-256: c09ebc717322a6a819708702af213b2d6a65b7e5a869c53200043f648826858a
"""

import json, hashlib, csv, math, sys
from typing import Dict, Optional

PROTOCOL_LOCK_DATE = "2026-06-10T18:00:00Z"
PROTOCOL_SHA256    = "c09ebc717322a6a819708702af213b2d6a65b7e5a869c53200043f648826858a"

COEFFICIENTS = {
    "alpha": 0.42,
    "beta":  0.18,
    "gamma": 0.91,
    "delta": -0.15,
}

EEF_BASELINES = {
    "RO": 0.9308, "PL": 0.7200, "HU": 0.7100, "DE": 0.6100,
    "FR": 0.7800, "IT": 0.5800, "ES": 0.6900, "US": 0.6800,
}

SRM_T0 = {
    "RO_AUR":   {"V":0.75,"A":0.21,"D":0.652,"N":0.83,"lam":38.20,"SRM":0.052,"P_t":38.2},
    "RO_PSD":   {"V":0.52,"A":0.19,"D":0.617,"N":0.71,"lam":6.57, "SRM":0.038,"P_t":17.5},
    "RO_PNL":   {"V":0.58,"A":0.20,"D":0.629,"N":0.74,"lam":7.01, "SRM":0.041,"P_t":20.3},
    "RO_USR":   {"V":0.43,"A":0.17,"D":0.660,"N":0.62,"lam":8.50, "SRM":0.028,"P_t":10.0},
    "RO_UDMR":  {"V":0.22,"A":0.12,"D":0.597,"N":0.48,"lam":2.31, "SRM":0.015,"P_t":5.0 },
    "RO_TOMAC": {"V":0.38,"A":0.25,"D":0.720,"N":0.58,"lam":4.20, "SRM":0.008,"P_t":None},
}


def srm_canonical(V, A, D, N, lam):
    return V * A * math.exp(-lam * D) * N


def srm_optimized(V, A, D, N, lam):
    return V * A * math.exp(-(lam ** 0.20) * (D ** 3.00)) * N


def predict_delta_p(srm_t, p_t, country, c=0, eef_override=None):
    eef = eef_override if eef_override is not None else EEF_BASELINES.get(country, 0.70)
    a = COEFFICIENTS
    p_pred = a["alpha"]*srm_t + a["beta"]*eef + a["gamma"]*p_t + a["delta"]*c
    delta_p = p_pred - p_t
    sigma = 2.5
    return {
        "delta_p_point": round(delta_p, 2),
        "sigma":         sigma,
        "ci95_lo":       round(delta_p - 2*sigma, 2),
        "ci95_hi":       round(delta_p + 2*sigma, 2),
        "p_t30_point":   round(p_pred, 2),
    }


def evaluate(predictions, actuals):
    keys = [k for k in predictions if k in actuals]
    preds = [predictions[k] for k in keys]
    obs   = [actuals[k]     for k in keys]
    n = len(keys)
    if n == 0:
        return {"error": "no matching keys"}
    mae  = sum(abs(p-o) for p,o in zip(preds,obs)) / n
    rmse = math.sqrt(sum((p-o)**2 for p,o in zip(preds,obs)) / n)
    mp, mo = sum(preds)/n, sum(obs)/n
    num = sum((p-mp)*(o-mo) for p,o in zip(preds,obs))
    sp  = math.sqrt(sum((p-mp)**2 for p in preds))
    so  = math.sqrt(sum((o-mo)**2 for o in obs))
    r   = (num/(sp*so)) if sp*so > 0 else 0.0
    dir_acc = sum(1 for p,o in zip(preds,obs) if (p>=0)==(o>=0)) / n * 100
    return {
        "n":               n,
        "MAE_pp":          round(mae, 3),
        "RMSE_pp":         round(rmse, 3),
        "pearson_r":       round(r, 3),
        "directional_acc": round(dir_acc, 1),
        "MAE_pass":        mae  < 3.0,
        "RMSE_pass":       rmse < 4.0,
        "r_pass":          r    > 0.50,
        "dir_pass":        dir_acc >= 60.0,
        "conditions_met":  sum([mae<3.0, rmse<4.0, r>0.50, dir_acc>=60.0]),
        "model_validated": sum([mae<3.0, rmse<4.0, r>0.50, dir_acc>=60.0]) >= 2,
    }


def generate_srm_csv(output_path="srm_values_t0_20260610.csv"):
    rows = []
    for actor, d in SRM_T0.items():
        rows.append({
            "actor":         actor,
            "V":             d["V"],
            "A":             d["A"],
            "D":             d["D"],
            "N":             d["N"],
            "lambda":        d["lam"],
            "SRM_canonical": round(srm_canonical(d["V"],d["A"],d["D"],d["N"],d["lam"]), 6),
            "SRM_optimized": round(srm_optimized(d["V"],d["A"],d["D"],d["N"],d["lam"]), 6),
            "P_t_baseline":  d["P_t"],
            "locked_utc":    PROTOCOL_LOCK_DATE,
        })
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"[OK] {output_path} written ({len(rows)} rows)")


def compute_and_show_predictions():
    print("\n=== POLITOMORPHISM PREDICTIONS — LOCKED 2026-06-10 ===\n")
    print(f"{'Actor':<12} {'P_t':>6} {'ΔP pred':>9} {'CI 95%':>16} {'SRM_t':>8}  λ")
    print("─" * 68)
    for actor, d in SRM_T0.items():
        if d["P_t"] is None:
            continue
        country = actor.split("_")[0]
        pred = predict_delta_p(d["SRM"], d["P_t"], country)
        ci = f"[{pred['ci95_lo']:+.1f}, {pred['ci95_hi']:+.1f}]"
        print(f"{actor:<12} {d['P_t']:>5.1f}%  {pred['delta_p_point']:>+6.1f} pp  {ci:>16}  {d['SRM']:>6.4f}  {d['lam']}")
    print()


def hash_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "predict"

    if cmd == "predict":
        compute_and_show_predictions()

    elif cmd == "csv":
        generate_srm_csv()

    elif cmd == "verify":
        path = sys.argv[2] if len(sys.argv) > 2 else "predictions_t0_20260610.json"
        h = hash_file(path)
        match = "✅ MATCH" if h == PROTOCOL_SHA256 else "❌ MISMATCH — file was modified"
        print(f"Expected: {PROTOCOL_SHA256}")
        print(f"Actual:   {h}")
        print(f"Status:   {match}")

    elif cmd == "evaluate":
        actuals = {}
        for pair in sys.argv[2:]:
            k, v = pair.split(":")
            actuals[k] = float(v)
        preds = {
            actor: predict_delta_p(d["SRM"], d["P_t"], actor.split("_")[0])["delta_p_point"]
            for actor, d in SRM_T0.items() if d["P_t"] is not None
        }
        print(json.dumps(evaluate(preds, actuals), indent=2))

    else:
        print("Commands: predict | csv | verify [file] | evaluate KEY:val ...")
