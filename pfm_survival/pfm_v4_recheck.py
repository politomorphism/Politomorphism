"""
PFM-Survival v4 - recalculare verificata (re-check)
Autor analiza: verificare independenta a raportului training_report_v4.json

Ce face scriptul:
  1. Citeste training_data_extended.csv
  2. Scoate dublurile (Putin / Vladimir Putin, Modi / Narendra Modi)
  3. Calculeaza c-index prin LOOCV (leave-one-out) pentru mai multe modele,
     toate in acelasi fel: fiecare caz este prezis de un model care NU l-a vazut.
  4. Interval de incredere 95% prin bootstrap pe predictiile LOOCV
  5. Jackknife corect: c-index-ul LOOCV recalculat fara fiecare caz
  6. Scorul Brier integrat (IBS) LOOCV pentru fiecare model si pentru Kaplan-Meier
  7. Verifica ipoteza semnului inversat la Cox (0.258 vs 1 - 0.258)
  8. Salveaza tabelele in CSV si o figura PNG

Rulare:
  python pfm_v4_recheck.py training_data_extended.csv iesire_folder

Necesita: pandas, numpy, scikit-learn, scikit-survival, matplotlib
"""

import sys
import os
import json
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sksurv.util import Surv
from sksurv.linear_model import CoxPHSurvivalAnalysis
from sksurv.ensemble import RandomSurvivalForest
from sksurv.nonparametric import kaplan_meier_estimator
from sksurv.metrics import concordance_index_censored, integrated_brier_score

warnings.filterwarnings("ignore")

SEED = 42
N_BOOT = 2000
N_TREES = 500

DUPLICATE_SETS = {
    # varianta principala: pastram numele complete
    "principal": ["Putin", "Modi"],
    # varianta de sensibilitate: pastram numele scurte
    "sensibilitate": ["Vladimir Putin", "Narendra Modi"],
}


def load_data(path, drop_symbols):
    df = pd.read_csv(path)
    df = df[~df["symbol"].isin(drop_symbols)].reset_index(drop=True)
    df["event"] = df["is_censored"] == 0
    return df


def make_y(df):
    return Surv.from_arrays(event=df["event"].values, time=df["event_time_months"].values)


def cindex(df, risk):
    return concordance_index_censored(
        df["event"].values, df["event_time_months"].values, np.asarray(risk)
    )[0]


def fit_model(kind, X, y):
    if kind == "cox":
        m = CoxPHSurvivalAnalysis(alpha=0.1)
    else:
        m = RandomSurvivalForest(
            n_estimators=N_TREES, min_samples_split=4, min_samples_leaf=2,
            max_features="sqrt", random_state=SEED, n_jobs=-1,
        )
    m.fit(X, y)
    return m


def loocv(df, kind, features, times):
    """Returneaza: scor de risc LOOCV (mai mare = colaps mai rapid) si
    functii de supravietuire LOOCV evaluate la 'times'."""
    n = len(df)
    risk = np.zeros(n)
    surv = np.zeros((n, len(times)))
    for i in range(n):
        tr = df.drop(index=i)
        te = df.iloc[[i]]
        if kind == "km":
            t, s = kaplan_meier_estimator(tr["event"].values, tr["event_time_months"].values)
            surv[i] = np.interp(times, t, s, left=1.0, right=s[-1])
            risk[i] = 0.0
            continue
        if kind == "raw":
            # fara model: scorul de risc este direct minus valoarea indicatorului
            # (mai putina atentie retinuta => colaps mai rapid)
            risk[i] = -float(te[features[0]].iloc[0])
            surv[i] = np.nan
            continue
        m = fit_model(kind, tr[features].values, make_y(tr))
        risk[i] = m.predict(te[features].values)[0]
        fn = m.predict_survival_function(te[features].values)[0]
        surv[i] = np.clip(fn(np.clip(times, fn.x.min(), fn.x.max())), 0, 1)
    return risk, surv


def bootstrap_ci(df, risk, n_boot=N_BOOT, seed=SEED):
    rng = np.random.default_rng(seed)
    vals = []
    n = len(df)
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        sub = df.iloc[idx].reset_index(drop=True)
        if sub["event"].sum() < 2:
            continue
        try:
            vals.append(cindex(sub, risk[idx]))
        except Exception:
            continue
    return np.percentile(vals, [2.5, 97.5])


def jackknife(df, risk):
    full = cindex(df, risk)
    out = []
    for i in range(len(df)):
        keep = np.ones(len(df), bool)
        keep[i] = False
        sub = df[keep].reset_index(drop=True)
        c = cindex(sub, risk[keep])
        out.append({"symbol": df.loc[i, "symbol"], "cindex_fara": round(c, 4),
                    "delta": round(c - full, 4)})
    return pd.DataFrame(out)


def ibs(df, surv, times):
    y = make_y(df)
    return integrated_brier_score(y, y, surv, times)


def run(path, outdir, variant):
    df = load_data(path, DUPLICATE_SETS[variant])
    y = make_y(df)
    tmax = np.percentile(df["event_time_months"], 80)
    times = np.linspace(0.5, tmax, 25)

    specs = [
        ("ratio_4wk singur (fara model)", "raw", ["ratio_4wk"]),
        ("CDI singur (fara model)", "raw", ["CDI"]),
        ("decay_rate singur (fara model)", "raw", ["decay_rate_4wk"]),
        ("Cox: CDI", "cox", ["CDI"]),
        ("Cox: ratio + decay", "cox", ["ratio_4wk", "decay_rate_4wk"]),
        ("RSF: CDI (model v4 fara PE_ICI_gap)", "rsf", ["CDI"]),
        ("RSF: ratio + decay", "rsf", ["ratio_4wk", "decay_rate_4wk"]),
        ("Kaplan-Meier (fara indicatori)", "km", []),
    ]

    rows, jk_tables, km_surv = [], {}, None
    loo_store = {}
    for name, kind, feats in specs:
        risk, surv = loocv(df, kind, feats, times)
        if kind == "km":
            km_surv = surv
            rows.append({"model": name, "cindex_LOOCV": 0.5, "IC95_jos": np.nan,
                         "IC95_sus": np.nan, "IBS_LOOCV": round(ibs(df, surv, times), 4)})
            continue
        c = cindex(df, risk)
        lo, hi = bootstrap_ci(df, risk)
        row = {"model": name, "cindex_LOOCV": round(c, 4),
               "IC95_jos": round(lo, 4), "IC95_sus": round(hi, 4), "IBS_LOOCV": np.nan}
        if kind in ("cox", "rsf"):
            row["IBS_LOOCV"] = round(ibs(df, surv, times), 4)
        rows.append(row)
        loo_store[name] = risk
        if kind in ("rsf", "raw") and feats in (["CDI"], ["ratio_4wk"]):
            jk_tables[name] = jackknife(df, risk)

    res = pd.DataFrame(rows)
    km_ibs = res.loc[res["model"].str.startswith("Kaplan"), "IBS_LOOCV"].iloc[0]
    res["IBS_vs_KM_%"] = ((km_ibs - res["IBS_LOOCV"]) / km_ibs * 100).round(1)

    # verificare semn Cox: c-index cu scorul inversat
    cox_risk = loo_store["Cox: CDI"]
    sign_check = {
        "cox_cdi_cindex_corect": round(cindex(df, cox_risk), 4),
        "cox_cdi_cindex_semn_inversat": round(cindex(df, -cox_risk), 4),
        "raportat_in_v4": 0.258,
    }

    os.makedirs(outdir, exist_ok=True)
    res.to_csv(os.path.join(outdir, f"rezultate_{variant}.csv"), index=False)
    for k, t in jk_tables.items():
        safe = k.split(":")[0].split(" ")[0].replace("/", "_")
        t.to_csv(os.path.join(outdir, f"jackknife_{variant}_{safe}.csv"), index=False)
    with open(os.path.join(outdir, f"verificare_semn_cox_{variant}.json"), "w") as f:
        json.dump(sign_check, f, indent=2)

    if variant == "principal":
        plot(df, outdir)
    return df, res, jk_tables, sign_check


def plot(df, outdir):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    t, s = kaplan_meier_estimator(df["event"].values, df["event_time_months"].values)
    axes[0].step(t, s, where="post", color="#1f4e79", lw=2)
    axes[0].set_title("Kaplan-Meier: cate simboluri mai 'traiesc'")
    axes[0].set_xlabel("luni de la varf")
    axes[0].set_ylabel("proportie simboluri inca vii")
    axes[0].set_ylim(0, 1.05)
    axes[0].grid(alpha=0.3)

    ev = df["event"]
    axes[1].scatter(df.loc[ev, "ratio_4wk"], df.loc[ev, "event_time_months"],
                    color="#c0392b", label="colaps observat", zorder=3)
    if (~ev).any():
        axes[1].scatter(df.loc[~ev, "ratio_4wk"], df.loc[~ev, "event_time_months"],
                        facecolors="none", edgecolors="#c0392b", label="cenzurat", zorder=3)
    for _, r in df.iterrows():
        if r["event_time_months"] > 4 or r["ratio_4wk"] > 0.25:
            axes[1].annotate(r["symbol"], (r["ratio_4wk"], r["event_time_months"]),
                             fontsize=8, xytext=(4, 2), textcoords="offset points")
    axes[1].set_title("Atentia ramasa la 4 saptamani vs. timpul pana la colaps")
    axes[1].set_xlabel("ratio_4wk (atentie la 4 sapt. / atentie la varf)")
    axes[1].set_ylabel("luni pana la colaps")
    axes[1].legend()
    axes[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "figura_pfm_v4_recheck.png"), dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "training_data_extended.csv"
    out = sys.argv[2] if len(sys.argv) > 2 else "pfm_recheck_output"
    for v in ("principal", "sensibilitate"):
        df, res, jk, sc = run(csv_path, out, v)
        print(f"\n=== Varianta {v}: n={len(df)}, colapsuri={int(df['event'].sum())} ===")
        print(res.to_string(index=False))
        print("Verificare semn Cox:", sc)
        for k, t in jk.items():
            print(f"Jackknife {k}: min={t['cindex_fara'].min()}, max={t['cindex_fara'].max()}, "
                  f"influenta maxima={t['delta'].abs().max()} ({t.loc[t['delta'].abs().idxmax(), 'symbol']})")
