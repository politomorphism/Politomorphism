# Politomorphism Engine
### Computational Political Anthropology Framework

**Serban Gabriel Florin** | Independent Researcher | Hannover, Germany  
ORCID: [0009-0000-2266-3356](https://orcid.org/0009-0000-2266-3356) | SSRN: [ssrn.com/author=6192814](https://ssrn.com/author=6192814)  
OSF: [10.17605/OSF.IO/HYDNZ](https://doi.org/10.17605/OSF.IO/HYDNZ) | GitHub: [github.com/politomorphism](https://github.com/politomorphism)  
Substack: [profserban.substack.com](https://profserban.substack.com) | License: CC BY 4.0

---

## What is the Politomorphism Engine?

The Politomorphism Engine is a seven-component computational framework for analyzing political dynamics through symbolic resonance, cognitive frame evolution, institutional entropy, and legitimacy dynamics. It is the empirical core of **Politomorphism** — a paradigm in Computational Political Anthropology (CPA) developed as independent research (2024–2026).

The Engine models a closed feedback cycle:

```
MC(t) → CMG(t) → SRM(t) → EEF(t) → PFM(t) → ISC(t) → LDE(t) → MC(t+1)
```

---

## Quick Start

```bash
git clone https://github.com/politomorphism/Politomorphism.git
cd Politomorphism
pip install -r requirements.txt
python data_collector.py    # collect real RSS data
python fix_data.py          # or generate synthetic data
python mc_run.py            # run MC calibration
python cmg_run.py           # run CMG calibration
```

---

## Repository Structure

```
Politomorphism/
├── components/
│   ├── mc_component.py        # MC — Metapolitical Calibration
│   └── cmg_component.py       # CMG — Cognitive Morphogenesis
├── data/
│   └── real/
│       ├── sentiment_topics.csv
│       ├── srm_scores.csv
│       └── polling.csv        # INSCOP 2024–2026
├── outputs/
│   ├── MC_real_comparative.png
│   ├── MC_real_trajectories.png
│   ├── MC_results.csv
│   ├── CMG_real_results.png
│   └── CMG_real_results.csv
├── data_collector.py
├── fix_data.py
├── mc_run.py
├── cmg_run.py
└── requirements.txt
```

---

## Component Status

| # | Code | Name | Status | SSRN |
|---|------|------|--------|------|
| 1 | MC | Metapolitical Calibration | ✅ Implemented | This repo |
| 2 | CMG | Cognitive Morphogenesis | ✅ Implemented | This repo |
| 3 | SRM | Social Resonance Model | ✅ 25 symbols, R²=0.770 | [6348318](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6348318) |
| 4 | EEF | Entropic Equilibrium Function | ✅ α=0.8116, 3 countries | [6677579](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6677579) |
| 5 | PFM | Political Fragmentation Model | ✅ Published | [6729899](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6729899) |
| 6 | ISC | Symbolic Coherence Index | ✅ Null result documented | [6826140](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6826140) |
| 7 | LDE | Legitimacy Dynamics Engine | 🔄 Partial validation | [6850362](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6850362) |

---

## Component 1 — MC: Metapolitical Calibration

```
S(t+1) = (1 - α) · S(t) + α · W · I(t) + β · SRM(t-1) + ε_MC(t)
```

**β Hypothesis:** Populist actors (AUR, Georgescu) have significantly higher β than institutional actors (PNL, PSD) — they recalibrate strategy more aggressively based on prior resonance feedback.

### Results — Romania 2024–2026

| Actor | Type | α | β | β 95% CI |
|-------|------|---|---|----------|
| AUR | Populist | 0.373 | 0.032 | [0.005, 0.049] |
| Georgescu | Populist | 0.874 | −0.005 | [−0.053, 0.063] |
| PSD | Institutional | 0.228 | −0.023 | [−0.043, 0.010] |
| PNL | Institutional | 0.133 | −0.028 | [−0.073, 0.021] |
| USR | Institutional | 0.506 | 0.034 | [−0.022, 0.063] |

**β_populist = 0.013 > β_institutional = −0.006 → Hypothesis supported.**

Georgescu α=0.874 — highest in dataset, consistent with flash-viral symbol profile and post-annulment symbolic exile dynamics (SSRN 6880661).

![MC Comparative](outputs/MC_real_comparative.png)

![MC Trajectories](outputs/MC_real_trajectories.png)

---

## Component 2 — CMG: Cognitive Morphogenesis

```
C_A(t+1) = C_A(t) + α_A × (S_A(t) − C_A(t)) + γ × SRM_A(t)
C_B(t+1) = C_B(t) + α_B × (S_B(t) − C_B(t)) + γ × SRM_B(t)
POL(t)   = ||C_A(t) − C_B(t)||₂
```

- **Bloc A (populist):** AUR + Georgescu  
- **Bloc B (institutional):** PSD + PNL + USR

**Differential Update Rate Hypothesis:** α_A > α_B — populist-receptive subpopulation updates cognitive frames faster.

### Polarization Zones

| POL(t) | Zone |
|--------|------|
| > 0.30 | STRUCTURAL |
| 0.15–0.30 | ELEVATED |
| 0.05–0.15 | MODERATE |
| < 0.05 | LOW |

### Results — Romania 2024–2026

| Parameter | Estimate | 95% CI |
|-----------|----------|--------|
| α_A | 0.055 | [0.020, 0.062] |
| α_B | 0.036 | [0.012, 0.045] |
| γ | −0.479 | [−0.500, −0.114] |
| POL trend | −0.021 | DECREASING |

**Key finding:** γ = −0.479 entirely negative. Post-electoral annulment (Romania, Dec 2024): Georgescu's resonance driven by juridical exclusion narratives → resonance-induced frame *freezing*, not amplification. Consistent with Symbolic Exile framework (SSRN 6880661).

![CMG Results](outputs/CMG_real_results.png)

---

## Component 3 — SRM: Social Resonance Model

```
SRM = V × A × exp(−λ^0.20 × D^3.00) × N
```

**25 symbol-periods validated | LOOCV R²=0.770**

| Symbol | Context | SRM | Category |
|--------|---------|-----|----------|
| Imran Khan | PK, 2018 | 0.4349 | HIGH — Ultra-Sustained Ambient Saturation |
| Zelensky | UA/EU/US, 2022–26 | 0.1121 | MEDIUM — Distributed |
| Trump | US, 2015–16 | 0.0922 | MEDIUM — Electoral Burst |
| Georgescu | RO, Oct–Dec 2024 | 0.0800 | MEDIUM — Electoral Burst |
| Milei | AR, 2023–24 | 0.0455 | LOW |
| Ciolacu | RO, 2025–26 | 0.0345 | LOW |

CCFI confirmed: Cross-Cultural Frame Incompatibility does not decay to zero (Narendra Modi, India 2024).

---

## Component 4 — EEF: Entropic Equilibrium Function

```
IS(t) = α · H(t) + (1−α) · V(t)
H(t)  = S(t) / ln(3)              [normalized Shannon entropy]
V(t)  = 0.0·p₀ + 0.5·p₁ + 1.0·p₂
```

- Krippendorff α = 0.8116
- V-Dem convergent validity: r = −0.980 (Hungary), r = −0.941 (Poland)
- LOOCV accuracy = 1.000
- Superior early warning vs. Freedom House for Romania 2024

---

## Component 5 — PFM: Political Fragmentation Model

```
PFM(t) = Σ[SRM_i × w_ij × exp(−δ × d_ij)] / EEF(t)
```

Formal theory of fragmentation propagation. Published SSRN 6729899.

---

## Component 6 — ISC: Symbolic Coherence Index

```
ISC_A(t) = 0.5 · CMP_A(t) + 0.5 · CI_A(t)
```

**Null result documented openly (SSRN 6826140):** ISC does not predict electoral support Romania 2019–2024.  
**Governing Party Penalty confirmed:** −1.1 pp/quarter (p < 0.001).

---

## Component 7 — LDE: Legitimacy Dynamics Engine

```
L(t+1) = L(t) + λ[α·P(t) + β·N(t) − γ·C(t)] − θ[L(t) − L*]
```

| Country | R² | 95% CI | Status |
|---------|-----|--------|--------|
| Greece | 0.624 | [0.416, 0.986] | ✅ Validated |
| Serbia | 0.308 | [0.065, 0.933] | ✅ Validated |
| Hungary | — | [−0.111, 0.967] | Inconclusive |

**LDE Roadmap:** 3.0 (memory + SRM feedback) → 3.1 (ISC integration) → 4.0 (institutional network) → 5.0 (state-space)

---

## Methodology

- LOOCV for all empirical results
- Bootstrap CIs (300–500 replications)
- Null results documented openly
- Adversarial AI review (Grok, ChatGPT) before SSRN submission
- V-Dem v14 as convergent validity benchmark
- L-BFGS-B parametric optimization
- OSF pre-registration for prospective predictions

---

## Citation

```
Serban, G.F. (2026). Politomorphism Engine: Computational Political Anthropology Framework.
GitHub: https://github.com/politomorphism/Politomorphism
ORCID: 0009-0000-2266-3356
SSRN: https://ssrn.com/author=6192814
OSF: https://doi.org/10.17605/OSF.IO/HYDNZ
```

---

License: CC BY 4.0 — All code and data open source.
