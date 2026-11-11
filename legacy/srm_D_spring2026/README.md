# Legacy D pipeline (spring 2026) — provenance archive

Archived 11 November 2026 by the author (Șerban, G. F.). These files were recovered from the author's computer; the repository history before 7 June 2026 ("clean restore") no longer exists, and no GitHub Actions runs older than 10 June 2026 are retained. They are archived **as found, unmodified** (hashes in `SHA256SUMS`). File dates on disk: scripts 19 March 2026 (`compute_V_A_N.py` 3 April 2026); results 3 April 2026.

Not archived: the downloaded Media Cloud corpora (e.g. `TRUMP-DATA.csv`), because redistribution of Media Cloud data may be restricted.

## What these files show (checked 11 November 2026)

1. **PE** is the mean Jensen–Shannon *distance* (SciPy `jensenshannon`), computed on **titles only** (`load_texts_from_csv` is called without a body column), with TF-IDF unigrams+bigrams, `min_df=1`, no lemmatization, no stop-word removal and no language filter. This differs from the text of SSRN 6583879, which specifies title + first paragraph, lemmatization and language checks.
2. **ICI** is 1 − mean of the full cosine matrix including the diagonal.
3. **Bootstrap intervals** resample documents within one fetched corpus (D ± 1.96·SD). They do not include variation between corpus fetches.
4. **alpha = 0.351** comes from `calibrate_alpha.py`, which fits alpha so that alpha·PE + (1−alpha)·ICI reproduces the legacy D values, using hand-entered *estimated* PE/ICI values (the qualitative estimates of SSRN 6583879, Table 2). Re-running the script reproduces 0.351 exactly. It has no empirical basis and is not used.
5. **test_hypotheses.py** was still set to estimated values (`real_values: False` for every case); any H1–H3 output it produced was based on estimates.
6. **compute_V_A_N.py** derives V from lambda by default, while SRM then uses lambda again in exp(−lambda·D); V is then not an independent measurement.
7. **The 18 result files do not match** the PE/ICI table published in “The Longevity Paradox …” (SRM_Orban_SSRN_2026_v2, March 2026) for any case, e.g. Putin PE/ICI 0.566/0.834 (paper) vs 0.619/0.646 (file); Zelensky 0.604/0.660 vs 0.596/0.542. Query strings, date windows and code versions were entered at dispatch time and were not saved, so the cause cannot be established. If the difference is due to re-fetching the corpus, between-fetch variation (up to 0.19 in ICI) is far larger than the reported bootstrap SD (about 0.0025).

Consequence: published PE/ICI values, typology rankings and confidence intervals from this pipeline should be treated as unreproduced. New measurements follow the analysis protocol (corpus fetched once and frozen by hash before any computation).
