# Politomorphism — Social Resonance Model (SRM)

**Serban Gabriel Florin** | Independent Researcher  
ORCID: [0009-0000-2266-3356](https://orcid.org/0009-0000-2266-3356) | DOI: [10.17605/OSF.IO/HYDNZ](https://doi.org/10.17605/OSF.IO/HYDNZ)  
GitHub: [profserbangabriel-del/politomorphism](https://github.com/profserbangabriel-del/politomorphism)

---

## Ce este Politomorphism?

Politomorphism este un cadru teoretic care tratează simbolurile politice ca **agenți morfogenetici** — entități care transformă structurile de putere prin difuzie simbolică. Componenta sa computațională, **Social Resonance Model (SRM)**, furnizează o măsură cantitativă a acestui fenomen.

## Formula SRM

**SRM = V × A × e^(−λD) × N** (λ = 2)

| Variabilă | Nume | Definiție |
|-----------|------|-----------|
| V | Viral Velocity | Rata de difuzie a simbolului (raport de escaladare log-normalizat) |
| A | Affective Weight | Intensitatea emoțională (analiza de sentiment VADER) |
| D | Semantic Drift | Fragmentarea semantică (0=stabil, 1=complet fragmentat) |
| N | Network Coverage | Proporția zilelor/surselor în care simbolul este prezent |

**Interpretare scoruri:**
- SRM ≥ 0.20 → HIGH RESONANCE
- 0.07 ≤ SRM < 0.20 → MEDIUM RESONANCE
- 0.02 ≤ SRM < 0.07 → LOW RESONANCE
- SRM < 0.02 → MINIMAL RESONANCE

---

## Dataset comparativ — 5 simboluri validate

| Simbol / Context | V | A | D | N | **SRM** | Interpretare |
|-----------------|---|---|---|---|---------|--------------|
| Sunflower Mvt (TW, 2014) | 0.680 | 0.420 | 0.7737 | 0.580 | 0.0352 | Low |
| Călin Georgescu (RO, 2024) | 0.750 | 0.398 | 0.8813 | 0.600 | 0.0307 | Low |
| Marcel Ciolacu (RO, 2025-26) | 0.720 | 0.420 | 0.8412 | 0.650 | 0.0365 | Low |
| Donald Trump (US, 2015-16) | 0.958 | 0.580 | 0.7340 | 0.720 | 0.0922 | **Medium** |
| **Zelensky (UA/EU/US, 2022-26)** | **0.873** | **0.640** | **0.680** | **0.781** | **0.1121** | **Medium** |

> **Pattern consistent:** Semantic Drift (D) este variabila diferențiatoare principală. D mai mic → SRM mai mare, indiferent de vizibilitate.

---

## Validări — detalii

### Validarea 1 — Sunflower Movement (Taiwan, 2014)
| V | A | D | N | **SRM** | Interpretare |
|---|---|---|---|---------|--------------|
| 0.680 | 0.420 | 0.7737 | 0.580 | **0.0352** | LOW RESONANCE |

---

### Validarea 2 — Călin Georgescu (România, Oct–Dec 2024)
| V | A | D | N | **SRM** | Interpretare |
|---|---|---|---|---------|--------------|
| 0.750 | 0.398 | 0.8813 | 0.600 | **0.0307** | LOW RESONANCE |

Rezultate: [SRM_raport_final.json](SRM_raport_final.json) | Grafic: [SRM_grafic_final.png](SRM_grafic_final.png)

---

### Validarea 3 — Marcel Ciolacu (România, Dec 2025 – Mar 2026)
Date: Media Cloud Romania National + State & Local | 539 articole, 50 surse, 91 zile

| V | A | D | N | **SRM** | Interpretare |
|---|---|---|---|---------|--------------|
| 0.720 | 0.420 | 0.8412 | 0.650 | **0.0365** | LOW RESONANCE |

**Finding principal — Paradoxul Rezonanței:** Vizibilitate ridicată (V=0.72, N=0.65), rezonanță scăzută din cauza derivei semantice extreme (D=0.8412). Șase cadre semantice concurente: critic al opoziției, fost premier responsabil de criză, administrator local, lider PSD, țintă judiciară, strateg electoral.

**Categorie nouă diagnostică:** *Post-Executive Symbolic Trap* — tranziția premier → opoziție generează structural fragmentare semantică maximă.

Paper: [SRM_Ciolacu_Validation.docx](SRM_Ciolacu_Validation.docx) | Date: [data_ciolacu/](data_ciolacu/)

---

### Validarea 4 — Donald Trump (SUA, Feb 2015 – Nov 2016)
Date: Media Cloud US National + State & Local | 640 observații zilnice

| V | A | D | N | **SRM** | Interpretare |
|---|---|---|---|---------|--------------|
| 0.958 | 0.580 | 0.7340 | 0.720 | **0.0922** | MEDIUM RESONANCE |

**Finding principal:** Primul caz de Medium Resonance confirmat. V=0.958 — escaladare 82.3x față de baseline. D=0.734 — suficient de coerent pentru mobilizare electorală de succes.

Rezultate: [SRM_trump_result.json](SRM_trump_result.json) | Grafic: [SRM_trump_grafic.png](SRM_trump_grafic.png)

---

### Validarea 5 — Volodymyr Zelensky (UA/EU/US, Mai 2022 – Feb 2026)
Date: Media Cloud US National + Europe | 2,387 observații zilnice

| V | A | D | N | **SRM** | Interpretare |
|---|---|---|---|---------|--------------|
| 0.873 | 0.640 | 0.680 | 0.781 | **0.1121** | MEDIUM RESONANCE |

**Finding principal:** Cel mai înalt scor SRM din dataset. Escaladare 123.6x în media US față de baseline pre-invazie (mai 2019 – feb 2022). Peak: **28 feb – 4 mar 2025** (întâlnirea Zelensky–Trump la Casa Albă). D=0.680 — cel mai mic din dataset, reflectând dominanța cadrului „lider al rezistenței".

Paper: [SRM_Zelensky_Validation.docx](SRM_Zelensky_Validation.docx) | Rezultate: [SRM_zelensky_result.json](SRM_zelensky_result.json) | Date: [data_zelensky/](data_zelensky/)

---

## Structura repository-ului

```
politomorphism/
├── .github/workflows/
│   ├── srm_zelensky_validation.yml
│   └── srm_sunflower_validation.yml
├── data_zelensky/
│   ├── counts_zelensky_first_period.csv
│   ├── counts_zelensky_second_period.csv
│   ├── counts_zelensky_usa.csv
│   └── counts_zelensky_europe.csv
├── data_ciolacu/
├── data_sunflower/
├── SRM_Zelensky_Validation.docx
├── SRM_Ciolacu_Validation.docx
├── SRM_zelensky_result.json
├── SRM_trump_result.json
├── SRM_raport_final.json
└── index.html
```

---

## Reproducibilitate

Toate datele, codul și rezultatele sunt open-source și public disponibile.  
Sursa date: [mediacloud.org](https://mediacloud.org)  
Licență: CC BY 4.0
