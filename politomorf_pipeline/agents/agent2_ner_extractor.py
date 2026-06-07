"""
Agent 2 — NER Extractor
Responsabilitati:
- Extrage entitati (partide, lideri, organizatii) din articole
- Foloseste spaCy ro_core_news_lg pentru NER avansat
- Fallback pe regex daca spaCy nu e disponibil
- Clasifica articolele pe partide si blocuri politice
- Salveaza date procesate in data/processed/
"""

import json, re, yaml
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime, timezone

def load_config():
    with open("config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)

def normalize(text):
    for k, v in {"ș":"s","ț":"t","ă":"a","â":"a","î":"i",
                  "Ș":"S","Ț":"T","Ă":"A","Â":"A","Î":"I"}.items():
        text = text.replace(k, v)
    return text

# ── NER ENGINE ────────────────────────────────────────────────────

class NERExtractor:
    def __init__(self, config):
        self.config  = config
        self.partide = list(config["partide"].keys())
        self.lideri  = config["lideri"]
        self.nlp     = None
        self._load_spacy()

    def _load_spacy(self):
        """Incearca sa incarce spaCy ro_core_news_lg."""
        try:
            import spacy
            self.nlp = spacy.load("ro_core_news_lg")
            print("  [NER] spaCy ro_core_news_lg incarcat.")
        except Exception:
            try:
                import spacy
                self.nlp = spacy.load("ro_core_news_sm")
                print("  [NER] spaCy ro_core_news_sm incarcat (fallback).")
            except Exception:
                print("  [NER] spaCy indisponibil — folosesc regex NER.")

    def extract_parties_spacy(self, text):
        """NER cu spaCy — extrage organizatii si verifica contra listei de partide."""
        if not self.nlp:
            return {}
        doc    = self.nlp(text[:100000])
        counts = Counter()
        for ent in doc.ents:
            if ent.label_ in ("ORG", "GPE", "PER"):
                for p in self.partide:
                    if p in ent.text.upper() or ent.text.upper() in p:
                        counts[p] += 1
        return dict(counts)

    def extract_parties_regex(self, text):
        """Regex NER — fallback robust."""
        counts = {}
        patterns = {
            "PSD":   [r"\bPSD\b", r"Social Democrat"],
            "PNL":   [r"\bPNL\b", r"National Liberal", r"Partidul National Liberal"],
            "USR":   [r"\bUSR\b", r"Salvati Romania"],
            "AUR":   [r"\bAUR\b", r"Unirea Romanilor", r"Alianta pentru Unirea"],
            "UDMR":  [r"\bUDMR\b", r"Maghiara", r"Uniunea Democrata"],
            "SOS":   [r"\bSOS\b", r"S\.O\.S\.", r"Sosoacu?a"],
            "POT":   [r"\bPOT\b", r"Oamenilor Tineri"],
            "REPER": [r"\bREPER\b", r"Forta Dreptei"],
        }
        for p, pats in patterns.items():
            cnt = sum(len(re.findall(pat, text, re.IGNORECASE)) for pat in pats)
            if cnt > 0:
                counts[p] = cnt
        return counts

    def extract_leaders(self, text):
        """Detecteaza lideri politici mentionati."""
        norm  = normalize(text.lower())
        found = []
        for leader, party in self.lideri.items():
            if normalize(leader.lower()) in norm:
                found.append({"name": leader, "party": party})
        return found

    def extract_topics(self, text):
        """Extrage teme politice din config."""
        norm   = normalize(text.lower())
        teme   = self.config.get("teme_politice", {})
        found  = []
        scores = {}
        for tema, keywords in teme.items():
            score = sum(norm.count(normalize(kw.lower())) for kw in keywords)
            if score > 0:
                found.append(tema)
                scores[tema] = score
        return found, scores

    def classify_article(self, article):
        """Clasifica un articol — combina spaCy + regex."""
        text = article.get("text", "")
        title = article.get("title", "")
        full  = f"{title} {text}"

        # Partide
        if self.nlp:
            parties_spacy = self.extract_parties_spacy(full)
            parties_regex = self.extract_parties_regex(full)
            # Combina: spaCy pentru confirmarea NER, regex pentru completitudine
            parties = {}
            all_parties = set(list(parties_spacy.keys()) + list(parties_regex.keys()))
            for p in all_parties:
                parties[p] = max(parties_spacy.get(p,0), parties_regex.get(p,0))
        else:
            parties = self.extract_parties_regex(full)

        leaders = self.extract_leaders(full)
        topics, topic_scores = self.extract_topics(full)

        # Detecteaza ABSA: propozitii specifice per partid
        party_sentences = {}
        sentences = re.split(r'[.!?]', full)
        for p, info in self.config["partide"].items():
            relevant = []
            for sent in sentences:
                if re.search(rf'\b{p}\b', sent, re.IGNORECASE):
                    relevant.append(sent.strip()[:200])
            if relevant:
                party_sentences[p] = relevant[:5]

        return {
            **article,
            "parties":         parties,
            "leaders":         leaders,
            "topics":          topics,
            "topic_scores":    topic_scores,
            "party_sentences": party_sentences,
        }

    def aggregate(self, classified_articles):
        """Agregate statistici per partid."""
        result = {}
        for p in self.partide:
            arts = [a for a in classified_articles if p in a["parties"]]
            if not arts:
                continue

            all_sentences = []
            for a in arts:
                all_sentences.extend(a.get("party_sentences",{}).get(p,[]))

            # Distribuie pe tip sursa
            source_dist = Counter(a.get("source_type","unknown") for a in arts)

            result[p] = {
                "article_count":    len(arts),
                "mentions_total":   sum(a["parties"][p] for a in arts),
                "bloc":             self.config["partide"][p]["bloc"],
                "gov":              self.config["partide"][p]["gov"],
                "grup_camera":      self.config["partide"][p]["grup_camera"],
                "source_dist":      dict(source_dist),
                "relevant_sentences": all_sentences[:20],  # pentru sentiment ABSA
                "sufficient_data":  len(arts) >= self.config["praguri"]["minim_articole_partid"],
                "articles":         [{"title":a["title"],"link":a["link"],
                                      "source_type":a["source_type"]} for a in arts],
            }
        return result

# ── TEME DOMINANTE ────────────────────────────────────────────────

def compute_teme_dominante(classified_articles, config):
    """Calculeaza top teme din toate articolele."""
    scores = Counter()
    for a in classified_articles:
        for tema, score in a.get("topic_scores",{}).items():
            scores[tema] += score
    return scores.most_common(10)

# ── MAIN ──────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print("[Agent 2] NER EXTRACTOR — pornit")
    config = load_config()

    with open("data/raw/ready_for_agent2.json", encoding="utf-8") as f:
        signal = json.load(f)
    ts = signal["timestamp"]

    with open(f"data/raw/articles_{ts}.json", encoding="utf-8") as f:
        articles = json.load(f)
    with open(f"data/raw/parliament_{ts}.json", encoding="utf-8") as f:
        parl_items = json.load(f)

    print(f"  Articole de procesat: {len(articles)}")

    extractor = NERExtractor(config)

    print("  Clasificare articole...")
    classified = [extractor.classify_article(a) for a in articles]

    print("  Agregare per partid...")
    party_data = extractor.aggregate(classified)

    print("  Calcul teme dominante...")
    teme = compute_teme_dominante(classified, config)

    # Statistici NER
    ner_stats = {
        "total_articles":    len(articles),
        "political_articles": len([a for a in classified if a["parties"]]),
        "parties_detected":  list(party_data.keys()),
        "teme_dominante":    teme,
        "spacy_available":   extractor.nlp is not None,
    }
    print(f"  NER stats: {ner_stats['political_articles']}/{ner_stats['total_articles']} articole cu partide")
    print(f"  Partide detectate: {ner_stats['parties_detected']}")
    print(f"  Top teme: {[t[0] for t in teme[:3]]}")

    Path("data/processed").mkdir(exist_ok=True)

    # Salveaza fara propozitiile detaliate (prea mare) — articolele merg separat
    party_data_slim = {
        p: {k:v for k,v in d.items() if k != "articles"}
        for p,d in party_data.items()
    }
    # Dar pastram relevant_sentences pentru Agent 3
    party_data_for_agent3 = party_data

    with open(f"data/processed/entities_{ts}.json","w",encoding="utf-8") as f:
        json.dump({
            "party_data":     party_data_for_agent3,
            "teme_dominante": teme,
            "ner_stats":      ner_stats,
            "parl_items":     parl_items,
        }, f, ensure_ascii=False, indent=2)

    with open("data/processed/ready_for_agent3.json","w",encoding="utf-8") as f:
        json.dump({"timestamp": ts}, f)

    print(f"[Agent 2] DONE — {len(party_data)} partide procesate")

if __name__ == "__main__":
    main()
