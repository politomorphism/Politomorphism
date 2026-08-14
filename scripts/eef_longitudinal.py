"""
EEF Longitudinal Validation v4 — Politomorphism Engine, Component #4
=======================================================================
Computes EEF instability scores IS(t) for a six-country panel (120 country-years):
  Baseline (v1-v3): Romania, Hungary, Poland — all HIGH/CRITICAL, no low-instability control
  v4 extension:     Estonia (consolidated-democracy control), Slovakia (intermediate
                     oscillator), Serbia (competitive-authoritarian trajectory)

Formula (per repo README.md, Component #4):
    IS(t) = alpha * H(t) + (1 - alpha) * V(t)
    H(t)  = S(t) / ln(3)                          [normalized Shannon entropy of the
                                                     3-state fuzzy membership distribution
                                                     p0/p1/p2]
    V(t)  = 0.0*p0 + 0.5*p1 + 1.0*p2               [severity-weighted score]

Domains (per compute_eef.py convention — VERIFY breakpoints match before use):
    Justice   <- FH NIT "Judicial Framework and Independence" (1.00-7.00)
    Electoral <- FH NIT "Electoral Process" (1.00-7.00)
    Coalition <- BTI "Political Participation" (1-10, rescaled)  [BTI = TODO, see below]

===============================================================================
CRITICAL SCALE-CONVENTION NOTE (read before adding any new country)
===============================================================================
Freedom House Nations in Transit relabeled AND retroactively renumbered its 1-7
scale starting with the NIT 2020 edition (events of 2019):
  - OLD convention (editions through NIT 2019, i.e. events through 2018):
        1.00 = best/most democratic, 7.00 = worst/most authoritarian
  - NEW convention (editions NIT 2020 onward, i.e. events 2019+):
        1.00 = worst/most authoritarian, 7.00 = best/most democratic
  - Conversion:  new = 8 - old   (verified arithmetically across dozens of
    country-years; e.g. Estonia Electoral Process 1.50 old <-> 6.50 new)

This script uses the NEW convention (7 = best) throughout, consistent with the
existing Romania/Hungary/Poland series (Hungary's Judicial Framework declining
from higher to 1.75 by 2024 only makes sense as democratic backsliding under the
new/7=best convention). If your existing RO/HU/PL values turn out to be on the
OLD convention instead, convert with score_new = 8 - score_old before merging.

===============================================================================
DATA PROVENANCE FLAGS
===============================================================================
  [VERIFIED]      Read directly from an official FH NIT country-report PDF/page,
                   or unambiguously chained from FH's own "declined/improved from
                   X to Y" statements across every intervening edition.
  [RECONSTRUCTED] Chained from adjacent editions but not read from a single
                   authoritative table; flagged for direct spot-check.
  [PARTIAL/TODO]   Value not available in this script's source material; must be
                   completed from the original project source before publication.
  [NOT FOUND]      BTI Political Participation — not extracted from an official
                   source in this pass. Do NOT estimate; pull from the official
                   BTI combined-scores workbook (bti-project.org) before use.

Author : Serban Gabriel Florin | ORCID: 0009-0000-2266-3356
Project: Politomorphism Engine | OSF: 10.17605/OSF.IO/HYDNZ
"""

import math
import csv
import json

# ── SECTION 1: RAW DATA — FH NIT "Judicial Framework and Independence" ──────
# Scale: 1.00-7.00, quarter-point increments, NEW convention (7 = best).
#
# Romania/Hungary/Poland below are reproduced EXACTLY as recovered from a prior
# project session (partial recovery — Poland's series was cut off mid-list in
# the source material). VERIFY every RO/HU/PL value against your own original
# compute_eef.py / eef_longitudinal.py before using in publication — treat
# these as [PARTIAL/TODO], not [VERIFIED], despite looking complete for RO/HU.

FH_JUDICIAL = {
    "Romania": {  # [PARTIAL/TODO — verify against original source]
        2005: 3.50, 2006: 3.50, 2007: 3.75, 2008: 3.75, 2009: 4.00,
        2010: 4.00, 2011: 3.75, 2012: 3.75, 2013: 4.00, 2014: 4.00,
        2015: 4.25, 2016: 4.25, 2017: 4.00, 2018: 3.75, 2019: 3.75,
        2020: 4.00, 2021: 4.00, 2022: 4.00, 2023: 4.25, 2024: 4.50,
    },
    "Hungary": {  # [PARTIAL/TODO — verify against original source]
        2005: 4.25, 2006: 4.25, 2007: 4.25, 2008: 4.25, 2009: 4.25,
        2010: 4.00, 2011: 3.50, 2012: 3.00, 2013: 2.75, 2014: 2.50,
        2015: 2.25, 2016: 2.00, 2017: 2.00, 2018: 2.00, 2019: 2.00,
        2020: 2.00, 2021: 1.75, 2022: 1.75, 2023: 1.75, 2024: 1.75,
    },
    "Poland": {  # [PARTIAL/TODO — source cut off; RECOMPLETE 2016-2024 below
                  # are a placeholder continuation and MUST be re-verified,
                  # they are NOT confirmed from an official FH table in this pass]
        2005: 4.25, 2006: 4.25, 2007: 4.50, 2008: 4.50, 2009: 4.50,
        2010: 4.50, 2011: 4.50, 2012: 4.75, 2013: 4.75, 2014: 4.75,
        2015: 4.75, 2016: None, 2017: None, 2018: None, 2019: None,  # TODO
        2020: None, 2021: None, 2022: None, 2023: None, 2024: None,  # TODO
    },
    # ── v4 extension — [VERIFIED] against official FH NIT country reports,
    #    new convention (7 = best), events-year indexed. Source: research
    #    report "Freedom House NIT and Bertelsmann BTI Data Extraction for
    #    Estonia, Slovakia, and Serbia (2005-2024)".
    "Estonia": {
        2004: 6.50, 2005: 6.50, 2006: 6.50, 2007: 6.50, 2008: 6.50,
        2009: 6.50, 2010: 6.50, 2011: 6.50, 2012: 6.50, 2013: 6.50,
        2014: 6.50, 2015: 6.50, 2016: 6.50, 2017: 6.50, 2018: 6.50,
        2019: 6.50, 2020: 6.50, 2021: 6.50, 2022: 6.50, 2023: 6.50,
    },
    "Slovakia": {
        2004: None,  # TODO: JFI value for edition-2005 not confirmed in source
        2005: 6.00, 2006: 6.00, 2007: 5.75, 2008: 5.25, 2009: 5.00,
        2010: 5.25, 2011: 5.25, 2012: 5.00, 2013: 5.00, 2014: 5.00,
        2015: 5.25, 2016: 5.25, 2017: 5.25, 2018: 5.25, 2019: 5.00,
        2020: 5.25, 2021: 5.25, 2022: 5.25, 2023: 5.25,
    },
    "Serbia": {
        2004: 3.75, 2005: 3.75, 2006: 3.75, 2007: 3.50, 2008: 3.50,
        2009: 3.50, 2010: 3.50, 2011: 3.50, 2012: 3.50, 2013: 3.50,
        2014: 3.50, 2015: 3.50, 2016: 3.50, 2017: 3.50, 2018: 3.50,
        2019: 3.50, 2020: 3.50, 2021: 3.50, 2022: 3.50, 2023: 3.25,
    },
}

# ── SECTION 2: RAW DATA — FH NIT "Electoral Process" ─────────────────────────
# Scale: 1.00-7.00, quarter-point increments, NEW convention (7 = best).

FH_ELECTORAL = {
    "Romania": {  # [PARTIAL/TODO — verify against original source; series was
                   # cut off mid-list in the recovered fragment]
        2005: 3.25, 2006: 3.25, 2007: 3.50, 2008: 3.50, 2009: 3.50,
        2010: 3.50, 2011: 3.50, 2012: 3.50, 2013: 3.75, 2014: 3.75,
        2015: 3.75, 2016: 3.75, 2017: 3.75, 2018: 3.75, 2019: 3.75,
        2020: 3.75, 2021: 3.75, 2022: 3.75, 2023: 3.75, 2024: 3.25,
    },
    "Hungary": {  # [PARTIAL/TODO — verify against original source]
        2005: 4.00, 2006: 4.00, 2007: 4.00, 2008: 4.00, 2009: 3.75,
        2010: 3.75, 2011: 3.50, 2012: 3.25, 2013: 3.00, 2014: 2.75,
        2015: 2.75, 2016: 2.75, 2017: 2.50, 2018: 2.50, 2019: 2.50,
        2020: 2.50, 2021: 2.25, 2022: 2.25, 2023: 2.25, 2024: 2.00,
    },
    "Poland": {  # [PARTIAL/TODO — source cut off after 2014; RECOMPLETE]
        2005: 4.50, 2006: 4.50, 2007: 4.75, 2008: 4.75, 2009: 4.75,
        2010: 4.75, 2011: 4.75, 2012: 4.75, 2013: 4.75, 2014: 4.75,
        2015: None, 2016: None, 2017: None, 2018: None, 2019: None,  # TODO
        2020: None, 2021: None, 2022: None, 2023: None, 2024: None,  # TODO
    },
    # ── v4 extension — [VERIFIED], new convention (7 = best).
    "Estonia": {
        2004: 6.50, 2005: 6.50, 2006: 6.50, 2007: 6.50, 2008: 6.50,
        2009: 6.25, 2010: 6.25, 2011: 6.25, 2012: 6.25, 2013: 6.25,
        2014: 6.25, 2015: 6.50, 2016: 6.50, 2017: 6.50, 2018: 6.50,
        2019: 6.50, 2020: 6.50, 2021: 6.50, 2022: 6.50, 2023: 6.50,
    },
    "Slovakia": {
        2004: 6.75, 2005: 6.75, 2006: 6.50, 2007: 6.50, 2008: 6.50,
        2009: 6.25, 2010: 6.50, 2011: 6.50, 2012: 6.50, 2013: 6.50,
        2014: 6.50, 2015: 6.50, 2016: 6.50, 2017: 6.50, 2018: 6.50,
        2019: 6.25, 2020: 6.25, 2021: 6.25, 2022: 6.25, 2023: 6.25,
    },
    "Serbia": {
        2004: 4.75, 2005: 4.75, 2006: 4.75, 2007: 4.75, 2008: 4.75,
        2009: 4.75, 2010: 4.75, 2011: 4.75, 2012: 4.75, 2013: 4.75,
        2014: 4.75, 2015: 4.75, 2016: 4.75, 2017: 4.75, 2018: 4.75,
        2019: 4.50,  # [RECONSTRUCTED — verify directly against NIT2020 Serbia page]
        2020: 4.25, 2021: 4.25, 2022: 4.25, 2023: 3.75,
    },
}

# ── SECTION 3: RAW DATA — BTI "Political Participation" ─────────────────────
# Scale: 1-10, higher = better (standard BTI orientation, no reversal).
# Biennial: 2006, 2008, 2010, 2012, 2014, 2016, 2018, 2020, 2022, 2024.
#
# [NOT FOUND] for all three v4 countries. Do NOT estimate. Extract from the
# official combined BTI scores workbook (bti-project.org, "BTI 2006-2024
# Scores.xlsx" or the current combined-rounds file) or from the individual
# country-report / country-dashboard pages:
#   bti-project.org/en/reports/country-report/EST  (and /SVK, /SRB)
# Note: BTI 2006 assessed Serbia jointly as "Serbia and Montenegro" (state
# union dissolved June 2006); standalone "Serbia" from BTI 2008 on.

BTI_POLITICAL_PARTICIPATION = {
    "Estonia": {y: None for y in range(2006, 2025, 2)},   # TODO — all NOT FOUND
    "Slovakia": {y: None for y in range(2006, 2025, 2)},  # TODO — all NOT FOUND
    "Serbia": {y: None for y in range(2006, 2025, 2)},    # TODO — all NOT FOUND
    # Romania/Hungary/Poland BTI series: not reproduced here — pull from your
    # original eef_longitudinal.py / compute_eef.py source alongside the RO/HU/PL
    # FH TODOs above.
}

COUNTRIES_V4_NEW = ["Estonia", "Slovakia", "Serbia"]
COUNTRIES_BASELINE = ["Romania", "Hungary", "Poland"]
ALL_COUNTRIES = COUNTRIES_BASELINE + COUNTRIES_V4_NEW


# ── SECTION 4: Score-to-probability mapping ──────────────────────────────────
# Maps a 1.00-7.00 FH-style score (7 = best) to fuzzy membership [p0, p1, p2]
# over three instability states: p0 = consolidated/low, p1 = moderate/watch,
# p2 = severe/critical. Breakpoints below are illustrative defaults and MUST
# be reconciled against the exact fuzzy breakpoints already coded in your
# project's compute_eef.py (per the 12 Jul 2026 session note: "breakpoint-urile
# funcțiilor fuzzy trebuie sincronizate cu compute_eef.py din repo — nivelurile
# IS din demonstrație nu sunt comparabile cu R_EEF publicat până la reconciliere").

def _score_to_probs(score):
    """
    score: 1.00 (worst) - 7.00 (best), new FH convention.
    Returns [p0, p1, p2] summing to 1.0, where higher p2 = more instability.
    Piecewise-linear default mapping — RECONCILE against compute_eef.py.
    """
    if score is None:
        return None
    # Normalize 1-7 (worst-best) to 0-1 instability axis x (1=worst instability)
    x = (7.0 - score) / 6.0  # 0 = best (score=7), 1 = worst (score=1)
    if x <= 0.33:
        p2 = 0.0
        p0 = 1.0 - (x / 0.33)
        p1 = 1.0 - p0
    elif x <= 0.66:
        p0 = 0.0
        frac = (x - 0.33) / 0.33
        p1 = 1.0 - frac
        p2 = frac
    else:
        p0 = 0.0
        p1 = max(0.0, 1.0 - (x - 0.66) / 0.34)
        p2 = 1.0 - p1
    return [round(p0, 4), round(p1, 4), round(p2, 4)]


def shannon_entropy_norm(probs):
    """H(t) = Shannon entropy of [p0,p1,p2] normalized by ln(3)."""
    if probs is None:
        return None
    s = 0.0
    for p in probs:
        if p > 0:
            s -= p * math.log(p)
    return s / math.log(3)


def severity_score(probs):
    """V(t) = 0*p0 + 0.5*p1 + 1.0*p2"""
    if probs is None:
        return None
    p0, p1, p2 = probs
    return 0.0 * p0 + 0.5 * p1 + 1.0 * p2


def domain_is(score, alpha=0.5):
    """IS(t) = alpha*H(t) + (1-alpha)*V(t) for a single domain score."""
    probs = _score_to_probs(score)
    if probs is None:
        return None
    h = shannon_entropy_norm(probs)
    v = severity_score(probs)
    return alpha * h + (1 - alpha) * v


# ── SECTION 5: Aggregate IS_agg across domains ───────────────────────────────

def compute_country_year_is(country, year, alpha=0.5):
    """
    Returns dict with domain-level and aggregate IS for one country-year.
    Coalition domain (BTI) is included only if a non-None value exists for
    that biennial year; otherwise it is excluded from the aggregate average
    (documented, not silently zero-filled).
    """
    jfi = FH_JUDICIAL.get(country, {}).get(year)
    ep = FH_ELECTORAL.get(country, {}).get(year)
    bti_year = year if year % 2 == 0 else year - 1  # nearest biennial round
    bti = BTI_POLITICAL_PARTICIPATION.get(country, {}).get(bti_year)
    bti_rescaled = None
    if bti is not None:
        bti_rescaled = 1.0 + (bti - 1.0) * (6.0 / 9.0)  # rescale 1-10 -> 1-7

    is_justice = domain_is(jfi, alpha)
    is_electoral = domain_is(ep, alpha)
    is_coalition = domain_is(bti_rescaled, alpha)

    domains_available = [d for d in (is_justice, is_electoral, is_coalition) if d is not None]
    is_agg = sum(domains_available) / len(domains_available) if domains_available else None

    return {
        "country": country,
        "year": year,
        "JFI_raw": jfi,
        "EP_raw": ep,
        "BTI_PartPart_raw": bti,
        "IS_justice": is_justice,
        "IS_electoral": is_electoral,
        "IS_coalition": is_coalition,
        "IS_agg": is_agg,
        "n_domains": len(domains_available),
    }


def build_panel(alpha=0.5):
    rows = []
    for country in ALL_COUNTRIES:
        years = sorted(set(FH_JUDICIAL.get(country, {}).keys()) | set(FH_ELECTORAL.get(country, {}).keys()))
        for year in years:
            rows.append(compute_country_year_is(country, year, alpha=alpha))
    return rows


def export_csv(rows, path="eef_v4_panel.csv"):
    fieldnames = ["country", "year", "JFI_raw", "EP_raw", "BTI_PartPart_raw",
                  "IS_justice", "IS_electoral", "IS_coalition", "IS_agg", "n_domains"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    print(f"Wrote {len(rows)} rows to {path}")


def summarize_data_completeness():
    """Reports how many country-years have TODO/None values, per country/indicator."""
    print("=== Data completeness audit ===")
    for country in ALL_COUNTRIES:
        jfi_missing = sum(1 for v in FH_JUDICIAL.get(country, {}).values() if v is None)
        ep_missing = sum(1 for v in FH_ELECTORAL.get(country, {}).values() if v is None)
        jfi_total = len(FH_JUDICIAL.get(country, {}))
        ep_total = len(FH_ELECTORAL.get(country, {}))
        print(f"{country:10s} | JFI missing: {jfi_missing}/{jfi_total} | EP missing: {ep_missing}/{ep_total}")
    print()
    print("BTI Political Participation: ALL values NOT FOUND for Estonia/Slovakia/Serbia")
    print("(30/30 cells None) — extract from official BTI workbook before publication.")


if __name__ == "__main__":
    summarize_data_completeness()
    print()
    panel = build_panel(alpha=0.5)
    export_csv(panel, "eef_v4_panel.csv")

    print("\n=== Sample: Estonia vs Serbia, most recent available year ===")
    for country in ["Estonia", "Serbia"]:
        recent = [r for r in panel if r["country"] == country and r["IS_agg"] is not None]
        if recent:
            latest = max(recent, key=lambda r: r["year"])
            print(f"{country} {latest['year']}: IS_agg={latest['IS_agg']:.4f} "
                  f"(Justice={latest['IS_justice']:.3f}, Electoral={latest['IS_electoral']:.3f}, "
                  f"n_domains={latest['n_domains']})")
