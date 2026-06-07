#!/usr/bin/env python3
"""
RULEAZA_ISC.py
==============
Script automat pentru testarea ISC — Symbolic Coherence Index
Politomorphism Engine | Component IV | Version 4.0

Instrucțiuni:
    python RULEAZA_ISC.py

Autor: Serban Gabriel Florin
ORCID: 0009-0000-2266-3356
OSF: https://doi.org/10.17605/OSF.IO/HYDNZ
"""

import os
import sys
import json
import math
import csv
import logging
from pathlib import Path
from collections import Counter

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

BASE = Path(__file__).parent / "isc_test"

# ─────────────────────────────────────────────
# SETUP — foldere si date de test
# ─────────────────────────────────────────────

def setup():
    print("\n" + "="*60)
    print("  ISC — Symbolic Coherence Index")
    print("  Politomorphism Engine | Component IV | v4.0")
    print("  Serban Gabriel Florin | ORCID: 0009-0000-2266-3356")
    print("="*60)
    print("\n[1/5] Creare structura de foldere si date de test...")

    for folder in [
        BASE / "data" / "psd_texts" / "2016Q1",
        BASE / "data" / "psd_texts" / "2023Q3",
        BASE / "results",
    ]:
        folder.mkdir(parents=True, exist_ok=True)

    # 2016Q1 — mesaj concentrat (CMP ridicat asteptat)
    docs_2016 = [
        "Pensiile romanilor trebuie sa creasca substantial. PSD va majora pensiile si salariile pentru ca Romania merita cetateni respectati si protejati social prin politici clare.",
        "Cresterea pensiilor si protectia sociala sunt prioritatea absoluta a PSD. Vom apara drepturile sociale ale romanilor impotriva oricaror atacuri la adresa statului social.",
        "Majorarea salariului minim este angajamentul nostru fata de muncitorii romani. PSD respecta clasa muncitoare si va continua sa creasca veniturile tuturor cetatenilor.",
        "PSD sustine familia si valorile traditionale romanesti. Vom apara identitatea nationala si vom creste alocatiile pentru familiile nevoiase din toata tara.",
        "Romania trebuie sa isi apere suveranitatea nationala. PSD va proteja interesele romanilor impotriva presiunilor externe care ameninta identitatea si valorile noastre.",
        "Investitiile sociale ale guvernului PSD au crescut veniturile romanilor. Vom continua sa majoram pensiile si sa protejam muncitorii cu salarii mai mari.",
        "Statul social roman trebuie consolidat. PSD garanteaza ca pensiile si alocatiile vor fi platite la timp si vor creste in fiecare an.",
    ]

    # 2023Q3 — mesaj dispersat (CMP scazut asteptat)
    docs_2023 = [
        "Romania trebuie sa fie pro-europeana si sa respecte angajamentele fata de Bruxelles. Vom negocia cu partenerii europeni dar vom apara si interesele nationale.",
        "Austeritatea impusa de deficitul bugetar ne obliga sa fim responsabili fiscal. Dar pensiile raman prioritate chiar daca trebuie sa taiem alte cheltuieli publice.",
        "Suveranismul romanesc este compatibil cu integrarea europeana. PSD nu este nici pro-rus nici anti-european ci doar pro-roman in toate negocierile internationale.",
        "Investitiile in infrastructura sunt esentiale dar si echilibrul bugetar conteaza. Vom construi autostrazi respectand criteriile de convergenta ale Uniunii Europene.",
        "Securitatea energetica si tranzitia verde sunt obiective care se pot combina daca avem o strategie nationala bazata pe resurse proprii si parteneriate diversificate.",
        "Reforma judiciara trebuie sa echilibreze independenta magistratilor cu responsabilitatea lor. Nu putem ignora nici standardele europene nici cerintele societatii civile.",
        "Politica externa a Romaniei trebuie sa fie echilibrata intre partenerii strategici din NATO si relatiile cu vecinii din est care raman importanti pentru stabilitate.",
    ]

    for i, text in enumerate(docs_2016, 1):
        (BASE / "data" / "psd_texts" / "2016Q1" / f"doc{i:03d}.txt").write_text(text, encoding="utf-8")
    for i, text in enumerate(docs_2023, 1):
        (BASE / "data" / "psd_texts" / "2023Q3" / f"doc{i:03d}.txt").write_text(text, encoding="utf-8")

    # Voturi CSV
    votes = [
        ["quarter","session_id","member_id","member_vote","official_position"],
        ["2016Q1","S001","M001","for","for"],
        ["2016Q1","S001","M002","for","for"],
        ["2016Q1","S001","M003","for","for"],
        ["2016Q1","S001","M004","for","for"],
        ["2016Q1","S001","M005","against","for"],
        ["2016Q1","S002","M001","against","against"],
        ["2016Q1","S002","M002","against","against"],
        ["2016Q1","S002","M003","against","against"],
        ["2016Q1","S002","M004","against","against"],
        ["2016Q1","S002","M005","against","against"],
        ["2023Q3","S101","M001","for","for"],
        ["2023Q3","S101","M002","against","for"],
        ["2023Q3","S101","M003","for","for"],
        ["2023Q3","S101","M004","abstain","for"],
        ["2023Q3","S101","M005","against","for"],
        ["2023Q3","S102","M001","for","unknown"],
        ["2023Q3","S102","M002","against","unknown"],
        ["2023Q3","S102","M003","for","unknown"],
        ["2023Q3","S102","M004","for","unknown"],
        ["2023Q3","S102","M005","against","unknown"],
    ]
    with open(BASE / "data" / "psd_votes.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(votes)

    # Structura CSV
    struct = [
        ["quarter","event_type","member_id","total_members"],
        ["2016Q1","","","110"],
        ["2023Q3","expulsion","M_X01","108"],
        ["2023Q3","resignation","M_X02","108"],
        ["2023Q3","resignation","M_X03","108"],
    ]
    with open(BASE / "data" / "psd_struct.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(struct)

    print("    OK — foldere, documente, voturi, structura create.")

    return {
        "actor": "PSD",
        "country": "Romania",
        "corpus_dir": BASE / "data" / "psd_texts",
        "votes_file": BASE / "data" / "psd_votes.csv",
        "struct_file": BASE / "data" / "psd_struct.csv",
        "weight_sensitivity": [0.30, 0.50, 0.70],
    }


# ─────────────────────────────────────────────
# CMP — metoda keyword (robusta, fara dependente externe)
# ─────────────────────────────────────────────

def compute_cmp_keywords(texts):
    """
    CMP prin entropie Shannon pe categorii tematice de cuvinte cheie.
    Metoda robusta, fara dependente externe, replicabila manual.
    """
    categories = {
        "social_pensii":   ["pensii", "pensiile", "salarii", "salariu", "social", "protectie", "muncitori", "alocatii", "venituri"],
        "suveran_national":["suveranitate", "national", "nationala", "identitate", "traditie", "traditional", "romani", "romania", "popor"],
        "european_extern": ["european", "europeana", "bruxelles", "ue", "integrare", "parteneriat", "nato", "extern", "international"],
        "fiscal_bugetar":  ["buget", "deficit", "austeritate", "fiscal", "cheltuieli", "investitii", "infrastructura", "autostrazi"],
        "juridic_politic": ["reforma", "justitie", "judiciara", "magistrati", "lege", "politica", "guvern", "partid"],
    }

    counts = {cat: 0 for cat in categories}
    for text in texts:
        words = text.lower().split()
        for cat, keywords in categories.items():
            for word in words:
                if any(kw in word for kw in keywords):
                    counts[cat] += 1

    total = sum(counts.values())
    if total == 0:
        return {"cmp": 0.5, "method": "keyword", "n_topics": len(categories),
                "h": 0.0, "h_max": math.log(len(categories)),
                "stable": True, "ci_lower": 0.5, "ci_upper": 0.5,
                "topic_counts": counts}

    p = {cat: count/total for cat, count in counts.items() if count > 0}
    h = -sum(pk * math.log(pk) for pk in p.values())
    h_max = math.log(len(categories))
    cmp = round(max(0.0, min(1.0, 1.0 - h / h_max)), 4)

    return {
        "cmp": cmp,
        "method": "keyword_entropy",
        "n_topics": len(categories),
        "h": round(h, 4),
        "h_max": round(h_max, 4),
        "stable": True,
        "ci_lower": cmp,
        "ci_upper": cmp,
        "topic_counts": counts,
    }


def compute_cmp_bertopic(texts):
    """
    CMP prin BERTopic ensemble. Fallback la keyword daca esueaza.
    """
    try:
        import numpy as np
        from bertopic import BERTopic
        from sentence_transformers import SentenceTransformer

        embedding_model = SentenceTransformer("readerbench/RoBERT-base")
        successful = []

        for seed in range(3):
            np.random.seed(seed)
            model = BERTopic(
                embedding_model=embedding_model,
                language="multilingual",
                min_topic_size=2,
                nr_topics="auto",
                verbose=False,
                calculate_probabilities=False,
            )
            try:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    topics, _ = model.fit_transform(texts)
                valid = [t for t in topics if t != -1]
                if valid:
                    successful.append(valid)
            except Exception:
                continue

        if not successful:
            raise RuntimeError("BERTopic esuat pe toate cele 3 rulari")

        final = successful[-1]
        n_topics = max(2, len(set(final)))
        counts = Counter(final)
        total = sum(counts.values())
        p = {k: v/total for k, v in counts.items()}
        h = -sum(pk * math.log(pk) for pk in p.values() if pk > 0)
        h_max = math.log(n_topics)
        cmp = round(max(0.0, min(1.0, 1.0 - h / h_max)), 4)

        # Bootstrap
        rng = np.random.default_rng(42)
        boot = []
        for _ in range(50):
            sample = list(rng.choice(final, size=max(3, int(len(final)*0.8)), replace=False))
            sc = Counter(sample)
            st = sum(sc.values())
            sp = {k: v/st for k, v in sc.items()}
            sh = -sum(pk * math.log(pk) for pk in sp.values() if pk > 0)
            boot.append(max(0.0, min(1.0, 1.0 - sh / h_max)))

        ci_lo = round(float(np.percentile(boot, 2.5)), 4)
        ci_hi = round(float(np.percentile(boot, 97.5)), 4)

        return {
            "cmp": cmp, "method": "ensemble_bertopic",
            "n_topics": n_topics, "h": round(h,4), "h_max": round(h_max,4),
            "stable": (ci_hi - ci_lo) <= 0.10,
            "ci_lower": ci_lo, "ci_upper": ci_hi,
            "topic_counts": dict(counts),
        }

    except Exception as ex:
        print(f"    BERTopic indisponibil ({ex.__class__.__name__}). Folosesc metoda keyword.")
        return compute_cmp_keywords(texts)


# ─────────────────────────────────────────────
# CI — Coeziune interna
# ─────────────────────────────────────────────

def compute_ci_vote(votes_file, quarter):
    rows = []
    with open(votes_file, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["quarter"] == quarter:
                rows.append(row)

    if not rows:
        return {"ci_vote": float("nan"), "n_total": 0, "n_divergent": 0,
                "unknown_frac": float("nan"), "ambiguity_risk": False}

    known = [r for r in rows if r["official_position"] != "unknown"]
    unknown_frac = round(1 - len(known)/len(rows), 4)
    ambiguity_risk = unknown_frac > 0.20

    if not known:
        return {"ci_vote": float("nan"), "n_total": 0, "n_divergent": 0,
                "unknown_frac": unknown_frac, "ambiguity_risk": True}

    n_div = sum(1 for r in known if r["member_vote"] != r["official_position"])
    ci_vote = round(max(0.0, 1.0 - n_div / len(known)), 4)
    return {"ci_vote": ci_vote, "n_total": len(known), "n_divergent": n_div,
            "unknown_frac": unknown_frac, "ambiguity_risk": ambiguity_risk}


def compute_ci_struct(struct_file, quarter):
    rows = []
    with open(struct_file, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["quarter"] == quarter:
                rows.append(row)

    if not rows:
        return {"ci_struct": 1.0, "n_events": 0, "total_members": 0}

    total_str = rows[0].get("total_members", "0").strip()
    total = int(total_str) if total_str.isdigit() else 0
    if total == 0:
        return {"ci_struct": 1.0, "n_events": 0, "total_members": 0}

    events = [r for r in rows if r.get("event_type","").strip()
              in ("expulsion","resignation","suspension")]
    ci_struct = round(max(0.0, 1.0 - len(events)/total), 4)
    return {"ci_struct": ci_struct, "n_events": len(events), "total_members": total}


# ─────────────────────────────────────────────
# ISC — Agregare si clasificare
# ─────────────────────────────────────────────

def isc_score(cmp, ci, w=0.50):
    if math.isnan(cmp) and math.isnan(ci): return float("nan")
    if math.isnan(cmp): return round(ci, 4)
    if math.isnan(ci):  return round(cmp, 4)
    return round(w * cmp + (1-w) * ci, 4)


def weight_interval(cmp, ci, weights):
    scores = {w: isc_score(cmp, ci, w) for w in weights}
    valid = [v for v in scores.values() if not math.isnan(v)]
    return {
        "by_weight": {str(round(w,2)): round(s,4) for w,s in scores.items()},
        "min": round(min(valid),4) if valid else float("nan"),
        "max": round(max(valid),4) if valid else float("nan"),
        "range": round(max(valid)-min(valid),4) if valid else float("nan"),
    }


def classify_zone(isc_val):
    if math.isnan(isc_val): return "MISSING"
    for threshold, zone in [(0.25,"CRITICAL"),(0.45,"LOW"),(0.70,"MODERATE")]:
        if isc_val < threshold:
            suffix = "*" if abs(isc_val - threshold) <= 0.03 else ""
            return zone + suffix
    return "HIGH"


def classify_phase(history):
    valid = [v for v in history if not math.isnan(v)]
    if len(valid) < 2: return "Insuficient"
    last, prev = valid[-1], valid[-2]
    if last < 0.25: return "Colaps"
    delta = last - prev
    if delta < -0.05: return "Colaps"
    if delta < -0.02: return "Eroziune"
    if delta > 0.02:  return "Consolidare"
    return "Platou"


def ci_volatility(history, window=4):
    try:
        import numpy as np
        valid = [v for v in history[-window:] if not math.isnan(v)]
        if len(valid) < 2: return None
        return round(float(np.std(valid, ddof=1)), 4)
    except ImportError:
        return None


# ─────────────────────────────────────────────
# PIPELINE PRINCIPAL
# ─────────────────────────────────────────────

def run(config):
    print("\n[2/5] Incarcare corpus...")
    corpus_dir = Path(config["corpus_dir"])
    quarters = sorted([d.name for d in corpus_dir.iterdir() if d.is_dir()])
    print(f"    {len(quarters)} trimestre gasite: {', '.join(quarters)}")

    print("\n[3/5] Calcul CMP (Coerenta Mesaj Public)...")
    print("[4/5] Calcul CI (Coeziune Interna)...")
    print("[5/5] Agregare ISC si clasificare...\n")

    results = []
    ci_vote_history = []

    for quarter in quarters:
        texts = []
        for f in sorted((corpus_dir / quarter).iterdir()):
            if f.suffix == ".txt":
                t = f.read_text(encoding="utf-8").strip()
                if len(t.split()) >= 5:
                    texts.append(t)

        # CMP
        cmp_result = compute_cmp_bertopic(texts)
        cmp_val = cmp_result["cmp"]

        # CI
        cv = compute_ci_vote(config["votes_file"], quarter)
        cs = compute_ci_struct(config["struct_file"], quarter)
        ci_vote_val = cv["ci_vote"]
        ci_struct_val = cs["ci_struct"]

        if math.isnan(ci_vote_val) and math.isnan(ci_struct_val):
            ci_val = float("nan")
        elif math.isnan(ci_vote_val):
            ci_val = ci_struct_val
        elif math.isnan(ci_struct_val):
            ci_val = ci_vote_val
        else:
            ci_val = round(0.60 * ci_vote_val + 0.40 * ci_struct_val, 4)

        ci_vote_history.append(ci_vote_val)
        ci_vol = ci_volatility(ci_vote_history)

        # ISC
        isc_val = isc_score(cmp_val, ci_val, w=0.50)
        wi = weight_interval(cmp_val, ci_val, config["weight_sensitivity"])
        zone = classify_zone(isc_val)
        isc_history = [r["isc"] for r in results] + [isc_val]
        phase = classify_phase(isc_history)

        results.append({
            "quarter": quarter,
            "cmp": cmp_val,
            "cmp_method": cmp_result["method"],
            "cmp_h": cmp_result["h"],
            "cmp_stable": cmp_result["stable"],
            "cmp_ci_lower": cmp_result["ci_lower"],
            "cmp_ci_upper": cmp_result["ci_upper"],
            "ci_vote": ci_vote_val,
            "ci_struct": ci_struct_val,
            "ci": ci_val,
            "ci_volatility_4q": ci_vol,
            "ci_ambiguity_risk": cv["ambiguity_risk"],
            "isc": isc_val,
            "isc_min": wi["min"],
            "isc_max": wi["max"],
            "isc_range": wi["range"],
            "zone": zone,
            "phase": phase,
        })

    # ── Output CSV
    out_dir = BASE / "results"
    csv_path = out_dir / f"isc_{config['actor'].lower()}_{config['country'].lower()}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    # ── Output JSON
    json_path = out_dir / f"isc_{config['actor'].lower()}_{config['country'].lower()}_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "actor": config["actor"],
            "country": config["country"],
            "quarters": len(results),
            "results": results,
        }, f, indent=2, ensure_ascii=False)

    # ── Tabel final
    print("\n" + "="*70)
    print(f"  REZULTATE ISC | {config['actor']} | {config['country']}")
    print("="*70)
    print(f"  {'Trimestru':<10} {'CMP':>6} {'CI':>6} {'ISC':>6}  "
          f"{'[min-max]':>14}  {'Zona':>10}  {'Faza'}")
    print("-"*70)
    for r in results:
        cmp_s = f"{r['cmp']:.3f}" if not math.isnan(r['cmp']) else "  NaN"
        ci_s  = f"{r['ci']:.3f}"  if not math.isnan(r['ci'])  else "  NaN"
        isc_s = f"{r['isc']:.3f}" if not math.isnan(r['isc']) else "  NaN"
        int_s = (f"[{r['isc_min']:.3f}-{r['isc_max']:.3f}]"
                 if not math.isnan(r['isc_min']) else "           NaN")
        flags = ""
        if r.get("ci_ambiguity_risk"): flags += " ⚠ambig"
        if not r.get("cmp_stable", True): flags += " ⚠instabil"
        print(f"  {r['quarter']:<10} {cmp_s:>6} {ci_s:>6} {isc_s:>6}  "
              f"{int_s:>14}  {r['zone']:>10}  {r['phase']}{flags}")
    print("="*70)

    # ── Interpretare
    print("\n  INTERPRETARE:")
    for r in results:
        if not math.isnan(r['isc']):
            print(f"  {r['quarter']}: ISC={r['isc']:.3f} → {r['zone']} | "
                  f"CMP={'concentrat' if r['cmp'] > 0.5 else 'dispersat'} | "
                  f"CI={'coerent' if not math.isnan(r['ci']) and r['ci'] > 0.8 else 'fragmentat'}")

    print(f"\n  Metoda CMP folosita: {results[0]['cmp_method'] if results else 'N/A'}")
    print(f"\n  Fisiere salvate:")
    print(f"    CSV:  {csv_path}")
    print(f"    JSON: {json_path}")
    print("\n  Test complet cu succes. Scriptul este gata pentru date reale.\n")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    config = setup()
    run(config)
    input("\nApasa Enter pentru a inchide...")
