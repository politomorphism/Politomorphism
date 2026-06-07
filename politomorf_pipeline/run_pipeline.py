"""
Orchestrator — Politomorf Pipeline v4.0
Ruleaza cei 4 agenti secvential cu logging si error handling.
"""

import subprocess, sys, time, json
from pathlib import Path
from datetime import datetime, timezone

AGENTS = [
    ("agent1_collector.py",    "Colector RSS + Parliament"),
    ("agent2_ner_extractor.py","NER Extractor"),
    ("agent3_analysis.py",     "Analysis Engine"),
    ("agent4_report.py",       "Report Generator"),
]

def run_agent(script, label):
    print(f"\n{'='*55}")
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {label}")
    print(f"{'='*55}")
    start = time.time()
    result = subprocess.run(
        [sys.executable, f"agents/{script}"],
        capture_output=False,   # afiseaza output direct
        text=True,
    )
    elapsed = round(time.time()-start, 1)
    if result.returncode == 0:
        print(f"  ✅ {label} — {elapsed}s")
        return True
    else:
        print(f"  ❌ {label} ESUAT (cod {result.returncode}) dupa {elapsed}s")
        return False

def main():
    print("\n" + "="*55)
    print("POLITOMORF PIPELINE v4.0 — START")
    print(f"Data: {datetime.now(timezone.utc).isoformat()}")
    print("="*55)

    # Creeaza structura de foldere
    for d in ["data/raw","data/processed","data/reports"]:
        Path(d).mkdir(parents=True, exist_ok=True)

    start_total = time.time()
    for script, label in AGENTS:
        if not run_agent(script, label):
            print(f"\n❌ Pipeline oprit la {label}")
            sys.exit(1)

    total = round(time.time()-start_total, 1)
    print(f"\n{'='*55}")
    print(f"✅ PIPELINE COMPLET — {total}s")
    print("="*55)

if __name__ == "__main__":
    main()
