# Politomorphism Engine

**Serban Gabriel Florin** | ORCID: 0009-0000-2266-3356  
OSF: [10.17605/OSF.IO/HYDNZ](https://doi.org/10.17605/OSF.IO/HYDNZ) | SSRN: [ssrn.com/author=6192814](https://ssrn.com/author=6192814)

---

## Instalare și rulare rapidă

```bash
# 1. Clonează
git clone https://github.com/politomorphing/politomorphism-engine.git
cd politomorphism-engine

# 2. Instalează dependențe
pip install -r requirements.txt

# 3. Colectează date reale (RSS + calcule automate)
python data_collector.py

# 4. Rulează calibrarea MC
python mc_run.py
```

Outputurile apar în `outputs/`.

---

## Structura repository

```
politomorphism-engine/
│
├── components/
│   └── mc_component.py        # MC — Metapolitical Calibration (clasa core)
│
├── data/
│   ├── real/                  # CSV-uri generate de data_collector.py
│   │   ├── sentiment_topics.csv
│   │   ├── srm_scores.csv
│   │   └── polling.csv
│   └── synthetic/             # Date de test generate automat
│
├── outputs/                   # Grafice și rezultate calibrare
│
├── data_collector.py          # Colectare RSS + calcul I(t) + SRM proxy
├── mc_run.py                  # Calibrare MC pe date reale
└── requirements.txt
```

---

## Componente implementate

| Componentă | Status | Fișier |
|------------|--------|--------|
| MC — Metapolitical Calibration | ✅ Implementat | `components/mc_component.py` |
| CMG — Cognitive Morphogenesis | 🔄 În lucru | — |
| SRM — Social Resonance Model | ✅ Validat (25 simboluri) | — |
| EEF — Entropic Equilibrium Function | ✅ Validat | — |
| PFM — Political Fragmentation Model | ✅ Publicat | — |
| ISC — Symbolic Coherence Index | ✅ Publicat | — |
| LDE — Legitimacy Dynamics Engine | 🔄 Validare parțială | — |

---

## Ecuația MC

```
S(t+1) = (1 - α) · S(t) + α · W · I(t) + β · SRM(t-1) + ε_MC(t)
```

**β hypothesis testabilă:**  
Actorii populiști (AUR, Georgescu) au `β` semnificativ mai mare decât actorii instituționali (PNL, PSD) — își recalibrează discursul mai agresiv pe baza rezonanței simbolice anterioare.

---

## Licență

CC BY 4.0 — Cod și date open source.
