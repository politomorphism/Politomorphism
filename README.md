# Politomorphism — Computational Political Anthropology Framework

**Serban Gabriel Florin** | Independent Researcher  
ORCID: [0009-0000-2266-3356](https://orcid.org/0009-0000-2266-3356) | SSRN: [ssrn.com/author=6192814](https://ssrn.com/author=6192814)  
Substack: [profserban.substack.com](https://profserban.substack.com) | GitHub: [github.com/politomorphism](https://github.com/politomorphism)

---

## What is Politomorphism?

**Politomorphism** is a paradigm in **Computational Political Anthropology (CPA)** — a transdisciplinary framework that treats political entities (leaders, movements, institutions) as *morphic agents*: symbolic structures capable of transforming social perception, legitimacy, and collective behavior through measurable computational mechanisms.

The framework integrates political anthropology, computational linguistics, media theory, survival analysis, and inferential statistics into a unified analytical architecture with seven interconnected components.

---

## Framework Components

### 1. Symbol Resonance Model (SRM) ✅ *Published & Validated*

The SRM quantifies the symbolic resonance of political leaders using four empirically grounded variables:

```
SRM_opt = V × A × exp(−λ^0.20 × D^3.00) × N
```

| Variable | Name | Definition |
|----------|------|------------|
| V | Viral Velocity | Diffusion rate of the symbol (log-normalized cascade escalation) |
| A | Affective Weight | Emotional intensity (VADER sentiment analysis) |
| D | Semantic Drift | Semantic stability (0=stable, 1=fully fragmented) |
| N | Network Coverage | Proportion of discourse nodes where the symbol is present |

**Interpretation thresholds:**
- SRM > 0.50 → HIGH RESONANCE
- 0.07 < SRM ≤ 0.50 → MEDIUM RESONANCE
- 0.02 < SRM ≤ 0.07 → LOW RESONANCE
- SRM ≤ 0.02 → MINIMAL RESONANCE

**Validated symbols (25 symbol-periods, LOOCV R²=0.770):**

| Symbol / Context | V | A | D | N | SRM | Interpretation |
|-----------------|---|---|---|---|-----|----------------|
| Sunflower Mvt (TW, 2014) | 0.680 | 0.420 | 0.1717 | 0.580 | 0.0552 | Low |
| Călin Georgescu (RO, 2024) | 0.750 | 0.338 | 0.8815 | 0.880 | **0.0800** | Medium |
| Marcel Ciolacu (RO, 2025–26) | 0.520 | 0.440 | 0.3481 | 0.440 | 0.0345 | Low |
| Donald Trump (US, 2015–16) | 0.106 | 0.560 | 0.3746 | 0.720 | 0.0922 | Medium |
| Zelensky (UA/EU/US, 2022–26) | 0.873 | 0.640 | 0.480 | 0.781 | **0.1121** | Medium |
| Imran Khan (PK, 2018) | — | — | — | — | **0.4349** | HIGH — record dataset entry |
| Javier Milei (AR, 2023–24) | — | — | — | — | 0.0455 | Low |

**Published SSRN papers (Serban 2026a–2026g):**
- [SRM Sunflower Movement Validation](https://ssrn.com/author=6192814)
- [SRM Călin Georgescu Validation](https://ssrn.com/author=6192814)
- [SRM Marcel Ciolacu Validation](https://ssrn.com/author=6192814)
- [SRM Donald Trump Validation](https://ssrn.com/author=6192814)
- [SRM Zelensky Validation](https://ssrn.com/author=6192814)
- [SRM Imran Khan — Record Entry](https://ssrn.com/author=6192814)
- [SRM Javier Milei](https://ssrn.com/author=6192814)

---

### 2. Legitimacy Dynamics Engine (LDE) ✅ *Published*

The LDE models legitimacy trajectories over time using Eurobarometer longitudinal data (EB82–EB104, 2014–2025).

**LDE Preprint #4** — Cross-national calibration on **Greece, Hungary, and Serbia** with bootstrap confidence intervals at model level. Submitted to SSRN (preliminary upload review).

Key features:
- Real Eurobarometer survey data (not proxy calibrations)
- Bootstrap CI at model level
- Cross-national validation across three distinct political regimes

---

### 3. Entropic Equilibrium Function (EEF) ✅ *Published*

The EEF measures the entropic state of political systems — the degree to which a system approaches equilibrium or instability.

**Validation results:**
- Krippendorff α = 0.8116 (inter-rater reliability)
- LOO-CV F1 = 1.000
- Convergent validity confirmed against V-Dem indicators
- Countries validated: Romania, Hungary, Poland (2005–2024)
- V-Dem cross-national extension designed for 13 countries

Published on SSRN. [View paper →](https://ssrn.com/author=6192814)

---

### 4. Political Fragmentation Model (PFM) ✅ *Published*

The PFM aggregates SRM symbol scores into a system-level fragmentation index:

```
PFM(t) = Σ[SRM_i × w_ij × exp(-δ × d_ij)] / EEF(t)
```

Where `w_ij` represents inter-symbol interaction weights and `d_ij` represents ideological distance between symbols.

Published on SSRN as a working paper. [View paper →](https://ssrn.com/author=6192814)

---

### 5. PFM-Survival (PFM-S) ✅ *Published*

PFM-Survival extends the Political Fragmentation Model with survival analysis techniques to model the temporal durability of political configurations.

- Retrospective demonstration on **Friedrich Merz** (Germany)
- Five prospectively **pre-registered predictions on OSF** (DOI: [10.17605/OSF.IO/HYDNZ](https://doi.org/10.17605/OSF.IO/HYDNZ))
- RSF C-index = 0.721

Published on SSRN. Pre-registration on OSF. [View paper →](https://ssrn.com/author=6192814)

---

### 6. Institutional Stability Classifier (ISC) ⚠️ *Null Result — Documented*

The ISC component tested panel fixed-effects models on institutional stability indicators.

**Finding:** Quasi-constant CI_vote (SD < 0.015) produced a methodological artefact, yielding spurious fixed-effects results. This is a **documented null result** — five SSRN documents published openly recording the methodological finding.

Development set: Poland. Held-out validation set: Romania.

This null result reflects the framework's commitment to academic honesty over overclaiming.

---

### 7. Collective Memory Graph (CMG) & Morphic Cascade (MC) 📋 *Theoretical*

CMG and MC remain theoretical proposals awaiting empirical operationalization. Both are documented in the framework's foundational literature.

---

## Politomorf Pipeline v4.2

An automated Romanian political media monitoring system with:
- 26 RSS sources
- 48-hour collection windows
- 4-agent sequential architecture: Collector → NER Extractor → Analysis Engine → Report Generator
- Parliament vote data integration
- Automated report generation

```
agents/
├── agent1_collector.py       # RSS + Parliament data collection
├── agent2_ner_extractor.py   # Named Entity Recognition
├── agent3_analysis.py        # SRM computation + sentiment
└── agent4_report.py          # Report generation
```

---

## SYMBOVOLT Electoral Prediction Model

SYMBOVOLT integrates SRM and EEF scores to generate directional electoral predictions. Validated directionally on the **2025 Hungarian parliamentary election**.

---

## OSF Pre-Registration

All prospective predictions and empirical protocols are pre-registered at the Open Science Framework:

**DOI: [10.17605/OSF.IO/HYDNZ](https://doi.org/10.17605/OSF.IO/HYDNZ)**

---

## Books & Long-form Publications

| Title | Status | Platform |
|-------|--------|----------|
| *Digital Tribalism* | Chapters 1–5 complete (EN) | In progress |
| *Foundations of Computational Political Anthropology* | Drafted | In progress |
| *Juridical Chains* | Published | Amazon / Hatchards / Foyles |
| *Elite Extinction* | In progress — HIER framework chapter complete | In progress |
| ~28–30 volumes total | Published | [Amazon Author Page](https://amazon.com/Serban-Gabriel-Florin/e/B0D57JJ7VX) |

**Digital Tribalism** introduces original theoretical concepts including *Negative Sovereignty*, *Tolerated Illegibility*, *Navigational Citizenship*, and *Parastatal Equilibrium*.

**Foundations of CPA** is structured around a four-axiom architecture with a formal structural impossibility argument.

---

## PACES Platform

**PACES** (Platforma de Analiză Comportamentală și Engagement Social) is a Romanian political media monitoring SaaS platform built on the Politomorphism framework.

- Frontend: React / Vercel
- Backend: FastAPI / Render
- Database: Supabase
- Price: 49€/month

---

## SSRN Working Papers

All working papers are available at: **[ssrn.com/author=6192814](https://ssrn.com/author=6192814)**

Key papers include SRM validations (2026a–2026g), EEF cross-national validation, PFM working paper, PFM-Survival with OSF pre-registration, ISC null result documentation, LDE cross-national calibration, and the Călin Georgescu disinformation ecosystem paper.

---

## Methodology & Quality Control

- All empirical results use LOOCV (Leave-One-Out Cross-Validation)
- Bootstrap confidence intervals reported at model level
- Null results documented and published openly (ISC)
- Adversarial AI review (Grok, ChatGPT) used as quality control before SSRN submission
- V-Dem used as external convergent validity benchmark

---

## License

CC BY 4.0 — All code and data are open source and publicly available.

---

## Citation

```
Serban, G.F. (2026). Politomorphism: Computational Political Anthropology Framework.
GitHub: https://github.com/politomorphism/Politomorphism
ORCID: 0009-0000-2266-3356
OSF Pre-registration: https://doi.org/10.17605/OSF.IO/HYDNZ
```
