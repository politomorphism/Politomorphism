#!/usr/bin/env python3
"""
UPLOAD_GITHUB.py
================
Uploadeaza datele ISC reale pe GitHub.
Ruleaza din folderul Desktop:
    python UPLOAD_GITHUB.py
"""

import subprocess, sys, shutil
from pathlib import Path

REPO = "https://github.com/profserbangabriel-del/Politomorphism.git"
FOLDER = Path("C:/Users/gabri/Desktop/Politomorphism")

# Clone daca nu exista
if not FOLDER.exists():
    print("Clonez repository-ul...")
    subprocess.run(["git","clone",REPO,str(FOLDER)], check=True)

# Creeaza folderul isc/data/
isc_data = FOLDER / "isc" / "data"
isc_data.mkdir(parents=True, exist_ok=True)

# Copiaza fisierele
files_to_copy = [
    (Path("C:/Users/gabri/Desktop/data/raw/psd_v2_2020.json"),
     isc_data / "psd_v2_2020_raw.json"),
]

# Cauta fisierele ISC real
for src_name in ["isc_psd_romania_2020_REAL.csv","isc_psd_romania_2020_REAL.json"]:
    for loc in [Path("C:/Users/gabri/Desktop"),
                Path("C:/Users/gabri/Downloads")]:
        src = loc / src_name
        if src.exists():
            files_to_copy.append((src, isc_data / src_name))
            break

for src, dst in files_to_copy:
    if src.exists():
        shutil.copy2(src, dst)
        print(f"Copiat: {dst.name}")
    else:
        print(f"Nu gasesc: {src}")

# README pentru folderul data
readme = isc_data / "README.md"
readme.write_text("""# ISC Data — PSD Romania 2020

## Dataset: isc_psd_romania_2020_REAL.csv

First real empirical data for the Symbolic Coherence Index (ISC).

| Field | Description |
|-------|-------------|
| country | Romania |
| quarter | 2020Q1-Q4 |
| actor | PSD |
| n_texts | Number of texts scraped from psd.ro |
| cmp_real | CMP calculated from real scraped texts |
| ci_estimated | CI estimated (pending: camera.ro vote data) |
| isc_final | ISC = 0.5*CMP + 0.5*CI |
| srm | Electoral polling / election results |
| srm_quality | verified / estimated / missing |

## Results

| Quarter | N | CMP | CI | ISC | SRM |
|---------|---|-----|----|-----|-----|
| 2020Q1 | 144 | 0.0827 | 0.952 | 0.5173 | 0.260 ✓ |
| 2020Q2 | 106 | 0.0611 | 0.936 | 0.4986 | N/A |
| 2020Q3 | 91 | 0.0566 | 0.926 | 0.4913 | N/A |
| 2020Q4 | 83 | 0.0352 | 0.906 | 0.4706 | 0.289 ✓ |

## Data Quality
- CMP: **real** (scraped from psd.ro, calendar indexing, 426 articles)
- CI: **estimated** (pending nominal vote data from camera.ro)
- SRM Q1: **verified** (CURS poll, 30 Jan 2020)
- SRM Q4: **verified** (BEC electoral result, 1 Dec 2020)

## Source
- Scraper: `scrape_psd_v2.py`
- Method: WordPress calendar indexing (psd.ro/2020/MM/)
- Schema: 5 frozen categories, keyword count
- Formula: ISC = 0.5 * CMP + 0.5 * CI (neutral prior, frozen)
""", encoding='utf-8')
print("README creat.")

# Git commit si push
import os
os.chdir(FOLDER)
subprocess.run(["git","add","isc/data/"], check=True)
subprocess.run(["git","commit","-m",
    "Add ISC real data v1.0 - PSD Romania 2020 (426 scraped articles, CMP real)"],
    check=True)
subprocess.run(["git","push"], check=True)

print()
print("="*50)
print("GATA. Datele sunt pe GitHub.")
print(f"https://github.com/profserbangabriel-del/Politomorphism")
input("Apasa Enter...")
