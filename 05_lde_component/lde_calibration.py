"""
LDE — Legitimacy Dynamics Engine: Calibration Script
Preprint #4: Cross-national empirical calibration on Standard Eurobarometer data (2014–2025)
Serban Gabriel Florin | ORCID: 0009-0000-2266-3356
GitHub: github.com/profserbangabriel/Politomorphism
License: CC BY 4.0
"""

import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution
import warnings
warnings.filterwarnings("ignore")

# ── Seed for reproducibility ──────────────────────────────────────────────────
np.random.seed(42)

# ── 1. Data ───────────────────────────────────────────────────────────────────
# L(t): proportion trusting national government
# Source: Standard Eurobarometer EB82–EB104, variable QA8a.11 / QA6.7
# Waves: biennial, 2014–2025 (9 observations per country)

DATA = {
    "Greece": {
        "years": [2014, 2016, 2018, 2019, 2020, 2021, 2022, 2023, 2025],
        "L":     [0.090, 0.130, 0.180, 0.220, 0.260, 0.280, 0.290, 0.270, 0.250],
    },
    "Hungary": {
        "years": [2014, 2016, 2018, 2019, 2020, 2021, 2022, 2023, 2025],
        "L":     [0.330, 0.360, 0.380, 0.400, 0.480, 0.450, 0.430, 0.410, 0.390],
    },
    "Serbia": {
        "years": [2014, 2016, 2018, 2019, 2020, 2021, 2022, 2023, 2025],
        "L":     [0.370, 0.390, 0.440, 0.460, 0.480, 0.470, 0.450, 0.420, 0.400],
    },
    # Exploratory cases
    "Moldova": {
        "years": [2022, 2023, 2024, 2025],
        "L":     [0.230, 0.290, 0.360, 0.410],
    },
}

# ── 2. LDE model ──────────────────────────────────────────────────────────────

def lde_simulate(L0, L_star, params, n_steps):
    """
    Simulate the LDE forward from L0.

    L(t+1) = L(t) + lambda * [alpha*P(t) + beta*N(t) - gamma*C(t)] - theta*[L(t) - L*]

    In this calibration, P(t), N(t), C(t) are not directly observed.
    The model is estimated as a structured autoregressive process:
    the driver term collapses to a net drift captured by the parameters,
    and mean reversion pulls toward the within-series mean L*.

    Parameters
    ----------
    L0      : float, initial legitimacy value
    L_star  : float, long-run equilibrium (within-series mean)
    params  : tuple (lam, alpha, beta, gamma, theta)
    n_steps : int, number of steps to simulate
    """
    lam, alpha, beta, gamma, theta = params
    L = np.zeros(n_steps)
    L[0] = L0

    for t in range(n_steps - 1):
        # Net driver signal: alpha*P - gamma*C approximated as (alpha - gamma) * trend_signal
        # beta*N captured in mean-reversion equilibrium
        # With unobserved P, N, C: driver = (alpha + beta - gamma) normalized by series mean
        driver = lam * (alpha * L_star + beta * L_star - gamma * (1 - L_star))
        reversion = theta * (L[t] - L_star)
        L[t + 1] = np.clip(L[t] + driver - reversion, 0.0, 1.0)

    return L


def rmse(observed, simulated):
    return np.sqrt(np.mean((observed - simulated) ** 2))


def r_squared(observed, simulated):
    ss_res = np.sum((observed - simulated) ** 2)
    ss_tot = np.sum((observed - np.mean(observed)) ** 2)
    if ss_tot == 0:
        return 0.0
    return 1.0 - ss_res / ss_tot


def objective(params, L_obs, L_star):
    L_sim = lde_simulate(L_obs[0], L_star, params, len(L_obs))
    return rmse(L_obs, L_sim)


# ── 3. Calibration ────────────────────────────────────────────────────────────

# Parameter bounds: (lambda, alpha, beta, gamma, theta)
BOUNDS = [(0.01, 2.0), (0.0, 2.0), (0.0, 2.0), (0.0, 2.0), (0.0, 1.0)]

def calibrate(country_name, data, n_bootstrap=500):
    L_obs = np.array(data["L"])
    L_star = np.mean(L_obs)
    n = len(L_obs)

    print(f"\n{'='*60}")
    print(f"  {country_name}  (N={n}, L*={L_star:.3f})")
    print(f"{'='*60}")

    # ── 3a. Differential evolution ───────────────────────────────────────────
    result = differential_evolution(
        objective,
        bounds=BOUNDS,
        args=(L_obs, L_star),
        seed=42,
        maxiter=1000,
        popsize=15,
        tol=1e-7,
        polish=True,
    )

    best_params = result.x
    lam, alpha, beta, gamma, theta = best_params
    L_sim = lde_simulate(L_obs[0], L_star, best_params, n)
    lde_rmse = rmse(L_obs, L_sim)
    r2 = r_squared(L_obs, L_sim)

    # Random walk baseline
    rw_rmse = np.std(np.diff(L_obs))

    delta_rw = (rw_rmse - lde_rmse) / rw_rmse * 100 if rw_rmse > 0 else 0.0

    print(f"  λ={lam:.3f}  α={alpha:.3f}  β={beta:.3f}  γ={gamma:.3f}  θ={theta:.3f}")
    print(f"  RMSE={lde_rmse:.4f}  RW_RMSE={rw_rmse:.4f}  ΔRW={delta_rw:+.1f}%  R²={r2:.3f}")

    # ── 3b. Bootstrap CI for R² ──────────────────────────────────────────────
    residuals = L_obs - L_sim
    boot_r2 = []

    for _ in range(n_bootstrap):
        boot_residuals = np.random.choice(residuals, size=n, replace=True)
        L_boot = np.clip(L_sim + boot_residuals, 0.0, 1.0)
        L_boot[0] = L_obs[0]  # fix initial value

        res_boot = differential_evolution(
            objective,
            bounds=BOUNDS,
            args=(L_boot, np.mean(L_boot)),
            seed=None,
            maxiter=500,
            popsize=10,
            tol=1e-6,
            polish=False,
        )
        L_sim_boot = lde_simulate(L_boot[0], np.mean(L_boot), res_boot.x, n)
        boot_r2.append(r_squared(L_boot, L_sim_boot))

    ci_lo = np.percentile(boot_r2, 2.5)
    ci_hi = np.percentile(boot_r2, 97.5)
    print(f"  Bootstrap R² CI (95%): [{ci_lo:.3f}, {ci_hi:.3f}]  (n={n_bootstrap})")

    return {
        "country": country_name,
        "n": n,
        "mean_L": L_star,
        "sd_L": np.std(L_obs),
        "lambda": lam,
        "alpha": alpha,
        "beta": beta,
        "gamma": gamma,
        "theta": theta,
        "lde_rmse": lde_rmse,
        "rw_rmse": rw_rmse,
        "delta_rw_pct": delta_rw,
        "r2": r2,
        "ci_lo_95": ci_lo,
        "ci_hi_95": ci_hi,
        "boot_r2_samples": boot_r2,
    }


# ── 4. Alpha boundary sensitivity test ───────────────────────────────────────
# Addresses the boundary-solution concern (alpha=2.0 in all countries).
# We re-run calibration with an extended alpha grid [0, 5] to test whether
# the parameter would migrate beyond 2.0 if unconstrained.

BOUNDS_EXTENDED = [(0.01, 2.0), (0.0, 5.0), (0.0, 2.0), (0.0, 2.0), (0.0, 1.0)]

def calibrate_extended_alpha(country_name, data):
    L_obs = np.array(data["L"])
    L_star = np.mean(L_obs)

    result = differential_evolution(
        objective,
        bounds=BOUNDS_EXTENDED,
        args=(L_obs, L_star),
        seed=42,
        maxiter=1000,
        popsize=15,
        tol=1e-7,
        polish=True,
    )

    best_params = result.x
    lam, alpha, beta, gamma, theta = best_params
    L_sim = lde_simulate(L_obs[0], L_star, best_params, len(L_obs))
    lde_rmse = rmse(L_obs, L_sim)
    r2 = r_squared(L_obs, L_sim)

    return {
        "country": country_name,
        "alpha_extended": alpha,
        "lde_rmse_extended": lde_rmse,
        "r2_extended": r2,
    }


# ── 5. Main ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # Primary sample
    primary = ["Greece", "Hungary", "Serbia"]
    results = []

    for country in primary:
        res = calibrate(country, DATA[country], n_bootstrap=500)
        results.append(res)

    # Moldova exploratory
    mol = calibrate("Moldova", DATA["Moldova"], n_bootstrap=500)
    results.append(mol)

    # ── Save main results ────────────────────────────────────────────────────
    summary_rows = []
    for r in results:
        summary_rows.append({
            "country":      r["country"],
            "n":            r["n"],
            "mean_L":       round(r["mean_L"], 3),
            "sd_L":         round(r["sd_L"], 3),
            "lambda":       round(r["lambda"], 3),
            "alpha":        round(r["alpha"], 3),
            "beta":         round(r["beta"], 3),
            "gamma":        round(r["gamma"], 3),
            "theta":        round(r["theta"], 3),
            "lde_rmse":     round(r["lde_rmse"], 4),
            "rw_rmse":      round(r["rw_rmse"], 4),
            "delta_rw_pct": round(r["delta_rw_pct"], 1),
            "r2":           round(r["r2"], 3),
            "ci_lo_95":     round(r["ci_lo_95"], 3),
            "ci_hi_95":     round(r["ci_hi_95"], 3),
        })

    df_summary = pd.DataFrame(summary_rows)
    df_summary.to_csv("lde_results_summary.csv", index=False)
    print("\n✓ Saved: lde_results_summary.csv")

    # ── Save bootstrap samples ───────────────────────────────────────────────
    boot_dict = {}
    for r in results:
        boot_dict[r["country"]] = r["boot_r2_samples"]

    df_boot = pd.DataFrame(boot_dict)
    df_boot.to_csv("bootstrap_r2_samples.csv", index=False)
    print("✓ Saved: bootstrap_r2_samples.csv")

    # ── Alpha boundary sensitivity ───────────────────────────────────────────
    print("\n--- Alpha boundary sensitivity (extended grid α ∈ [0, 5]) ---")
    ext_rows = []
    for country in primary:
        ext = calibrate_extended_alpha(country, DATA[country])
        print(f"  {country}: α_extended={ext['alpha_extended']:.3f}  "
              f"RMSE={ext['lde_rmse_extended']:.4f}  R²={ext['r2_extended']:.3f}")
        ext_rows.append(ext)

    df_ext = pd.DataFrame(ext_rows)
    df_ext.to_csv("alpha_sensitivity_extended.csv", index=False)
    print("✓ Saved: alpha_sensitivity_extended.csv")

    print("\n✓ All done. Files ready for upload to GitHub.")
