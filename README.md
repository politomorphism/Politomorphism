Politomorphism proposes a computational framework for studying political dynamics as a coupled system of symbolic resonance, cognitive frame change, institutional entropy, fragmentation, symbolic coherence, and legitimacy dynamics. Rather than treating these processes as isolated phenomena, the framework operationalizes them as interacting components and tests their empirical relationships using longitudinal and cross-national data.

The seven components are at different stages of empirical validation; the framework should therefore be understood as an evolving research program rather than a fully validated unified theory.

**Serban Gabriel Florin** | I.Researcher | Hannover, Germany  
ORCID: [0009-0000-2266-3356](https://orcid.org/0009-0000-2266-3356) | SSRN: https://papers.ssrn.com/sol3/cf_dev/AbsByAuth.cfm?per_id=10601216 
OSF: [10.17605/OSF.IO/HYDNZ](https://doi.org/10.17605/OSF.IO/HYDNZ) | GitHub: [github.com/politomorphism](https://github.com/politomorphism)  
ResearchGate: [Serban-Gabriel-Florin](https://www.researchgate.net/profile/Serban-Gabriel-Florin) | Academia.edu: [SerbanGabrielFlorin](https://independent.academia.edu/SerbanGabrielFlorin) | Google Scholar: [profile](https://scholar.google.com/citations?user=XibM3X0AAAAJ&hl=en)  
Substack: [profserban.substack.com](https://profserban.substack.com) | License: CC BY 4.0

---

## What is the Politomorphism Engine?

The Politomorphism Engine is a seven-component computational framework for analyzing political dynamics through symbolic resonance, cognitive frame evolution, institutional entropy, and legitimacy dynamics. It is the empirical core of **Politomorphism** — a paradigm in Computational Political Anthropology (CPA) developed by **Serban Gabriel Florin** as independent research (2024–2026).

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
| 3 | SRM | Social Resonance Model | ✅ 25 symbols, R²=0.770 | 6348318 |
| 4 | EEF | Entropic Equilibrium Function | ⚠️ Provisional — α=0.8116 validated on original 3 countries; 6-country extension (Estonia/Slovakia/Serbia) in progress, see [Data Integrity Note](docs/Data_Integrity_Note_NIT_Scale_Conversion.pdf) | 6677579 |
| 5 | PFM | Political Fragmentation Model | ✅ Published | 6729899 |
| 6 | ISC | Symbolic Coherence Index | ✅ Null result documented | 6826140 |
| 7 | LDE | Legitimacy Dynamics Engine | 🔄 Partial validation | 6850362 |

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

![MC Comparative](MC_real_comparative.png)

![MC Trajectories](MC_real_trajectories.png)

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

![CMG Results](CMG_real_results.png)

**Companion working paper:** *Operationalizing the Cognitive Maturation Gradient (CMG): A Transparent Measurement Framework, with Evidence from Romania (2005–2018)* documents a fully sourced, independently reproducible protocol (Eurostat tertiary-education series + WVS/EVS survey waves) for the national-level E(t)/T(t)/K(t)/C(t) trajectory — distinct from, and complementary to, the bloc-polarization application above. It fixes source selection, a mechanical shock-coding rule, theoretical-bound normalization, equal-weight defaults with a 3×3 sensitivity analysis, and introduces a formal **transition-zone rule** (|C(t) − τ| ≤ δ) for interpreting stage classifications near numeric thresholds, now part of CMG's general definition.

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
- 
Data Integrity: Freedom House NIT Scale Conversion (2005–2024)

Freedom House changed the coding convention of its Nations in Transit (NIT) 1–7 scale starting with the NIT 2020 edition (events of 2019), retroactively renumbering the historical series:

Old convention (through NIT 2019): 1 = most democratic, 7 = most authoritarian
New convention (NIT 2020 onward): 1 = most authoritarian, 7 = most democratic
Conversion: score_new = 8 − score_old

All indicator series in the EEF v4 panel are standardized to the new (7 = best) convention. This is a data-integrity correction, not a full numerical validation — see the note for the distinction between convention correction, coverage gaps, and fuzzy-transformation uncertainty still pending reconciliation.

📄 Full write-up: Data Integrity Note (PDF) · OSF

Series	Status
Romania / Hungary / Poland — Judicial & Electoral	New convention; not yet line-by-line re-verified
Poland — Judicial 2016–2024, Electoral 2015–2024	Missing (coverage gap)
Estonia / Slovakia / Serbia — Judicial & Electoral	New convention; verified against official country reports
BTI Political Participation (Estonia/Slovakia/Serbia)	Not yet extracted (0/30 cells)

Author: Serban Gabriel Florin · ORCID: 0009-0000-2266-3356

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
| Slovakia | 0.003 | [0.018, 0.836] | ❌ Null result — referent-instability diagnosis (partisan re-alignment of trust, not continuous shock-recovery) |

**Confirmatory extension in progress:** the transition-versus-stability hypothesis motivated by the Hungary/Slovakia results has been converted into a pre-registered, falsifiable test — Bulgaria (high partisan turnover) vs. Portugal (low partisan turnover) — with country selection, crisis-coding rule, and decision thresholds locked *before* data extraction. OSF registration: [10.17605/OSF.IO/HYDNZ](https://doi.org/10.17605/OSF.IO/HYDNZ), registered 21 July 2026.

---

## SRM → EEF Coupling (in progress)

First empirical test of the theorized inter-component coupling mechanism (symbolic divergence generating systemic entropy, Π(t) = π₀ + π₁·ICI_var(t) + ε(t)). Requires a same-country SRM series calibrated across multiple distinct years, matched against EEF's existing longitudinal panel — a data structure that did not previously exist for any single leader. Building it now for Viktor Orbán (Hungary), whose EEF longitudinal series already spans 2005–2024.

| Year | λ | PE | ICI | D | A | N |
|------|-----|-------|------------------------|-------|-------|-------|
| 2010 | 2.14 | 0.468 | 0.710 [0.672, 0.745] | 0.589 | 0.278 | 0.208 |

Method: Google Trends (Brent's method for λ), Media Cloud (US National + US State & Local + European collections), LDA topic modeling (K=10, PE), sentence-embedding bootstrap n=200 (ICI), VADER (A). D = 0.5·PE + 0.5·ICI, fixed to match the already-calibrated Orbán reference point.

Remaining: 2014, 2018, and a recalculation of the existing single Orbán point on the same calendar-year window (2022) for full internal comparability before the coupling regression is estimated.

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
Computational Political Anthropology: Defining a New Field and Its Core Engine

The Politomorphism Framework

Șerban Gabriel Florin
Independent Researcher, Hannover, Germany
ORCID 0009-0000-2266-3356 · OSF DOI 10.17605/OSF.IO/HYDNZ · github.com/politomorphism

Abstract

Political anthropology has long studied symbols, cognition, institutions and legitimacy, and computational social science now measures each of them at scale, but the two traditions treat these domains as separate objects. 

No formal framework models them as one coupled system. This paper proposes Computational Political Anthropology (CPA) as an emergent discipline whose task is to represent the symbolic, cognitive, institutional and legitimational layers of political life within a single set of equations that can be estimated from data and refuted by it. 

We present the Politomorphism Engine, a seven-component formalization (MC, CMG, SRM, EEF, PFM, ISC, LDE), and state it as a coupled discrete-time dynamical system. 

The most developed component, the Social Resonance Model, rests on a corpus of 22 symbol-periods in the primary PE/ICI dataset, extended to 24–25 with later case studies, spanning 14 countries and 2013–2024; we report what this corpus supports, including a strong within-sample association between decay rate and resonance and a Cross-Cultural Frame Incompatibility effect, and what it does not, including a negative out-of-sample result for persistence forecasting and several documented null and falsified results in other components. 

We then derive three falsifiable system-level predictions from the coupling structure, set out a three-to-five-year research agenda, and invite replication: all code, data and pipelines are open.

Keywords: computational political anthropology; politomorphism; symbolic resonance; dynamical systems; falsifiability; open science

1. The Problem
Classical political anthropology made its name by showing that power is exercised through meaning. 
Rituals, emblems, kinship idioms and founding narratives are not decoration laid over institutions; they are part of how authority is produced, contested and withdrawn.

The tradition from Turner and Geertz to Kapferer and Scott is rich in description and thin in formalization. 
Its claims about how a symbol gains or loses the capacity to coordinate a population are typically argued through cases, and the cases are rarely comparable with one another.

Contemporary computational social science has the opposite profile. It measures sentiment, framing, topic structure, network diffusion, institutional quality and public trust with considerable precision, and it does so on corpora that no field researcher could assemble. 
But it measures these things in separate literatures with separate vocabularies. 
Framing research does not speak to democratic-backsliding indices, and legitimacy surveys do not speak to the attention dynamics of individual symbols. 

Each community has good instruments for one layer, and no account of how the layers feed one another.
The missing object is a couple model. If a politically potent symbol fractures into incompatible readings across media, does that fracture raise the rate at which institutional disorder is produced? 

If legitimacy collapses, do actors recalibrate their symbolic strategy, and at what speed? If the population's cognitive frames diverge, does that amplify symbolic polarization in turn? 

These are questions about interaction between layers, and they cannot be answered by any single-layer model, however well validated. 
They require a framework in which the layers are written down in a common formal language, with explicit transmission mechanisms between them, so that the interactions become estimable and, above all, refutable.

3. The Proposal
4. 
2.1 Computational Political Anthropology as a discipline
   
We propose Computational Political Anthropology (CPA) as the discipline that studies political meaning-making through formally specified, data-estimable models. 

It inherits from anthropology the conviction that symbols, cognition and institutions are one phenomenon seen at different scales, and it inherits from computational social science the requirement that claims be operationalized, reproducible and exposed to disconfirmation. CPA is not a method for measuring a single construct. 

It is a research programme defined by three commitments: that the symbolic, cognitive, institutional and legitimational layers be modelled jointly; that every component carry an explicit validation status separating what has been measured from what has been theorized; and that the coupling between components, not only the components themselves, be treated as the object of empirical test.

The concept at the centre of the programme is politomorphism: the capacity of political symbols to transform their semiotic structure as they diffuse through public discourse, acting as morphogenetic agents whose dynamics become partly autonomous from the intentions of the actors they represent (cf. Archer, 1995). 

A companion note distinguishes intentional politomorphism, in which actors engineer meaning strategically, from emergent politomorphism, in which meaning drifts through uncoordinated reuse, and proposes drift, network-coverage and affective-weight signatures for telling them apart.
2.2 The Politomorphism Engine

The Politomorphism Engine is the formal core of CPA. It has seven components, each addressing one layer of political reality. 

Table 1 summarizes them together with their current evidential status, which we regard as part of the specification rather than an afterthought.
Table 1. The seven components of the Politomorphism Engine and their current status

Component	Layer	Core formalization	Current status

MC, Metapolitical Calibration	Actor strategy	S(t+1) = (1−α)S(t) + αW·I(t) + β·R(t−1) + ε	Specified; parameter recovery on synthetic data; preliminary Romanian estimates over 12 quarters (β challenger 0.033 vs. governmental −0.026)

CMG, Cognitive Morphogenesis	Collective frames	Two-subpopulation frame updating with resonance amplification γ·R	Romania 2024–2026: α_A = 0.055 > α_B = 0.036, γ = −0.479 (CI entirely negative)

SRM, Social Resonance Model	Symbols	R = V·A·exp(−λD)·N, with D = ½PE + ½ICI	Most developed; 22 symbol-periods in the primary dataset, 24–25 with later cases

EEF, Entropic Equilibrium Function	Institutions	IS(t) = ½H(t) + ½V(t); dIS = Π − Φ	Romania, Hungary, Poland 2005–2024; convergent validity with V-Dem (r = −0.98 Hungary, −0.94 Poland)

PFM, Political Fragmentation Model	Actor network	PFM = Σ R_i·w_ij·exp(−δd_ij) / IS	Three-country validation; one prediction falsified, one not supported at annual resolution

ISC, Symbolic Coherence Index	Actor coherence	ISC = weighted mean of message coherence (CMP) and internal cohesion (CI)	Predictive hypothesis not supported in panel fixed-effects tests (null result, 63 observations)

LDE, Legitimacy Dynamics Engine	Legitimacy	L(t+1) = L(t) + κ[αP + βN − γC]	Non-identifiable at low series variance; a pre-registered confirmatory test returned the opposite sign

Notation: R is symbolic resonance (SRM), V viral velocity, A affective weight, D semantic drift, N network coverage, λ the temporal decay constant, PE polysemy entropy, ICI intra-contextual incoherence. The responsiveness coefficient of LDE is written κ and the erosion rate in the ISC equation ρ, to avoid collision with the decay constant λ.

2.3 The Engine as a couple dynamical system

Written as a system, the Engine has a state vector x(t) collecting the actor state S, the frame vectors C_A and C_B of two subpopulations, the resonance R of the symbols in play, the institutional instability IS, the fragmentation PFM, the coherence ISC and the legitimacy L. 
Its evolution is governed by component equations that read each other's outputs. 

The principal ones are:

S(t+1) = (1 − α)·S(t) + α·W·I(t) + β·R(t−1) + ε_MC(t)
C_k(t+1) = C_k(t) + α_k·(S_k(t) − C_k(t)) + γ·R_k(t),   k ∈ {A, B}
POL(t) = ‖C_A(t) − C_B(t)‖
R(t) = V · A · exp(−λ·D) · N,   D = ½·PE + ½·ICI
IS(t+1) − IS(t) = Π(t) − Φ(t)
PFM(t) = Σ_ij R_i(t) · w_ij · exp(−δ·d_ij) / IS(t)
ΔISC(t) = −ρ·PFM(t)·ISC(t−1) + θ·IS(t) + ξ(t)
L(t+1) = L(t) + κ·[α·P(t) + β·N(t) − γ·C(t)]

Three families of cross-component terms close the loop. Symbolic resonance enters actor recalibration (β·R in MC) and frame updating (γ·R in CMG). Symbolic divergence is hypothesized to increase the crisis-production rate Π in the institutional equation, and fragmentation divides through institutional instability in PFM. 

Legitimacy collapse generates crisis events that re-enter Π and trigger recalibration. In the sequential reading of the Engine this gives the cycle MC → CMG → SRM → EEF → LDE → MC, with PFM and ISC mediating between the structural and symbolic layers. 

What distinguishes this from a list of models is that the cross terms carry parameters (β, γ, ρ, θ and the coupling coefficients of Π) that can be estimated and tested, and that the system as a whole generates predictions no single equation does.

 We say explicitly that the coupled system is a formalization at working-paper stage: its components are validated to very different degrees, as Table 1 shows, and the joint system has not yet been estimated end to end.
 
6. The Key Empirical Contribution
7. 
3.1 The symbol corpus and pipeline
   
The empirical anchor of the programme is the Social Resonance Model corpus. The primary dataset includes 22 symbol-periods drawn from 14 countries across five continents and the years 2013–2024. It covers political figures across the ideological spectrum (Trump, Modi, Mandela, Putin, Zelensky, Bolsonaro, Netanyahu, Duterte, Buhari, Macron, Orbán, Chávez, Erdoğan), civic movements (the Sunflower Movement), geopolitical events (Iran–Israel 2024), and flash-viral episodes (Charlie Hebdo, Georgescu, Simion). 

Later case studies extend it to Imran Khan 2018, Javier Milei 2023, Giorgia Meloni 2021–2024 and Kamala Harris 2024, bringing the working count to 24–25 depending on which analyses are included. 

It has a unique longitudinal series, three observations of the Modi symbol across a decade, and, to the author's knowledge, it is the largest cross-national symbol dataset of this kind assembled within a single reproducible pipeline.

Each symbol period is processed by the same chain. Article corpora of roughly 500 to 3,000 items are retrieved from Media Cloud; viral velocity V is a log-normalized escalation ratio, affective weight A is mean absolute VADER compound sentiment on titles (Hutto and Gilbert, 2014), and network coverage N is the share of days with at least one article. 
Semantic drift D is decomposed into polysemy entropy PE, the mean Jensen–Shannon divergence between LDA topic distributions with K = 10 (Blei et al., 2003), and intra-contextual incoherence ICI, one minus the mean pairwise cosine similarity of sentence embeddings of article titles (Reimers and Gurevych, 2019). 

The decay constant λ is solved numerically from the average-to-peak ratio of Google Trends series with Brent's method. 
The pipeline runs on public infrastructure, and every step is reproducible from the repository. 

Table 2 reports a representative subset.
Table 2. Selected symbol-periods from the SRM corpus (λ, ICI and D from the bootstrap n = 200 pipeline)

Symbol-period	λ	ICI	D	Typology

Modi, India 2014	2.37	0.904	0.747	CCFI, acute phase
Modi, India 2019	6.33	0.815	0.707	CCFI, partial decay
Modi, India 2024	9.11	0.849	0.726	CCFI, asymptote
Trump, US 2015–16	7.01	0.881	0.737	Western ICI ceiling
Sunflower Movement, Taiwan 2014	2.00	0.787	0.704	Civic mobilization
Putin, Russia 2022	4.90	0.753	0.650	Wartime aggressor
Macron, France 2017	12.53	0.729	0.666	Campaign
Netanyahu, Israel 2023–24	7.02	0.735	0.663	Pre-sorted wartime
Charlie Hebdo, France 2015	104.66	0.732	0.652	Extreme flash viral
Georgescu, Romania 2024	65.33	0.634	0.606	Flash viral
Orbán, Hungary 2022	2.31	0.592	0.597	Institutionally durable
Zelensky, Ukraine 2022	5.11	0.542	0.569	Wartime defender
Khan, Pakistan 2018	0.09	0.716	0.644	Electoral victory surge
Meloni, Italy 2021–24	0.21	0.161	0.567	Institutional anchor
Milei, Argentina 2023	6.14	0.637	0.747	Electoral burst boundary
Harris, US 2024	0.43	n/a	≈0.90	Persistent (VP baseline)

Values are as reported in the individual working papers. Corpus windows and sizes differ across cases, which affects ICI in particular (Section 3.3). Khan, Meloni, Milei and Harris were computed in later case studies with partly different data sources.
3.2 What the corpus supports

Three findings are best supported. First, framing contestation rather than topical breadth drives semantic drift: the range of ICI across the 22 symbol-periods (0.385) is 6.8 times the range of PE (0.057), and ICI correlates with D at r = 0.51 where PE does not. 
Second, Cross-Cultural Frame Incompatibility (CCFI) is detectable. 

Symbols from non-Western contexts that lack pre-established interpretive categories in Anglo-American media produce higher ICI than the Western ceiling of roughly 0.83 to 0.89; the Modi series shows the effect and its decay, with ICI falling from 0.904 in 2014 to 0.815 in 2019 and partially recovering to 0.849 in 2024. 

A Welch test of the CCFI group (n = 6) against the rest (n = 16) gives t = 2.17, p = 0.043, Cohen's d = 0.87, which is a large but small-sample effect. 
The Netanyahu case serves as a discriminating contrast: despite intense controversy, decades of settled Western frames keep its ICI in the moderate range. 
Third, the decay constant λ dominates resonance in a log-log regression, log R = 3.09 − 3.50·log λ + 1.57·log(V·A·N), with adjusted R² = 0.87 and leave-one-out R² = 0.770.

Other components have contributed smaller but real results. EEF discriminates joining from contested systems on a 20-year panel for Romania, Hungary and Poland, and tracks the V-Dem Liberal Democracy Index closely. CMG recovers a faster frame-update rate in the populist-receptive subpopulation than in the institutional-receptive one on Romanian data.
 PFM correctly flags the 2024 Romanian fragmentation spike once actors are selected by a three-criterion protocol that admits high-resonance outsiders. 
 
PFM-Survival, a random survival forest on early post-peak features, reaches a leave-one-out C-index of 0.854 on 18 symbols and has five genuinely prospective predictions pre-registered.

3.3 What it does not support, and why we say so

A founding document for a new discipline should tell its negative results as prominently as its positive ones, because the discipline's credibility depends on it. Four limits deserve emphasis.

The lambda result is partly built into the formula. Because R is defined with λ in the exponent, a strong association between λ and R is in part mechanical, and the leave-one-out figure of 0.770 should be read as describing the internal structure of the model on this sample rather than as independent predictive validation. 

The independent test is out-of-sample prediction of persistence, and there the result is negative: a cross-sectional leave-one-out evaluation on 15 symbols yields R² = −0.53 for the best model, a random forest, although it halves RMSE relative to the decay baseline, and the ordinary least squares alternative overfits badly (R² = −5.07 with 11 parameters on 15 observations). Early-stage survival features, as in PFM-Survival, are the more promising route to prediction.

Measurement is sensitive. ICI depends on corpus composition and window: bootstrap re-estimates differ from point estimates by up to 0.15 for some symbols (Georgescu, Chávez, Iran–Israel, Zelensky), explained by corpus size and temporal coverage rather than by resampling instability. 

A perturbation of ±0.05 in D moves resonance by about ±6% at λ = 2 but by about ±132% at λ = 65, so scores for flash-viral symbols are not point estimates. PE rises monotonically with the topic count K, which is harmless for comparison only because K = 10 is held fixed throughout.
The corpus is English-language and Western-hosted. Every article collection consists of English-language items from US national and international outlets. 

The corpus is therefore cross-cultural in its objects, since the symbols come from 14 countries, but not in its lens: it measures how Anglo-American media frame the world. CCFI is a finding about that lens. 

Establishing how symbols resonate in their own media ecosystems is the main reason for the expansion proposed below.
Several coupling-relevant tests came back negatively. The ISC hypothesis that coherent messaging predicts electoral support was not supported in panel fixed-effects models for Romania (63 party-quarters), and an earlier plain effect at p = 0.0002 was traced to a near-constant part that is collinear with the fixed effects.

 A parallel test of parliamentary speech coherence in Poland and Romania was also null. In PFM, the prediction that fragmentation propagates most strongly at intermediate structural distance was falsified (proximate pairs contributed 0.331 against 0.193 and 0.199), and the prediction that PFM(t) predicts EEF(t+1) was not supported at annual resolution (r between −0.01 and 0.04). For LDE, calibration on Eurobarometer series for Romania, Hungary and Poland was non-identifiable, a pattern consistent with a variance threshold of roughly sd(L) > 0.05, and a pre-registered Bulgaria–Portugal confirmatory test (OSF registration um6gp) returned a difference in R² of −0.2558, opposite to the predicted sign. 
 
These results have been published as working papers rather than withdrawn, and they shape the predictions in Section 4.
3.4 Extension to 40–50 symbols across three civilizational contexts
The planned extension has two aims: to raise the corpus from the current 24–25 symbol-periods to between 40 and 50, and to sample three civilizational contexts rather than one lens applied to many countries. 
The sampling frame will be fixed in a pre-registration before data collection, with symbol typologies balanced across contexts so that CCFI, institutional-anchor and flash-viral categories are not confounded with region. 
Each symbol will be collected twice where possible, once from the existing Anglo-American corpus and once from native-language media of its own context, using multilingual embeddings so that ICI is still comparable. 
This design allows the central CCFI claim to be tested properly: if incompatibility arises from the absence of interpretive categories in the observing media system, then the same symbol should show lower ICI in its home media than in Anglo-American coverage, and the gap should shrink with familiarity. 
The extension also lifts several current constraints at once, since a larger sample permits the Welch-type contrasts to be replaced by multilevel models with symbol and outlet effects, and allows the λ typology, currently defined by five categories with a sixth proposed for λ < 1, to be estimated rather than imposed.
9. Falsifiable Predictions
The coupling structure of Section 2 yields three system-level predictions that cannot be derived from any single part. 
Each is stated with an operationalization and with the outcome that would refute it. We deliberately build them from the coupling terms that survived testing in a form that can still be refuted, and we leave the ISC channel out of the prediction set because its direct hypothesis was not supported.
Prediction 1. Symbolic divergence raises institutional entropy production
When the dominant political symbols of a system carry high intra-contextual incoherence, the crisis-production rate Π(t) in the institutional equation should rise in the following period. 
Operationally, the mean ICI of the leading symbols in a country-period, measured at sub-annual resolution, should show a positive partial association with later Π(t) = max(0, ΔIS) after controlling for baseline IS, incumbency status and election timing. 
The prediction is refuted if the 95% bootstrap interval of the association includes zero or is negative in at least two of the three civilizational contexts once a minimum number of country-periods per context is reached. 
The existing evidence is only illustrative (Romania 2024, where Georgescu and Simion circulated while aggregate instability reached 84.7% of its maximum), and the PFM null at annual resolution is a warning that the test must be run at monthly or quarterly frequency.
Prediction 2. Legitimacy collapse triggers entropy production and strategic recalibration
Episodes in which legitimacy falls through a threshold should be followed within four quarters by a rise in Π(t) and by an increase in the recalibration rate α of the affected actors in MC, relative to matched control periods without collapse. 
The prediction is refuted if neither the entropy spike nor the recalibration increase appears against matched controls.
 Because LDE has proved non-identifiable on low-variance series and the confirmatory test reversed sign, this prediction can only be tested on episodes with sufficient within-series variance, which is itself a restriction the next version of LDE must formalize.
Prediction 3. Low collective consciousness amplifies polarization and legitimacy volatility
Systems whose mean consciousness C lies in the tribal range should show higher cognitive polarization POL(t), higher ICI per symbol, and more volatile legitimacy than systems with higher C, using education, trauma exposure and knowledge proxies from the World Values Survey and V-Dem. 
The prediction is refuted if POL, ICI and legitimacy volatility are unrelated or inversely related to C across a comparative panel. 
The Romanian CMG result, a faster frame-update rate in the populist-receptive bloc, is compatible with the mechanism but does not test the cross-national claim.
All three predictions are asymmetric by design. A confirmation would be informative but not decisive, whereas the stated refutation conditions are decisive for the coupling term concerned. A refutation does not discard the Engine; it removes or re-specifies one cross term, as happened with PFM's first prediction, which was falsified and reformulated into a proximity-driven typology of regimes.
10. The Open Research Agenda
For CPA to consolidate as a discipline rather than a single programme, five lines of work are needed over the next three to five years.
The first is the SRM expansion described in Section 3.4, together with a settled, versioned definition of the formula. 
Present papers use more than one specification (the original V·A·exp(−λD)·N and an optimized exp(−λ^0.20·D^3.00) form derived on 15 symbols), and the corpus numbering varies between 22 and 25 across documents. 
A frozen specification and a single consolidated dataset with a changelog are preconditions for external replication.
The second is estimating the couplings. At present the cross terms are specified but not jointly estimated. 
The practical route is staged: pairwise estimation of each coupling with pre-registered success criteria, then a reduced core with a small number of state variables fitted against V-Dem and comparable panels before the full seven-component system is attempted.
 A minimal three-variable core is the natural first step, since it allows identification questions to be settled before complexity is added.
The third is stability analysis. A coupled system invites questions that part models cannot pose: whether it has equilibria, whether feedback loops such as the proposed ratchet between coherence collapse and fragmentation produce cascades, and what parameter regions separate resilient from fragile regimes. 
This requires analytical work on the discrete-time system and simulation against historical episodes, and in the longer term a field-theoretic treatment in which coherence is a spatially distributed quantity.
The fourth is identification and measurement. LDE's variance threshold must be turned from an observation into a rule; ICI and D need cross-validation against human coding and against alternative embedding models, since an attempt to proxy D with an LLM-based estimate produced a correlation of −0.258 with expert values and is reported as a negative result; and the construct validity of ISC needs rebuilding on measures that vary within party, since its present components are near-constant.
The fifth is replication and prospective testing. Pre-registered prospective predictions already exist (PFM-Survival's five symbols, a pre-registered Romanian predictive protocol, a registered LDE confirmatory test), and the agenda is to make this the norm: every component should publish its prospective test before the data exist, report the outcome whatever it is, and invite independent teams to run the same pipeline on new cases.
11. Invitation
The programme is built to be checked by others. Code, data and pipelines are open: the repository at github.com/politomorphism contains the pipelines and, following earlier structural gaps, a validity kit with unit tests and canonical implementations of the formulas; the pre-registrations and working papers are archived under OSF DOI 10.17605/OSF.IO/HYDNZ; and the preprints are on SSRN. 
We invite four kinds of contribution: replications of existing symbol-periods with different corpora or windows; new symbol-periods, especially from non-Anglophone media ecosystems; independent attempts to refute the three predictions above; and critiques of the formalization, in particular of the coupling terms. 
Because the validation status of each part is stated in the open, a replication that fails is as welcome as one that succeeds and will be reported with the same prominence.
The claim of this paper is modest in one respect and ambitious in another. It does not claim that the Engine is confirmed; Table 1 shows that it is not. 
It claims that political anthropology and computational social science can share a formal object, that the object can be written down now, and that it can be put at risk of being wrong in public, which is the condition on which a field becomes a science.


References
Archer, M. S. (1995). Realist Social Theory: The Morphogenetic Approach. Cambridge University Press.
Blei, D. M., Ng, A. Y., & Jordan, M. I. (2003). Latent Dirichlet allocation. Journal of Machine Learning Research, 3, 993–1022.
Hutto, C. J., & Gilbert, E. (2014). VADER: A parsimonious rule-based model for sentiment analysis of social media text. Proceedings of ICWSM-14.
Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using Siamese BERT-networks. Proceedings of EMNLP-IJCNLP 2019.
Shannon, C. E. (1948). A mathematical theory of communication. Bell System Technical Journal, 27(3), 379–423.
Florin, Ș. G. (2026). Politomorphism and the Social Resonance Model: Quantifying political symbolic fragmentation across 22 symbol-periods. SSRN working paper; OSF DOI 10.17605/OSF.IO/HYDNZ.
Florin, Ș. G. (2026). Operationalizing semantic drift (D) in the Social Resonance Model. SSRN 6583879.
Florin, Ș. G. (2026). The Politomorphism Engine: Full empirical validation (bootstrap ICI, parametric optimization, Prophet forecasting). SSRN working paper.
Florin, Ș. G. (2026). Politomorphism: Clarifying intentional and emergent processes (Module 3.1). SSRN preprint.
Florin, Ș. G. (2026). The Politomorphism Engine: A five-component framework for computational political analysis. SSRN working paper.
Florin, Ș. G. (2026). Coupling SRM, EEF, and ISC: The adaptive layer of the Politomorphism Engine. OSF DOI 10.17605/OSF.IO/HYDNZ.
Florin, Ș. G. (2026). Measuring political systemic instability: The Entropic Equilibrium Function (EEF). SSRN working paper.
Florin, Ș. G. (2026). The Political Fragmentation Model (PFM): A formal theory of fragmentation propagation in political systems. SSRN working paper.
Florin, Ș. G. (2026). PFM-Survival: Pre-registered random survival forest prediction of political symbol attention decay. SSRN working paper.
Florin, Ș. G. (2026). Cognitive Morphogenesis (CMG): Modeling collective frame polarization. SSRN working paper.
Florin, Ș. G. (2026). Metapolitical Calibration (MC): Formalizing strategic adaptation. SSRN 6918918.
Florin, Ș. G. (2026). The Symbolic Coherence Index does not predict electoral support in Romania 2019–2024; Parliamentary speech coherence does not predict electoral support. Null-result working papers.
Florin, Ș. G. (2026). The Legitimacy Dynamics Engine: Preliminary calibration on Romania, Hungary and Poland; Cross-national calibration on Standard Eurobarometer data (2014–2025). Working papers.
Florin, Ș. G. (2026). Cross-cultural frame incompatibility: Modi 2014, 2019 and 2024; Imran Khan 2018; Milei 2023; Meloni 2021–2024; Harris 2024 and the VP baseline effect. SSRN working papers.


```
Serban, G.F. (2026). Politomorphism Engine: Computational Political Anthropology Framework.
GitHub: https://github.com/politomorphism/Politomorphism
ORCID: 0009-0000-2266-3356
SSRN: https://ssrn.com/author=6192814
OSF: https://doi.org/10.17605/OSF.IO/HYDNZ
```

---

License: CC BY 4.0 — All code and data open source.
