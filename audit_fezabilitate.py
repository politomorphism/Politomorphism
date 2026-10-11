#!/usr/bin/env python3
"""
Audit de fezabilitate si putere pentru testul delta (Symbolic Exile).

CE FACE
  1. Numara N_pre / N_post la rezolutie zilnica si saptamanala, cu fereastra
     de tranzitie exclusa, pentru fiecare simbol (exclus vs control).
  2. Calculeaza MDE prin simulare (erori AR(1), SE de tip Newey-West)
     pentru delta = beta_post - beta_pre.
  3. Aplica regula de inchidere A/B scrisa in avans (pragurile de mai jos
     sunt conventii, inghetate aici).

CE NU FACE
  - Nu foloseste pageviews ca C(t). Pageviews intra DOAR ca stand-in de
    varianta pentru expunere (X) si pentru numaratoare. C_A/C_B si SRM
    zilnic raman de furnizat.
  - Phi si sigma NU se estimeaza din date: se scaneaza pe grila fixa,
    deoarece autocorelatia lui dC nu se poate masura fara C.

RULARE
  pip install numpy pandas requests
  python audit_fezabilitate.py --synthetic        # test local, fara retea
  python audit_fezabilitate.py                    # date reale Wikimedia
Titlurile articolelor se verifica manual (redirect/titlu gresit = 404).
"""
import argparse, sys, urllib.parse
import numpy as np
import pandas as pd

# ---------------- conventii INGHETATE (editeaza inainte de rulare, nu dupa) ---
ORIGIN_DEFAULT = "2024-12-06"       # anularea CCR (primul act); BEC 2025-03-09 = robustete
FIRST_ROUND = "2024-11-24"          # inceputul regimului de expunere
END_DEFAULT = "2026-10-10"          # ultima zi completa la data scrierii
TRANSITION_DAYS = 3                 # +/- zile excluse in jurul actului
BASELINE_WEEKS = 52                 # mediana pre-eveniment, ca in lucrarea Wikipedia
BASELINE_END = "2024-10-31"         # inainte de socul electoral, fixata, nu din date
MIN_N_PRE_DAILY = 60                # prag minim zile pre-act in regimul de expunere
MIN_N_POST_DAILY = 60
MDE_MAX = 0.50                      # MDE maxim acceptat, in unitati sigma per sd(X)
POWER_TARGET = 0.80
PHI_GRID = [0.0, 0.3, 0.6]          # autocorelatie presupusa a erorilor (scanata)
NSIM = 2000
SEED = 20261011

SYMBOLS = {  # nume afisat : titlu articol ro.wikipedia (VERIFICA)
    "Georgescu (exclus)": "Călin_Georgescu",
    "AUR (control)": "Alianța_pentru_Unirea_Românilor",
    "Simion (control)": "George_Simion",
    "Lasconi (control)": "Elena_Lasconi",
}


def fetch_daily(title, start, end, project="ro.wikipedia"):
    import requests
    t = urllib.parse.quote(title, safe="")
    url = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
           f"{project}/all-access/user/{t}/daily/{start.replace('-', '')}00/{end.replace('-', '')}00")
    r = requests.get(url, headers={"User-Agent": "politomorphism-audit/0.1 (research)"}, timeout=60)
    r.raise_for_status()
    items = r.json()["items"]
    s = pd.Series({pd.to_datetime(i["timestamp"][:8]): i["views"] for i in items})
    return s.asfreq("D")  # zilele lipsa -> NaN (nu se imputa)


def synthetic_series(start, end, origin, seed):
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start, end)
    base = rng.poisson(40, len(idx)).astype(float)
    t = (idx - pd.Timestamp(origin)).days.values
    shock = 6000 * np.exp(-np.clip(t + 12, 0, None) / 6.0) * (t >= -12)
    resid = 150 * np.exp(-np.clip(t, 0, None) / 200.0) * (t >= 0)
    return pd.Series(base + shock + resid + rng.poisson(5, len(idx)), index=idx)


def newey_west_se(X, resid, lag):
    n, k = X.shape
    xe = X * resid[:, None]
    S = xe.T @ xe / n
    for l in range(1, lag + 1):
        w = 1 - l / (lag + 1)
        G = xe[l:].T @ xe[:-l] / n
        S += w * (G + G.T)
    XtXi = np.linalg.inv(X.T @ X / n)
    return np.sqrt(np.diag(XtXi @ S @ XtXi / n))


def simulate_power(x, post, phi, deltas, lag, nsim, rng):
    """y = alpha + 0*x*(1-P) + delta*x*P + e,  e ~ AR(1)(phi), sd_e = 1.
    x standardizat (sd=1) in fereastra: delta in unitati sigma per sd(X).
    beta_pre = 0 e inofensiv: puterea pentru delta nu depinde de beta_pre."""
    x = (x - x.mean()) / x.std()
    n = len(x)
    X = np.column_stack([np.ones(n), x * (1 - post), x * post])
    XtXi_Xt = np.linalg.pinv(X)
    out = {}
    for d in deltas:
        rej = 0
        for _ in range(nsim):
            e = np.empty(n)
            e[0] = rng.normal()
            innov = rng.normal(size=n) * np.sqrt(1 - phi ** 2)
            for i in range(1, n):
                e[i] = phi * e[i - 1] + innov[i]
            y = d * x * post + e
            b = XtXi_Xt @ y
            se = newey_west_se(X, y - X @ b, lag)
            if abs((b[2] - b[1]) / np.sqrt(se[1] ** 2 + se[2] ** 2)) > 1.96:
                rej += 1
        out[d] = rej / nsim
    return out


def mde_from_power(power_by_delta, target):
    for d in sorted(power_by_delta):
        if power_by_delta[d] >= target:
            return d
    return np.inf


def audit_symbol(name, s, origin, first_round, end, trans, resolution):
    origin, first_round = pd.Timestamp(origin), pd.Timestamp(first_round)
    base = s[pd.Timestamp(BASELINE_END) - pd.Timedelta(weeks=BASELINE_WEEKS):pd.Timestamp(BASELINE_END)]
    med = base.median()
    x_all = np.log((s + 1) / (med + 1))
    win = x_all[first_round:pd.Timestamp(end)].copy()
    win = win[(win.index < origin - pd.Timedelta(days=trans)) | (win.index > origin + pd.Timedelta(days=trans))]
    missing = int(win.isna().sum())
    win = win.dropna()
    if resolution == "weekly":
        win = win.resample("W").mean().dropna()
        lag = 2
    else:
        lag = 7
    post = (win.index > origin).astype(float)
    n_pre, n_post = int((1 - post).sum()), int(post.sum())
    return dict(name=name, win=win, post=post, n_pre=n_pre, n_post=n_post,
                missing=missing, baseline_median=med, lag=lag)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--origin", default=ORIGIN_DEFAULT)
    ap.add_argument("--first-round", default=FIRST_ROUND)
    ap.add_argument("--end", default=END_DEFAULT)
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--nsim", type=int, default=NSIM)
    a = ap.parse_args()
    rng = np.random.default_rng(SEED)

    fetch_start = (pd.Timestamp(BASELINE_END) - pd.Timedelta(weeks=BASELINE_WEEKS)).strftime("%Y-%m-%d")
    data = {}
    for nm, title in SYMBOLS.items():
        if a.synthetic:
            data[nm] = synthetic_series(fetch_start, a.end, a.origin, SEED + len(data))
        else:
            try:
                data[nm] = fetch_daily(title, fetch_start, a.end)
            except Exception as ex:
                print(f"[LIPSA] {nm} ({title}): {ex}", file=sys.stderr)

    deltas = [round(d, 2) for d in np.arange(0.05, 1.01, 0.05)]
    print(f"\nORIGINE={a.origin}  prima tura={a.first_round}  sfarsit={a.end}  "
          f"tranzitie=±{TRANSITION_DAYS} zile  NSIM={a.nsim}")
    print("Delta in unitati sigma per sd(X). Phi scanat, NU estimat.\n")

    verdicts = []
    for nm, s in data.items():
        for res in ("daily", "weekly"):
            r = audit_symbol(nm, s, a.origin, a.first_round, a.end, TRANSITION_DAYS, res)
            line = f"{nm:<22} {res:<7} N_pre={r['n_pre']:>4} N_post={r['n_post']:>4} lipsa={r['missing']}"
            if min(r["n_pre"], r["n_post"]) < 8:
                print(line + "  -> prea putine puncte, simulare omisa")
                verdicts.append((nm, res, np.inf, False))
                continue
            mdes = {}
            for phi in PHI_GRID:
                pw = simulate_power(r["win"].values, r["post"], phi, deltas,
                                    r["lag"], a.nsim if res == "daily" else a.nsim, rng)
                mdes[phi] = mde_from_power(pw, POWER_TARGET)
            worst = max(mdes.values())
            ok_n = (res == "daily" and r["n_pre"] >= MIN_N_PRE_DAILY and r["n_post"] >= MIN_N_POST_DAILY)
            ok = ok_n and worst <= MDE_MAX
            verdicts.append((nm, res, worst, ok))
            print(line + "  MDE(phi=" + ",".join(f"{p}" for p in PHI_GRID) + ")="
                  + ",".join("inf" if np.isinf(v) else f"{v:.2f}" for v in mdes.values()))

    print("\nREGULA DE INCHIDERE (conventii inghetate sus):")
    print(f"  intra daca daily: N_pre>={MIN_N_PRE_DAILY}, N_post>={MIN_N_POST_DAILY}, "
          f"MDE(cel mai rau phi)<={MDE_MAX}")
    for nm, res, w, ok in verdicts:
        print(f"  {nm:<22} {res:<7} MDE_worst={'inf' if np.isinf(w) else f'{w:.2f}'}  "
              f"{'TESTABIL (conditionat de C si beta_pre)' if ok else 'NETESTABIL la aceasta rezolutie'}")
    print("\nNOTA: 'testabil' aici inseamna doar numaratoare + putere. Raman necesare: "
          "C_A/C_B din corpus disjunct, beta_pre distinct de 0 pe fereastra pre-act, "
          "si control cu simbol neexclus (diferenta de delta).")


if __name__ == "__main__":
    main()
