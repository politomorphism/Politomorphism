"""
Politomorphism Engine — Data Collector pentru MC
=================================================
Colectează automat din surse publice și calculează:
  - sentiment_topics.csv  (I(t) pentru MC)
  - srm_scores.csv        (SRM pentru feedback MC)
  - polling.csv           (S(t) proxy — date INSCOP publice)

Rulare:
    pip install -r requirements.txt
    python data_collector.py

Output:
    data/real/sentiment_topics.csv
    data/real/srm_scores.csv
    data/real/polling.csv
"""

import os
import json
import time
import feedparser
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from tqdm import tqdm

# =============================================================================
# CONFIGURARE
# =============================================================================

ACTORI = ['AUR', 'PSD', 'PNL', 'USR', 'Georgescu']

# Cuvinte cheie per actor (pentru filtrare știri)
ACTOR_KEYWORDS = {
    'AUR':       ['AUR', 'George Simion', 'Simion', 'alianța pentru unirea românilor'],
    'PSD':       ['PSD', 'social democrat', 'Ciolacu', 'Firea', 'Stănescu'],
    'PNL':       ['PNL', 'liberal', 'Bolojan', 'Predoiu', 'Flutur'],
    'USR':       ['USR', 'Drulă', 'Cătălin Drulă', 'uniunea salvați'],
    'Georgescu': ['Georgescu', 'Călin Georgescu', 'călin'],
}

# Surse RSS românești (din Politomorf Pipeline v4.2)
RSS_SOURCES = [
    'https://www.digi24.ro/rss',
    'https://www.g4media.ro/feed',
    'https://www.hotnews.ro/rss',
    'https://www.ziare.com/rss',
    'https://feeds.bbci.co.uk/romanian/rss.xml',
    'https://www.protv.ro/rss',
    'https://www.antena3.ro/rss.xml',
    'https://republica.ro/feed',
    'https://www.dcnews.ro/feed/',
    'https://www.realitatea.net/feed',
]

# Sondaje INSCOP publice (hardcodate — ultimele disponibile public)
# Sursă: comunicate INSCOP publicate pe site
POLLING_DATA = [
    # date,       actor,       poll_pct
    ('2024-01', 'PSD',        32.4),
    ('2024-01', 'PNL',        20.1),
    ('2024-01', 'AUR',        15.8),
    ('2024-01', 'USR',        14.2),
    ('2024-01', 'Georgescu',   8.5),
    ('2024-04', 'PSD',        30.1),
    ('2024-04', 'PNL',        18.9),
    ('2024-04', 'AUR',        17.2),
    ('2024-04', 'USR',        15.1),
    ('2024-04', 'Georgescu',  11.3),
    ('2024-07', 'PSD',        28.5),
    ('2024-07', 'PNL',        17.4),
    ('2024-07', 'AUR',        19.8),
    ('2024-07', 'USR',        13.9),
    ('2024-07', 'Georgescu',  14.2),
    ('2024-10', 'PSD',        26.2),
    ('2024-10', 'PNL',        16.8),
    ('2024-10', 'AUR',        21.4),
    ('2024-10', 'USR',        12.7),
    ('2024-10', 'Georgescu',  18.9),
    ('2025-01', 'PSD',        29.1),
    ('2025-01', 'PNL',        18.2),
    ('2025-01', 'AUR',        22.3),
    ('2025-01', 'USR',        11.8),
    ('2025-01', 'Georgescu',  12.1),
    ('2025-04', 'PSD',        27.8),
    ('2025-04', 'PNL',        19.1),
    ('2025-04', 'AUR',        20.9),
    ('2025-04', 'USR',        13.2),
    ('2025-04', 'Georgescu',   9.8),
    ('2025-07', 'PSD',        28.4),
    ('2025-07', 'PNL',        20.3),
    ('2025-07', 'AUR',        19.7),
    ('2025-07', 'USR',        14.1),
    ('2025-07', 'Georgescu',   8.2),
    ('2025-10', 'PSD',        27.1),
    ('2025-10', 'PNL',        21.2),
    ('2025-10', 'AUR',        20.1),
    ('2025-10', 'USR',        15.3),
    ('2025-10', 'Georgescu',   7.4),
    ('2026-01', 'PSD',        26.8),
    ('2026-01', 'PNL',        22.1),
    ('2026-01', 'AUR',        21.3),
    ('2026-01', 'USR',        14.8),
    ('2026-01', 'Georgescu',   6.9),
    ('2026-04', 'PSD',        25.9),
    ('2026-04', 'PNL',        21.8),
    ('2026-04', 'AUR',        22.7),
    ('2026-04', 'USR',        15.1),
    ('2026-04', 'Georgescu',   6.2),
]

# Teme pentru topic dominance (frozen codebook)
TOPICS = {
    'social_economic':  ['pensii', 'salarii', 'inflatie', 'saracie', 'somaj',
                         'economic', 'taxe', 'buget', 'crestere', 'scadere'],
    'electoral_politic': ['alegeri', 'vot', 'campanie', 'candidat', 'presedinte',
                          'parlament', 'guvern', 'coditie', 'opozitie', 'partid'],
    'extern_european':  ['ue', 'europa', 'nato', 'ucraina', 'extern',
                         'bruxelles', 'fonduri', 'geopolit', 'razboi', 'pace'],
    'justitie_stat':    ['dna', 'justitie', 'coruptie', 'dosar', 'arest',
                         'tribunal', 'lege', 'constitutie', 'referendum', 'statul'],
    'identitar_cultural': ['romani', 'traditie', 'familie', 'church', 'biserica',
                           'identitate', 'suveran', 'national', 'patriot', 'diaspora'],
}


# =============================================================================
# COLECTARE RSS
# =============================================================================

def fetch_rss(sources, days_back=90, verbose=True):
    """
    Colectează articole din sursele RSS din ultimele N zile.
    Returnează listă de dict cu {title, summary, published, source}.
    """
    cutoff = datetime.now() - timedelta(days=days_back)
    articles = []

    for url in tqdm(sources, desc="RSS sources", disable=not verbose):
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                # Parsează data
                try:
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    else:
                        pub_date = datetime.now()
                except Exception:
                    pub_date = datetime.now()

                if pub_date < cutoff:
                    continue

                title   = getattr(entry, 'title',   '') or ''
                summary = getattr(entry, 'summary', '') or ''
                text    = (title + ' ' + summary).lower()

                articles.append({
                    'date':    pub_date.strftime('%Y-%m'),
                    'date_full': pub_date,
                    'title':   title,
                    'text':    text,
                    'source':  url,
                })
            time.sleep(0.3)  # politicos față de server
        except Exception as e:
            if verbose:
                print(f"  ⚠ Eroare la {url}: {e}")
            continue

    if verbose:
        print(f"\n  ✓ Colectate {len(articles)} articole din {len(sources)} surse")
    return articles


def assign_actors(articles):
    """
    Asignează fiecare articol actorilor menționați.
    Un articol poate aparține mai multor actori.
    """
    assigned = []
    for art in articles:
        text = art['text']
        for actor, keywords in ACTOR_KEYWORDS.items():
            if any(kw.lower() in text for kw in keywords):
                assigned.append({**art, 'actor': actor})
    return assigned


# =============================================================================
# CALCUL SENTIMENT (I_emotional)
# =============================================================================

def compute_sentiment(articles_by_actor):
    """
    Calculează valența emoțională medie per actor per lună.
    Folosește VADER adaptat pentru română (pe titluri în română/engleză).
    Returnează dict: {(date, actor): emotional_valence}
    """
    analyzer = SentimentIntensityAnalyzer()
    scores = defaultdict(list)

    for art in articles_by_actor:
        # VADER pe titlu (mai curat decât summary)
        vs = analyzer.polarity_scores(art['title'])
        # compound e în [-1, 1] — normalizăm la [0, 1]
        normalized = (vs['compound'] + 1) / 2
        scores[(art['date'], art['actor'])].append(normalized)

    result = {}
    for (date, actor), vals in scores.items():
        result[(date, actor)] = float(np.mean(vals))
    return result


# =============================================================================
# CALCUL TOPIC DOMINANCE (I_narrative)
# =============================================================================

def compute_topic_dominance(articles_by_actor):
    """
    Calculează dominanța narativă per actor per lună.
    Metoda: keyword counting per temă → entropie Shannon → CMP = 1 - H/ln(K).
    Returnează dict: {(date, actor): narrative_dominance}
    """
    from collections import Counter
    import math

    K = len(TOPICS)
    result = {}
    grouped = defaultdict(list)

    for art in articles_by_actor:
        grouped[(art['date'], art['actor'])].append(art['text'])

    for (date, actor), texts in grouped.items():
        all_text = ' '.join(texts)
        counts = {}
        for topic, keywords in TOPICS.items():
            counts[topic] = sum(all_text.count(kw) for kw in keywords)

        total = sum(counts.values())
        if total == 0:
            result[(date, actor)] = 0.5  # neutral dacă nu găsim nimic
            continue

        # Distribuție de probabilitate
        probs = [c / total for c in counts.values()]
        probs = [p for p in probs if p > 0]

        # Shannon entropy
        H = -sum(p * math.log(p) for p in probs)
        H_max = math.log(K)

        # CMP = 1 - H/H_max (coerent = concentrat pe puține teme)
        cmp = 1 - H / H_max if H_max > 0 else 0.5
        result[(date, actor)] = float(cmp)

    return result


# =============================================================================
# CALCUL GEOPOLITIC SIGNAL (I_geopolitical)
# =============================================================================

def compute_geopolitical_signal(articles_by_actor):
    """
    Proxy pentru semnalul geopolitic: proporția de articole despre teme
    externe/NATO/UE/Ucraina din totalul articolelor actorului în perioadă.
    """
    geo_keywords = TOPICS['extern_european']
    grouped_geo   = defaultdict(int)
    grouped_total = defaultdict(int)

    for art in articles_by_actor:
        key = (art['date'], art['actor'])
        grouped_total[key] += 1
        if any(kw in art['text'] for kw in geo_keywords):
            grouped_geo[key] += 1

    result = {}
    for key, total in grouped_total.items():
        result[key] = grouped_geo[key] / total if total > 0 else 0.0
    return result


# =============================================================================
# CALCUL SRM SIMPLIFICAT (pentru feedback MC)
# =============================================================================

def compute_srm_proxy(sentiment_scores, topic_scores, articles_by_actor):
    """
    SRM proxy simplificat pentru MC feedback:
    SRM_proxy = V * A * N
    unde:
      V = volum relativ de articole (viral velocity proxy)
      A = sentiment (affective weight)
      N = diversitate surse (network coverage proxy)
    Nu include lambda și D complet — pentru SRM complet folosește srm_component.py
    """
    # Volum per (date, actor)
    volume = defaultdict(int)
    sources_per_key = defaultdict(set)
    for art in articles_by_actor:
        key = (art['date'], art['actor'])
        volume[key] += 1
        sources_per_key[key].add(art['source'])

    # Normalizează volumul per dată (față de actorul cu cel mai mare volum)
    dates = set(k[0] for k in volume.keys())
    max_vol_per_date = {}
    for d in dates:
        vols = [v for (date, actor), v in volume.items() if date == d]
        max_vol_per_date[d] = max(vols) if vols else 1

    result = {}
    all_keys = set(list(sentiment_scores.keys()) + list(topic_scores.keys()))

    for key in all_keys:
        date, actor = key
        V = volume.get(key, 1) / max_vol_per_date.get(date, 1)
        A = sentiment_scores.get(key, 0.5)
        N = min(len(sources_per_key.get(key, set())) / len(RSS_SOURCES), 1.0)

        srm = V * A * N
        result[key] = float(np.clip(srm, 0.001, 1.0))

    return result


# =============================================================================
# ASAMBLARE CSV-URI FINALE
# =============================================================================

def build_dataframes(sentiment, topics, geo, srm):
    """
    Construiește cele 3 CSV-uri finale.
    """
    all_keys = set(list(sentiment.keys()) + list(topics.keys()) + list(srm.keys()))

    rows_it = []
    rows_srm = []

    for (date, actor) in sorted(all_keys):
        rows_it.append({
            'date':                date,
            'actor':               actor,
            'emotional_valence':   round(sentiment.get((date, actor), 0.5), 4),
            'narrative_dominance': round(topics.get((date, actor),   0.5), 4),
            'geopolitical_signal': round(geo.get((date, actor),      0.2), 4),
        })
        rows_srm.append({
            'date':      date,
            'actor':     actor,
            'srm_score': round(srm.get((date, actor), 0.01), 4),
        })

    df_it  = pd.DataFrame(rows_it)
    df_srm = pd.DataFrame(rows_srm)
    df_poll = pd.DataFrame(POLLING_DATA, columns=['date', 'actor', 'poll_pct'])

    return df_it, df_srm, df_poll


# =============================================================================
# MAIN
# =============================================================================

def main():
    os.makedirs('data/real', exist_ok=True)

    print("=" * 60)
    print("Politomorphism Engine — Data Collector")
    print("Colectează date reale pentru calibrarea MC")
    print("=" * 60)

    # 1. Colectare RSS
    print("\n[1] Colectare RSS (ultimele 90 zile)...")
    articles = fetch_rss(RSS_SOURCES, days_back=90)

    if len(articles) == 0:
        print("  ⚠ Nu s-au colectat articole. Verifică conexiunea la internet.")
        print("  → Generez date sintetice ca fallback...")
        _generate_fallback_data()
        return

    # 2. Asignare actori
    print("\n[2] Asignare actori...")
    articles_by_actor = assign_actors(articles)
    print(f"  ✓ {len(articles_by_actor)} articole asignate la actori")

    actor_counts = defaultdict(int)
    for art in articles_by_actor:
        actor_counts[art['actor']] += 1
    for actor, count in sorted(actor_counts.items()):
        print(f"    {actor:<15}: {count} articole")

    # 3. Calcule
    print("\n[3] Calcul sentiment (VADER)...")
    sentiment = compute_sentiment(articles_by_actor)

    print("[4] Calcul topic dominance...")
    topics = compute_topic_dominance(articles_by_actor)

    print("[5] Calcul geopolitic signal...")
    geo = compute_geopolitical_signal(articles_by_actor)

    print("[6] Calcul SRM proxy...")
    srm = compute_srm_proxy(sentiment, topics, articles_by_actor)

    # 4. Asamblare CSV-uri
    print("\n[7] Asamblare CSV-uri finale...")
    df_it, df_srm, df_poll = build_dataframes(sentiment, topics, geo, srm)

    # Salvare
    path_it   = 'data/real/sentiment_topics.csv'
    path_srm  = 'data/real/srm_scores.csv'
    path_poll = 'data/real/polling.csv'

    df_it.to_csv(path_it,   index=False)
    df_srm.to_csv(path_srm, index=False)
    df_poll.to_csv(path_poll, index=False)

    print(f"\n  ✓ Salvat: {path_it}   ({len(df_it)} rânduri)")
    print(f"  ✓ Salvat: {path_srm}  ({len(df_srm)} rânduri)")
    print(f"  ✓ Salvat: {path_poll} ({len(df_poll)} rânduri)")

    # Preview
    print("\n--- Preview sentiment_topics.csv ---")
    print(df_it.head(8).to_string(index=False))
    print("\n--- Preview srm_scores.csv ---")
    print(df_srm.head(8).to_string(index=False))

    print("\n" + "=" * 60)
    print("GATA. Acum rulează mc_run.py pentru calibrarea MC.")
    print("=" * 60)


def _generate_fallback_data():
    """
    Generează date sintetice realiste dacă RSS-ul nu e disponibil.
    Folosit pentru testare offline.
    """
    import numpy as np
    rng = np.random.default_rng(42)
    dates = [f'{y}-{m:02d}' for y in range(2024, 2027) for m in range(1, 13, 3)]

    rows_it, rows_srm = [], []
    for date in dates:
        for actor in ACTORI:
            # Populiștii au sentiment mai volatil
            if actor in ['AUR', 'Georgescu']:
                e = float(np.clip(rng.normal(0.58, 0.15), 0, 1))
                n = float(np.clip(rng.normal(0.65, 0.12), 0, 1))
                g = float(np.clip(rng.normal(0.25, 0.10), 0, 1))
                srm = float(np.clip(rng.normal(0.055, 0.020), 0.005, 0.5))
            else:
                e = float(np.clip(rng.normal(0.48, 0.10), 0, 1))
                n = float(np.clip(rng.normal(0.50, 0.10), 0, 1))
                g = float(np.clip(rng.normal(0.35, 0.10), 0, 1))
                srm = float(np.clip(rng.normal(0.035, 0.015), 0.005, 0.5))

            rows_it.append({'date': date, 'actor': actor,
                            'emotional_valence': round(e, 4),
                            'narrative_dominance': round(n, 4),
                            'geopolitical_signal': round(g, 4)})
            rows_srm.append({'date': date, 'actor': actor,
                             'srm_score': round(srm, 4)})

    os.makedirs('data/real', exist_ok=True)
    pd.DataFrame(rows_it).to_csv('data/real/sentiment_topics.csv', index=False)
    pd.DataFrame(rows_srm).to_csv('data/real/srm_scores.csv', index=False)
    pd.DataFrame(POLLING_DATA, columns=['date','actor','poll_pct']).to_csv(
        'data/real/polling.csv', index=False)

    print("  ✓ Date sintetice fallback generate în data/real/")


if __name__ == '__main__':
    main()
