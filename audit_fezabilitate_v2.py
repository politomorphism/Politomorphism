#!/usr/bin/env python3
"""
Audit de fezabilitate v2: mai multe cazuri dintr-un JSON, aceleasi reguli.

Ce verifica scriptul: criteriile B (fereastra, N_pre/N_post, baza) si C.2
(potrivire pe expunere), plus puterea (MDE) prin simulare vectorizata.
Ce NU verifica: A, C.1, C.3, D, E, F (declaratii / verificari manuale).

Pageviews sunt folosite doar pentru numaratoare si ca stand-in de varianta
pentru X. NU sunt C(t). phi nu se estimeaza: se scaneaza.

Rulare:
  pip install numpy pandas requests
  python audit_fezabilitate_v2.py --hash-only                # manifest, inainte de orice date
  python audit_fezabilitate_v2.py --synthetic --nsim 200     # test local
  python audit_fezabilitate_v2.py --nsim 500                 # date reale Wikimedia
  python audit_fezabilitate_v2.py --select                   # dupa D/E: alege cazul B
"""
import argparse, hashlib, json, os, sys, urllib.parse
import numpy as np
import pandas as pd

# ------------- conventii INGHETATE (aliniate cu criterii_caz_B.md) -------------
TRANSITION_DAYS = 3
BASELINE_WEEKS = 52
BASELINE_GAP_DAYS = 90        # baza se termina cu 90 de zile inainte de act
MIN_PRE_DAYS = 182            # 26 saptamani
MIN_POST_DAYS = 182
MATCH_FACTOR = 3.0            # C.2: raportul medianelor pre-act in [1/3, 3]
MIN_CONTROLS = 2
MDE_MAX = 0.50                # unitati sigma per sd(X)
POWER_TARGET = 0.80
PHI_GRID = [0.0, 0.3, 0.6]
DELTAS = [round(d, 2) for d in np.arange(0.05, 1.01, 0.05)]
NSIM_DEFAULT = 500
SEED = 20261011
MAX_MISSING_BASELINE = 0.20   # >20% zile lipsa in baza => simbol neevaluabil


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def write_manifest(files, out="results/manifest.txt"):
    os.makedirs("results", exist_ok=True)
    lines = [f"{sha256(p)}  {p}" for p in files if os.path.exists(p)]
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("MANIFEST (inregistreaza aceste hash-uri inainte de orice serie SRM/C):")
    print("\n".join(lines))


def fetch_daily(title, start, end, project):
    import requests
    t = urllib.parse.quote(title, safe="")
    url = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
           f"{project}/all-access/user/{t}/daily/{start.strftime('%Y%m%d')}00/{end.strftime('%Y%m%d')}00")
    r = requests.get(url, headers={"User-Agent": "politomorphism-audit/0.2 (research)"}, timeout=60)
    r.raise_for_status()
    s = pd.Series({pd.to_datetime(i["timestamp"][:8]): i["views"] for i in r.json()["items"]})
    return s.asfreq("D")


def synthetic_series(start, end, act, exposure_start, seed):
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start, end)
    t = (idx - act).days.values
    te = (idx - exposure_start).days.values
    base = rng.poisson(40, len(idx)).astype(float)
    shock = 3000 * np.exp(-np.clip(te, 0, None) / 40.0) * (te >= 0)
    post = 400 * np.exp(-np.clip(t, 0, None) / 120.0) * (t >= 0)
    return pd.Series(base + shock + post, index=idx)


def hac_contrast_var(X, R, lag):
    """Varianta lui (b2 - b1) cu HAC Newey-West, vectorizat peste simulari."""
    m, n = R.shape
    xe = R[:, :, None] * X[None, :, :]
    S = np.einsum("mnk,mnl->mkl", xe, xe) / n
    for l in range(1, lag + 1):
        w = 1 - l / (lag + 1)
        G = np.einsum("mnk,mnl->mkl", xe[:, l:], xe[:, :-l]) / n
        S += w * (G + G.transpose(0, 2, 1))
    A = np.linalg.inv(X.T @ X / n)
    V = A @ S @ A / n
    return V[:, 1, 1] + V[:, 2, 2] - 2 * V[:, 1, 2]


def power_curve(x, post, phi, nsim, rng, lag=7):
    x = (x - x.mean()) / x.std()
    n = len(x)
    X = np.column_stack([np.ones(n), x * (1 - post), x * post])
    P = np.linalg.pinv(X)                         # (3, n)
    out = {}
    for d in DELTAS:
        e = np.empty((nsim, n))
        e[:, 0] = rng.normal(size=nsim)
        innov = rng.normal(size=(nsim, n)) * np.sqrt(1 - phi ** 2)
        for i in range(1, n):
            e[:, i] = phi * e[:, i - 1] + innov[:, i]
        y = d * x * post + e
        B = y @ P.T                               # (nsim, 3)
        R = y - B @ X.T
        var = hac_contrast_var(X, R, lag)
        t = (B[:, 2] - B[:, 1]) / np.sqrt(np.maximum(var, 1e-12))
        out[d] = float(np.mean(np.abs(t) > 1.96))
    return out


def mde(pw):
    for d in sorted(pw):
        if pw[d] >= POWER_TARGET:
            return d
    return float("inf")


def symbol_windows(s, act, exposure_start, end):
    base_end = act - pd.Timedelta(days=BASELINE_GAP_DAYS)
    base = s[base_end - pd.Timedelta(weeks=BASELINE_WEEKS):base_end]
    miss_frac = float(base.isna().mean()) if len(base) else 1.0
    med = base.median()
    out = dict(base_missing=miss_frac, base_median=med)
    if not np.isfinite(med) or miss_frac > MAX_MISSING_BASELINE:
        out["ok_base"] = False
        return out
    out["ok_base"] = True
    tr = pd.Timedelta(days=TRANSITION_DAYS)
    pre_raw = s[exposure_start:act - tr - pd.Timedelta(days=1)]
    post_raw = s[act + tr + pd.Timedelta(days=1):end]
    out["pre_raw"], out["post_raw"] = pre_raw, post_raw
    out["n_pre"], out["n_post"] = int(pre_raw.notna().sum()), int(post_raw.notna().sum())
    out["pre_median_raw"] = float(pre_raw.median()) if out["n_pre"] else np.nan
    return out


def run_case(case, end, nsim, rng, synthetic):
    act = pd.Timestamp(case["act_date"])
    exp0 = pd.Timestamp(case["exposure_start"])
    fetch_start = act - pd.Timedelta(days=BASELINE_GAP_DAYS) - pd.Timedelta(weeks=BASELINE_WEEKS)
    syms = [("excl", case["excluded"])] + [("ctrl", c) for c in case.get("controls", [])]
    proj = case.get("project", "en.wikipedia")
    rows, reasons = [], []
    info = {}
    for kind, sym in syms:
        try:
            if synthetic:
                s = synthetic_series(fetch_start, end, act, exp0, SEED + sum(map(ord, sym["name"])))
            else:
                s = fetch_daily(sym["title"], fetch_start, end, proj)
        except Exception as ex:
            reasons.append(f"{sym['name']}: date indisponibile ({ex})")
            continue
        w = symbol_windows(s, act, exp0, end)
        w["kind"], w["name"], w["series"] = kind, sym["name"], s
        info[sym["name"]] = w

    excl = info.get(case["excluded"]["name"])
    # A.4 declarat
    if case.get("prior_act_in_26w", None) is not False:
        reasons.append("A.4: prior_act_in_26w nu este declarat explicit false")
    if not case.get("exposure_source") or not case.get("source"):
        reasons.append("lipsesc 'exposure_source' si/sau 'source' (fapte de calendar fara sursa)")
    if excl is None or not excl.get("ok_base"):
        reasons.append("simbolul exclus: baza de normalizare lipsa/insuficienta")
    n_ctrl_ok = 0
    if excl is not None and excl.get("ok_base"):
        if excl["n_pre"] < MIN_PRE_DAYS:
            reasons.append(f"B.1: N_pre={excl['n_pre']} < {MIN_PRE_DAYS}")
        if excl["n_post"] < MIN_POST_DAYS:
            reasons.append(f"B.1: N_post={excl['n_post']} < {MIN_POST_DAYS}")
        for nm, w in info.items():
            if w["kind"] != "ctrl" or not w.get("ok_base"):
                continue
            if excl["n_pre"] and w["n_pre"] and excl["pre_median_raw"] > 0 and w["pre_median_raw"] > 0:
                ratio = excl["pre_median_raw"] / w["pre_median_raw"]
                if 1 / MATCH_FACTOR <= ratio <= MATCH_FACTOR:
                    n_ctrl_ok += 1
                else:
                    reasons.append(f"C.2: {nm} raport expunere pre-act={ratio:.2f} (in afara [1/3,3])")
        if n_ctrl_ok < MIN_CONTROLS:
            reasons.append(f"C: controale potrivite={n_ctrl_ok} < {MIN_CONTROLS}")

    mde_worst = float("nan")
    if excl is not None and excl.get("ok_base") and excl["n_pre"] >= 8 and excl["n_post"] >= 8:
        win = pd.concat([excl["pre_raw"], excl["post_raw"]]).dropna()
        x = np.log((win + 1) / (excl["base_median"] + 1)).values
        post = (win.index > act).astype(float)
        mdes = [mde(power_curve(x, post, phi, nsim, rng)) for phi in PHI_GRID]
        mde_worst = max(mdes)
        if not np.isfinite(mde_worst) or mde_worst > MDE_MAX:
            reasons.append(f"MDE_worst={mde_worst} > {MDE_MAX}")
    else:
        mdes = [float("nan")] * len(PHI_GRID)

    passed = len(reasons) == 0
    return dict(id=case["id"], country=case.get("country", ""), act_date=case["act_date"],
                n_pre=excl["n_pre"] if excl and excl.get("ok_base") else None,
                n_post=excl["n_post"] if excl and excl.get("ok_base") else None,
                controls_matched=n_ctrl_ok, mde_by_phi=mdes, mde_worst=mde_worst,
                platform_removal=case.get("platform_removal"),
                de_status=case.get("de_status", "pending"),
                abc_pass=passed, reasons=" | ".join(reasons))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default="cases.json")
    ap.add_argument("--criteria", default="criterii_caz_B.md")
    ap.add_argument("--end", default="2026-10-10")
    ap.add_argument("--nsim", type=int, default=NSIM_DEFAULT)
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--hash-only", action="store_true")
    ap.add_argument("--select", action="store_true")
    a = ap.parse_args()

    write_manifest([a.cases, a.criteria, os.path.abspath(__file__)])
    if a.hash_only:
        return

    cases = [c for c in json.load(open(a.cases, encoding="utf-8"))["cases"] if not c.get("template")]
    end = pd.Timestamp(a.end)
    rng = np.random.default_rng(SEED)
    results = []
    print()
    for c in cases:
        r = run_case(c, end, a.nsim, rng, a.synthetic)
        results.append(r)
        mdes = ",".join("nan" if not np.isfinite(m) else f"{m:.2f}" for m in r["mde_by_phi"])
        print(f"{r['id']:<10} {r['country']:<12} act={r['act_date']}  N_pre={r['n_pre']}  N_post={r['n_post']}  "
              f"controale={r['controls_matched']}  MDE(phi={PHI_GRID})={mdes}")
        print(f"   -> {'A-C TRECUT (D/E pe mana)' if r['abc_pass'] else 'RESPINS: ' + r['reasons']}")

    os.makedirs("results", exist_ok=True)
    df = pd.DataFrame(results)
    df["mde_by_phi"] = df["mde_by_phi"].astype(str)
    df.to_csv("results/audit_results.csv", index=False)
    print("\nScris: results/audit_results.csv, results/manifest.txt")

    if a.select:
        ok = [r for r in results if r["abc_pass"] and r["de_status"] == "pass"]
        if not ok:
            print("SELECTIE: niciun caz cu A-C trecut si de_status='pass'. Nu se alege nimic.")
        elif len(ok) == 1:
            print(f"SELECTIE: {ok[0]['id']} (singurul caz eligibil)")
        else:
            oldest = sorted(ok, key=lambda r: r["act_date"])[0]
            print(f"SELECTIE (cea mai veche data a actului): {oldest['id']} din {len(ok)} eligibile")
    else:
        print("Selectia (G.3) se aplica doar dupa D/E, cu --select si de_status='pass'.")


if __name__ == "__main__":
    main()
