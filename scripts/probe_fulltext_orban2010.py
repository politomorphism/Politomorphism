#!/usr/bin/env python3
"""Feasibility probe: can title + first paragraph be obtained for the 270 Orban-2010 items?
Route A: Media Cloud SearchApi.story(id) text. Route B: direct URL fetch + trafilatura.
Writes only coverage counts and per-route status (no article text is committed)."""
import json, os, time
import pandas as pd

df = pd.read_csv("data/orban2010_content.csv")
df = df[df["title"].astype(str).str.strip().str.len() > 10].reset_index(drop=True)
out = {"n_items": len(df), "routeA_mediacloud": {}, "routeB_url": {}}

key = os.environ.get("MEDIACLOUD_API_KEY", "")
if key:
    import mediacloud.api as mc
    s = mc.SearchApi(key); ok = 0; err = {}; lens = []
    for sid in df["id"].head(30):
        try:
            st = s.story(sid); txt = (st or {}).get("text") or ""
            if len(txt) > 50: ok += 1; lens.append(len(txt))
            else: err["no_text"] = err.get("no_text", 0) + 1
        except Exception as e:
            k = type(e).__name__ + ":" + str(e)[:80]; err[k] = err.get(k, 0) + 1
        time.sleep(0.5)
    out["routeA_mediacloud"] = {"tested": 30, "with_text": ok, "errors": err,
                                "median_len": sorted(lens)[len(lens)//2] if lens else None}
else:
    out["routeA_mediacloud"] = {"status": "MEDIACLOUD_API_KEY not set"}

import requests, trafilatura
ok = 0; status = {}; par_ok = 0
for u in df["url"]:
    try:
        r = requests.get(u, timeout=12, headers={"User-Agent": "Mozilla/5.0 (research reproducibility probe)"})
        k = f"http_{r.status_code}"
        if r.status_code == 200:
            t = trafilatura.extract(r.text) or ""
            paras = [p for p in t.split("\n") if len(p.strip()) > 80]
            if paras: par_ok += 1; k = "200_with_paragraph"
            else: k = "200_no_paragraph"
    except Exception as e:
        k = type(e).__name__
    status[k] = status.get(k, 0) + 1
out["routeB_url"] = {"tested": len(df), "with_first_paragraph": par_ok, "status_counts": status}
os.makedirs("disinformation_paper/orban2010_data", exist_ok=True)
json.dump(out, open("disinformation_paper/orban2010_data/fulltext_probe.json", "w"), indent=2)
print(json.dumps(out, indent=1))
