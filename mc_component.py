"""
Politomorphism Engine — Component 1: Metapolitical Calibration (MC)
===================================================================
Șerban, G. F. | ORCID: 0009-0000-2266-3356
OSF: https://doi.org/10.17605/OSF.IO/HYDNZ

MC v2.0 — RECONSTRUCTION (November 2026)

The original mc_component.py (June 2026) was lost. This module was rebuilt
from the published specification (SSRN 6918918; CPA working paper v1.0,
Table 1 and section 2.3) and from the interface that mc_run.py expects.
It is NOT the original code: estimates produced with it are new estimates
and will differ from the June 2026 values saved in MC_results.csv.

Core equation:
    S(t+1) = (1 − α)·S(t) + α·W·I(t) + β·SRM(t−1) + ε_MC(t)

Where:
    S(t)    : actor state vector, dim_s dimensions
              (in mc_run.py: [poll share / 100, SRM score])
    I(t)    : noosphere input vector, dim_i dimensions
              (in mc_run.py: [emotional valence, narrative dominance,
               geopolitical signal])
    W       : dim_s × dim_i projection matrix from inputs to state
    α       : learning (recalibration) rate, 0 ≤ α ≤ 1
    β       : SRM feedback coefficient (resonance of the previous period)
    SRM(t)  : symbolic resonance score of the actor

Estimation (choices made in this reconstruction, stated explicitly):
    1. The trajectory is simulated from the first observation S(0); the fit
       is on the simulated path, not on one-step-ahead predictions, the same
       approach used in cmg_component.py.
    2. For a fixed α, the simulated path is linear in W and β, so W and β
       are obtained exactly by least squares (variable projection). α is
       then chosen by a grid search over [0, 1] refined with a bounded
       scalar search. This avoids local minima and makes the fit
       deterministic.
    3. W can instead be fixed by the user (argument W in fit). The default
       estimates W, as the equation treats it as a parameter.
    4. SRM(t−1) for the first period is not observed; SRM(0) is used.
    5. The objective is the RMSE over all state dimensions and periods
       1..T. R² is reported per dimension over the same periods.

Identification warning:
    With W estimated, each actor has dim_s·dim_i + 2 parameters (8 in
    mc_run.py) for dim_s·T observations (24 for 12 quarters). β then
    competes with W·I for the same variance and is weakly identified.
    Run this file directly (python mc_component.py) for a parameter
    recovery check on synthetic data at T = 12 and T = 40.
"""

import numpy as np
from scipy.optimize import minimize_scalar


class MetapoliticalCalibration:
    """
    MC component of the Politomorphism Engine.

    Parameters
    ----------
    dim_s : int
        Dimensionality of the actor state S (default 2).
    dim_i : int
        Dimensionality of the noosphere input I (default 3).
    """

    def __init__(self, dim_s=2, dim_i=3):
        self.dim_s = dim_s
        self.dim_i = dim_i
        self.alpha = None
        self.beta = None
        self.W = None
        self.fitted = False
        self.results_ = {}

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------

    @staticmethod
    def _lagged_srm(SRM_series):
        """SRM(t−1) for t = 0..T−1, with SRM(0) standing in for SRM(−1)."""
        SRM = np.asarray(SRM_series, dtype=float)
        return np.r_[SRM[0], SRM[:-1]]

    def simulate(self, S0, I_series, SRM_series, alpha, beta, W):
        """
        Simulate the MC trajectory.

        Parameters
        ----------
        S0         : np.ndarray [dim_s] — initial state
        I_series   : np.ndarray [T x dim_i] — noosphere inputs
        SRM_series : np.ndarray [T] — SRM scores
        alpha, beta: float
        W          : np.ndarray [dim_s x dim_i]

        Returns
        -------
        np.ndarray [T+1 x dim_s]
        """
        I = np.asarray(I_series, dtype=float)
        R_lag = self._lagged_srm(SRM_series)
        T = len(I)
        S = np.zeros((T + 1, self.dim_s))
        S[0] = S0
        for t in range(T):
            S[t + 1] = (1 - alpha) * S[t] + alpha * (W @ I[t]) + beta * R_lag[t]
        return S

    def _design(self, S0, I, R_lag, alpha):
        """
        For a fixed α the simulated path is
            S(t) = (1−α)^t·S(0) + Σ_k (1−α)^(t−1−k)·[α·W·I(k) + β·R(k−1)]
        which is linear in (W, β). Returns the offset and the design
        matrix so that vec(S(1..T)) = offset + X @ theta, with
        theta = [vec(W) (row-major), β].
        """
        T = len(I)
        ds, di = self.dim_s, self.dim_i
        decay = 1 - alpha
        # Accumulated inputs: A_I(t) = Σ_k decay^(t−1−k) · α · I(k)
        A_I = np.zeros((T + 1, di))
        A_R = np.zeros(T + 1)
        offset_path = np.zeros((T + 1, ds))
        offset_path[0] = S0
        for t in range(T):
            A_I[t + 1] = decay * A_I[t] + alpha * I[t]
            A_R[t + 1] = decay * A_R[t] + R_lag[t]
            offset_path[t + 1] = decay * offset_path[t]
        n_theta = ds * di + 1
        X = np.zeros((T * ds, n_theta))
        offset = np.zeros(T * ds)
        for t in range(1, T + 1):
            for d in range(ds):
                row = (t - 1) * ds + d
                X[row, d * di:(d + 1) * di] = A_I[t]
                X[row, -1] = A_R[t]
                offset[row] = offset_path[t, d]
        return offset, X

    def _solve_given_alpha(self, S_obs, I, R_lag, alpha, W_fixed=None):
        """Least-squares W and β for a fixed α. Returns (rmse, W, β)."""
        ds, di = self.dim_s, self.dim_i
        y = S_obs[1:].reshape(-1)
        offset, X = self._design(S_obs[0], I, R_lag, alpha)
        if W_fixed is None:
            theta, *_ = np.linalg.lstsq(X, y - offset, rcond=None)
            W = theta[:-1].reshape(ds, di)
            beta = theta[-1]
        else:
            W = np.asarray(W_fixed, dtype=float)
            fixed_part = X[:, :-1] @ W.reshape(-1)
            x_b = X[:, -1]
            denom = x_b @ x_b
            beta = 0.0 if denom == 0 else x_b @ (y - offset - fixed_part) / denom
        pred = offset + X[:, :-1] @ W.reshape(-1) + X[:, -1] * beta
        rmse = np.sqrt(np.mean((y - pred) ** 2))
        return rmse, W, beta

    # ------------------------------------------------------------------
    # Estimation
    # ------------------------------------------------------------------

    def fit(self, S_obs, I_series, SRM_series, W=None, n_grid=201):
        """
        Estimate α, β (and W unless given) by minimizing the RMSE of the
        simulated trajectory.

        Parameters
        ----------
        S_obs      : np.ndarray [T+1 x dim_s] — observed states, S_obs[0] = S(0)
        I_series   : np.ndarray [T x dim_i]
        SRM_series : np.ndarray [T]
        W          : optional np.ndarray [dim_s x dim_i] — fixed projection
        n_grid     : number of α grid points before refinement

        Returns
        -------
        dict with alpha, beta, W, rmse, r2_per_dim, S_simulated, converged
        """
        S_obs = np.asarray(S_obs, dtype=float)
        I = np.asarray(I_series, dtype=float)
        if S_obs.shape != (len(I) + 1, self.dim_s):
            raise ValueError(
                f"S_obs must have shape (T+1, {self.dim_s}); got {S_obs.shape} "
                f"with T = {len(I)}")
        if I.shape[1] != self.dim_i:
            raise ValueError(f"I_series must have {self.dim_i} columns; got {I.shape[1]}")
        R_lag = self._lagged_srm(SRM_series)

        def obj(a):
            return self._solve_given_alpha(S_obs, I, R_lag, a, W)[0]

        grid = np.linspace(0.0, 1.0, n_grid)
        vals = np.array([obj(a) for a in grid])
        k = int(np.argmin(vals))
        lo, hi = grid[max(k - 1, 0)], grid[min(k + 1, n_grid - 1)]
        if hi > lo:
            ref = minimize_scalar(obj, bounds=(lo, hi), method='bounded',
                                  options={'xatol': 1e-6})
            alpha = ref.x if ref.fun <= vals[k] else grid[k]
            converged = bool(ref.success)
        else:
            alpha, converged = grid[k], True

        rmse, W_hat, beta = self._solve_given_alpha(S_obs, I, R_lag, alpha, W)
        S_sim = self.simulate(S_obs[0], I, SRM_series, alpha, beta, W_hat)

        def r2(obs, sim):
            ss_tot = np.sum((obs - obs.mean()) ** 2)
            return 1 - np.sum((obs - sim) ** 2) / ss_tot if ss_tot > 0 else 0.0

        r2_per_dim = [r2(S_obs[1:, d], S_sim[1:, d]) for d in range(self.dim_s)]

        self.alpha, self.beta, self.W = alpha, beta, W_hat
        self.fitted = True
        self.results_ = {
            'alpha': float(alpha),
            'beta': float(beta),
            'W': W_hat,
            'W_estimated': W is None,
            'rmse': float(rmse),
            'r2_per_dim': r2_per_dim,
            'S_simulated': S_sim,
            'n_periods': len(I),
            'n_params': (self.dim_s * self.dim_i if W is None else 0) + 2,
            'converged': converged,
        }
        return self.results_

    def bootstrap_ci(self, S_obs, I_series, SRM_series, n_boot=200,
                     ci=0.95, seed=42, W=None):
        """
        Bootstrap confidence intervals for α and β by residual resampling
        around the fitted trajectory (same scheme as cmg_component.py).
        """
        rng = np.random.default_rng(seed)
        S_obs = np.asarray(S_obs, dtype=float)
        res0 = self.fit(S_obs, I_series, SRM_series, W=W)
        S_sim = res0['S_simulated']
        resid = S_obs[1:] - S_sim[1:]
        saved = dict(self.results_)
        saved_params = (self.alpha, self.beta, self.W)

        alphas, betas = [], []
        for _ in range(n_boot):
            idx = rng.integers(0, len(resid), len(resid))
            S_pseudo = np.vstack([S_obs[0], S_sim[1:] + resid[idx]])
            try:
                r = self.fit(S_pseudo, I_series, SRM_series, W=W, n_grid=101)
                alphas.append(r['alpha'])
                betas.append(r['beta'])
            except Exception:
                continue

        # restore the fit on the real data
        self.results_ = saved
        self.alpha, self.beta, self.W = saved_params
        self.fitted = True

        lo, hi = (1 - ci) / 2, 1 - (1 - ci) / 2
        return {
            'alpha_ci': (float(np.quantile(alphas, lo)), float(np.quantile(alphas, hi))),
            'beta_ci': (float(np.quantile(betas, lo)), float(np.quantile(betas, hi))),
            'n_boot_success': len(alphas),
        }

    def print_summary(self, label="MC"):
        if not self.fitted:
            print("Model not yet fitted.")
            return
        r = self.results_
        print(f"\n    {'='*56}")
        print(f"    MC Results — {label}  (reconstructed module, v2.0)")
        print(f"    {'='*56}")
        print(f"      alpha (recalibration rate) : {r['alpha']:.4f}")
        print(f"      beta  (SRM feedback)       : {r['beta']:.4f}")
        print(f"      RMSE                       : {r['rmse']:.4f}")
        for d, v in enumerate(r['r2_per_dim']):
            print(f"      R² dim{d}                    : {v:.3f}")
        print(f"      W estimated                : {r['W_estimated']}"
              f"  ({r['n_params']} parameters, {self.dim_s * r['n_periods']} observations)")
        print(f"    {'='*56}")


# =============================================================================
# SYNTHETIC DATA AND PARAMETER RECOVERY
# =============================================================================

def generate_synthetic_mc(T=40, alpha=0.35, beta=0.04, noise_sd=0.01, seed=42,
                          dim_s=2, dim_i=3):
    """Generate synthetic MC data with known α, β and W."""
    rng = np.random.default_rng(seed)
    W = rng.uniform(0.1, 0.5, (dim_s, dim_i))
    I = np.clip(rng.normal(0.45, 0.12, (T, dim_i)), 0, 1)
    SRM = np.clip(rng.normal(0.05, 0.02, T), 0.005, 0.3)
    mc = MetapoliticalCalibration(dim_s, dim_i)
    S_true = mc.simulate(rng.uniform(0.2, 0.4, dim_s), I, SRM, alpha, beta, W)
    S_obs = S_true + np.vstack([np.zeros(dim_s), rng.normal(0, noise_sd, (T, dim_s))])
    return {'S_obs': S_obs, 'I_series': I, 'SRM_series': SRM,
            'true_alpha': alpha, 'true_beta': beta, 'true_W': W}


def parameter_recovery(T=12, n_rep=200, alpha=0.35, beta=0.04, noise_sd=0.01,
                       W_known=False, seed=0):
    """
    Fit MC on n_rep synthetic datasets and report bias and spread of
    the recovered α and β.
    """
    alphas, betas = [], []
    for r in range(n_rep):
        d = generate_synthetic_mc(T=T, alpha=alpha, beta=beta,
                                  noise_sd=noise_sd, seed=seed + r)
        mc = MetapoliticalCalibration()
        res = mc.fit(d['S_obs'], d['I_series'], d['SRM_series'],
                     W=d['true_W'] if W_known else None, n_grid=101)
        alphas.append(res['alpha'])
        betas.append(res['beta'])
    alphas, betas = np.array(alphas), np.array(betas)
    return {
        'T': T, 'W_known': W_known,
        'alpha_median': float(np.median(alphas)),
        'alpha_90': (float(np.quantile(alphas, 0.05)), float(np.quantile(alphas, 0.95))),
        'beta_median': float(np.median(betas)),
        'beta_90': (float(np.quantile(betas, 0.05)), float(np.quantile(betas, 0.95))),
        'beta_sign_correct': float(np.mean(np.sign(betas) == np.sign(beta))),
    }


if __name__ == '__main__':
    print("MC parameter recovery (true α = 0.35, β = 0.04, noise sd = 0.01)")
    for T in (12, 40):
        for known in (False, True):
            r = parameter_recovery(T=T, W_known=known)
            print(f"  T={T:>2}  W {'known    ' if known else 'estimated'}  "
                  f"α median {r['alpha_median']:.3f} [90%: {r['alpha_90'][0]:.3f}, {r['alpha_90'][1]:.3f}]  "
                  f"β median {r['beta_median']:+.3f} [90%: {r['beta_90'][0]:+.3f}, {r['beta_90'][1]:+.3f}]  "
                  f"sign of β correct {r['beta_sign_correct']:.0%}")
