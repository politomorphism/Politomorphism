"""
Agent 3 — Analysis Engine v2
- Sentiment ABSA corelat direct cu entitati din Agent 2
- RoBERT-RO daca disponibil, lexicon ponderat fallback
- Algoritm disidenta complet (3 componente + ponderare)
- Bootstrap CI 95%
- SRM/ISC/EEF documentat matematic
"""

import json, re, yaml, math, csv
import numpy as np
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

# ── SENTIMENT ENGINE ──────────────────────────────────────────────

class SentimentEngine:
    POS = {"crestere":1.5,"succes":1.8,"victorie":2.0,"reform":1.2,"progres":1.5,
           "investitie":1.3,"dezvoltare":1.4,"realizare":1.6,"sprijin":1.2,
           "solutie":1.4,"acord":1.3,"transparenta":1.5,"eficient":1.3,"stabil":1.2,
           "castig":1.7,"aprobare":1.4,"sustinere":1.2,"pozitiv":1.0,"bun":0.8,
           "excelent":1.9,"colaborare":1.1,"constructiv":1.2,"dialog":1.0}
    NEG = {"coruptie":-2.0,"scandal":-1.8,"criza":-1.5,"esec":-1.7,"protest":-1.2,
           "demisie":-1.4,"acuzatie":-1.6,"dosar":-1.5,"arest":-1.9,"condamnat":-2.0,
           "frauda":-1.9,"abuz":-1.7,"incompetenta":-1.6,"dezastru":-1.9,
           "conflict":-1.4,"blocaj":-1.3,"infractiune":-1.8,"penali":-1.7,
           "ilegal":-1.8,"respins":-1.2,"tensiune":-1.1,"radicalizare":-1.6,
           "haos":-1.7,"negativ":-1.0,"rau":-1.2,"prost":-1.1,"corupt":-1.9}

    def __init__(self):
        self.bert = None
        try:
            from transformers import pipeline as hp
            self.bert = hp("sentiment-analysis",
                           model="readerbench/ro-bert-base",
                           max_length=512, truncation=True)
            print("  [Sentiment] RoBERT-RO incarcat.")
        except:
            try:
                from transformers import pipeline as hp
                self.bert = hp("sentiment-analysis",
                               model="nlptown/bert-base-multilingual-uncased-sentiment",
                               max_length=512, truncation=True)
                print("  [Sentiment] BERT multilingual incarcat (fallback).")
            except:
                print("  [Sentiment] Lexicon ponderat activ.")

    def score_bert(self, text):
        try:
            r = self.bert(text[:512])[0]
            l = r["label"].upper()
            s = r["score"]
            if "POS" in l or l in ("4 STARS","5 STARS"): return s
            if "NEG" in l or l in ("1 STAR","2 STARS"):  return -s
            return 0.0
        except:
            return None

    def score_lexicon(self, text):
        norm  = normalize(text.lower())
        words = re.findall(r'\b\w+\b', norm)
        pos   = sum(self.POS.get(w, 0) for w in words)
        neg   = sum(abs(self.NEG.get(w, 0)) for w in words)
        total = pos + neg
        if total < 0.1: return 0.0, 0.0
        score = (pos - neg) / total
        n_sw  = sum(1 for w in words if w in self.POS or w in self.NEG)
        conf  = min(n_sw / max(len(words),1) * 10, 1.0)
        return round(score,4), round(conf,4)

    def absa(self, text, party_patterns):
        """
        ABSA: extrage propozitiile care contin partid
        si calculeaza sentimentul DOAR pe acestea.
        """
        sents    = re.split(r'[.!?]', text)
        relevant = [s for s in sents
                    if any(re.search(p, s, re.IGNORECASE) for p in party_patterns)]
        if not relevant:
            # Fallback: sentiment pe tot articolul
            if self.bert:
                s = self.score_bert(text)
                return (s if s is not None else 0.0), 0.3
            return self.score_lexicon(text)

        scores = []
        for sent in relevant[:10]:
            if self.bert:
                s = self.score_bert(sent)
                if s is not None:
                    scores.append(s)
                    continue
            s, _ = self.score_lexicon(sent)
            scores.append(s)

        if not scores: return 0.0, 0.0
        mean = sum(scores)/len(scores)
        conf = min(len(scores)/5, 1.0)
        return round(mean,4), round(conf,4)

# ── BOOTSTRAP CI ─────────────────────────────────────────────────

def bootstrap_ci(scores, n=500, ci=0.95):
    if len(scores) < 2:
        m = scores[0] if scores else 0.0
        return m, None, None, None
    arr  = np.array(scores, dtype=float)
    boot = [np.mean(np.random.choice(arr, len(arr), replace=True)) for _ in range(n)]
    a    = (1-ci)/2
    return (round(float(np.mean(arr)),4),
            round(float(np.percentile(boot, a*100)),4),
            round(float(np.percentile(boot,(1-a)*100)),4),
            round(float(np.std(arr)),4))

# ── METRICI ───────────────────────────────────────────────────────

def compute_eef(party_data, total):
    if total == 0: return 0.0, 0.0
    probs = [d["article_count"]/total for d in party_data.values() if d["article_count"]>0]
    H    = -sum(p*math.log2(p) for p in probs if p>0)
    Hmax = math.log2(max(len(party_data),2))
    return round(H,4), round(H/Hmax if Hmax>0 else 0.0, 4)

def compute_srm(V, A, sigma, lam=0.15):
    return round(V*(abs(A)+0.05)*math.exp(-lam*sigma**2), 4)

def compute_isc(sigma):
    return round(max(0, 1-sigma**2), 4)

# ── DISIDENTA v2 ─────────────────────────────────────────────────

def compute_disidenta(votes_data, config):
    """
    Algoritm complet disidenta parlamentara.

    SD = SVE*0.6 + SA*0.4 + bonus_alarme

    SVE (Vot Explicit):
        = sum(voturi_contra_linie * w) / sum(prezenti * w)
        unde w = 2.0 (organica) | 1.5 (populara) | 1.0 (ordinara)

    SA (Absenteism Strategic):
        = (grup_size - prezenti_medii) / grup_size
        Alarma daca > prag_absenta din config

    Linia partidului = votul majoritatii grupului in acea sedinta.
    """
    partide_cfg = config["partide"]
    prag_abs    = config["praguri"]["alerta_absenta"] / 100

    agg = {p: {
        "ve_contra":0.0, "abtineri":0.0, "absenti":0,
        "prezenti":0, "n_voturi":0, "w_total":0.0,
        "alarme":0, "exemple":[]
    } for p in partide_cfg}

    popular_kws = ["masa la scoala","rca","pensii","salarii","horeca",
                   "sanatate","salarizare","masa sanatoasa"]

    for sedinta in votes_data:
        voturi = sedinta.get("voturi", [])
        if not voturi: continue

        titlu = sedinta.get("proiect","").lower()
        is_org = sedinta.get("tip","") == "organica"
        is_pop = sedinta.get("is_popular", False) or any(k in titlu for k in popular_kws)
        w = 2.0 if is_org else 1.5 if is_pop else 1.0

        # Grupeaza voturile pe partid
        by_party = {}
        for v in voturi:
            p_raw = v.get("partid","").upper()
            # Mapeaza abrevieri
            p = None
            for key in partide_cfg:
                if key in p_raw or p_raw.startswith(key):
                    p = key; break
            if not p: continue
            by_party.setdefault(p, []).append(v["vot"])

        for p, votlist in by_party.items():
            if p not in agg: continue

            gs       = partide_cfg[p]["grup_camera"]
            cnt      = {"PENTRU":0,"CONTRA":0,"ABTINERE":0,"NU A VOTAT":0}
            for vot in votlist:
                cnt[vot] = cnt.get(vot,0) + 1

            prezenti = cnt["PENTRU"] + cnt["CONTRA"] + cnt["ABTINERE"]

            # Linia grupului = optiunea majoritara
            linia = max(["PENTRU","CONTRA","ABTINERE"], key=lambda x: cnt[x])
            contra_linie = sum(cnt[k] for k in ["PENTRU","CONTRA","ABTINERE"] if k != linia)

            agg[p]["ve_contra"] += contra_linie * w
            agg[p]["abtineri"]  += cnt["ABTINERE"] * w
            agg[p]["absenti"]   += cnt["NU A VOTAT"]
            agg[p]["prezenti"]  += prezenti
            agg[p]["n_voturi"]  += 1
            agg[p]["w_total"]   += w

            # Alarma absenteism
            rata_abs = (gs - prezenti) / gs if gs > 0 else 0
            if rata_abs > prag_abs:
                agg[p]["alarme"] += 1
                agg[p]["exemple"].append(
                    f"Absenta {rata_abs*100:.0f}% la: {sedinta.get('proiect','?')[:60]}"
                )

    scores = {}
    for p, data in agg.items():
        if data["n_voturi"] == 0: continue
        gs  = partide_cfg[p]["grup_camera"]
        wt  = max(data["w_total"], 1)
        pm  = data["prezenti"] / data["n_voturi"]
        sve = data["ve_contra"] / (pm * wt) if pm > 0 else 0
        sa  = max(0, gs - pm) / gs if gs > 0 else 0
        sd  = min(sve*0.6 + sa*0.4 + 0.05*data["alarme"], 1.0)

        scores[p] = {
            "scor":             round(sd,4),
            "scor_vot_explicit":round(sve,4),
            "scor_absenteism":  round(sa,4),
            "scor_disidenta_pct": round(sd*100,2),   # in procente pt compatibilitate
            "prezenta_medie":   round(pm/gs*100,1) if gs>0 else 0,
            "alarme":           data["alarme"],
            "n_voturi":         data["n_voturi"],
            "exemple":          data["exemple"][:3],
            "formula":          f"SD={sd:.4f}=SVE({sve:.4f})*0.6+SA({sa:.4f})*0.4",
            "alerta_fractura":  sd >= config["praguri"]["alerta_disidenta"]/100,
            "interpretare": (
                "CRIZA INTERNA"           if sd>0.30 else
                "Disidenta semnificativa" if sd>0.15 else
                "Tensiuni moderate"       if sd>0.05 else
                "Disciplina de fier"
            ),
        }

    return {p:v for p,v in scores.items() if v["n_voturi"]>0}

# ── SCENARII ──────────────────────────────────────────────────────

def generate_scenarios(adj_polls, eef, config):
    threshold = 5.0
    n_seats   = 330

    def seats(polls):
        above = {p:v for p,v in polls.items() if v>=threshold}
        total = sum(above.values())
        return {p: round(v/total*n_seats) for p,v in above.items()} if total > 0 else {}

    def coalitions(s):
        maj = 166
        combos = [
            ("Coalitie actuala (PSD+PNL+USR+UDMR)", ["PSD","PNL","USR","UDMR"]),
            ("Nationalisti (AUR+SOS+POT)",           ["AUR","SOS","POT"]),
            ("PSD+AUR",                              ["PSD","AUR"]),
            ("Dreapta (PNL+USR+REPER+UDMR)",         ["PNL","USR","REPER","UDMR"]),
        ]
        return [{"name":n,"seats":sum(s.get(p,0) for p in ps),
                 "viable":sum(s.get(p,0) for p in ps)>=maj}
                for n,ps in combos if sum(s.get(p,0) for p in ps)>0]

    base  = {p: v["point"] for p,v in adj_polls.items()}
    s1    = seats(base)

    polls2 = {p: v*(1.12 if p in ["AUR","SOS","POT"] else 0.96) for p,v in base.items()}
    t2     = sum(polls2.values())
    polls2 = {p: round(v/t2*100,2) for p,v in polls2.items()} if t2>0 else polls2
    s2     = seats(polls2)

    polls3 = dict(base)
    t3     = sum(polls3.values())
    polls3 = {p: round(v/t3*100,2) for p,v in polls3.items()} if t3>0 else polls3
    s3     = seats(polls3)

    return {
        "baseline":    {"label":"Baseline","seats":s1,"coalitions":coalitions(s1),
                         "prob":round(0.5-abs(eef-0.5)*0.3,2)},
        "fragmentare": {"label":"Fragmentare (AUR/SOS/POT cresc)","seats":s2,
                         "coalitions":coalitions(s2),"prob":round(eef*0.4,2)},
        "consolidare": {"label":"Consolidare coalitie","seats":s3,
                         "coalitions":coalitions(s3),"prob":round((1-eef)*0.4,2)},
    }

# ── MAIN ──────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print("[Agent 3] ANALYSIS ENGINE v2 — pornit")
    config = load_config()

    with open("data/processed/ready_for_agent3.json", encoding="utf-8") as f:
        signal = json.load(f)
    ts = signal["timestamp"]

    with open(f"data/processed/entities_{ts}.json", encoding="utf-8") as f:
        entity_data = json.load(f)
    with open(f"data/raw/votes_{ts}.json", encoding="utf-8") as f:
        votes_data = json.load(f)

    party_data     = entity_data["party_data"]
    teme           = entity_data["teme_dominante"]
    parl_items     = entity_data.get("parl_items", [])
    total_articles = entity_data["ner_stats"]["total_articles"]

    # Patterns per partid pentru ABSA
    patterns_map = {
        "PSD":   [r"\bPSD\b", r"Social Democrat"],
        "PNL":   [r"\bPNL\b", r"National Liberal"],
        "USR":   [r"\bUSR\b", r"Salvati Romania"],
        "AUR":   [r"\bAUR\b", r"Simion"],
        "UDMR":  [r"\bUDMR\b", r"Maghiara"],
        "SOS":   [r"\bSOS\b", r"Sosoacu?a"],
        "POT":   [r"\bPOT\b"],
        "REPER": [r"\bREPER\b"],
    }

    sentiment_engine = SentimentEngine()

    print("  Calcul ABSA per partid (corelat cu entitati Agent 2)...")
    party_scores = {}
    for p, data in party_data.items():
        # Folosim propozitiile relevante extrase de Agent 2 (ABSA)
        sentences = data.get("relevant_sentences", [])
        if not sentences:
            party_scores[p] = [0.0]
            continue
        scores = []
        pats   = patterns_map.get(p, [rf"\b{p}\b"])
        for sent in sentences[:15]:
            score, conf = sentiment_engine.absa(sent, pats)
            scores.append(score)
        party_scores[p] = scores if scores else [0.0]

    # Bootstrap CI + metrici
    print("  Bootstrap CI 95%...")
    n_boot = config["praguri"]["bootstrap_n"]
    ci_niv = config["praguri"]["ci_nivel"]

    for p, data in party_data.items():
        scores = party_scores.get(p, [0.0])
        mean, lower, upper, std = bootstrap_ci(scores, n_boot, ci_niv)
        data["sentiment_mean"]     = mean
        data["sentiment_ci_lower"] = lower
        data["sentiment_ci_upper"] = upper
        data["sentiment_std"]      = std or 0.0
        data["n_sentiment"]        = len(scores)
        data["srm"]  = compute_srm(data["article_count"], mean, data["sentiment_std"])
        data["isc"]  = compute_isc(data["sentiment_std"])
        print(f"  {p}: sent={mean:+.3f} CI=[{lower},{upper}] SRM={data['srm']} ISC={data['isc']}")

    H, eef = compute_eef(party_data, total_articles)
    eef_int = ("haos" if eef>0.85 else "fragmentat" if eef>0.65 else
               "moderat" if eef>0.45 else "concentrat")

    # Indici antropologici
    extremist = sum(party_data.get(p,{}).get("article_count",0) for p in ["AUR","SOS","POT"])
    irs = round(extremist/total_articles,4) if total_articles>0 else 0
    gov_stds = [party_data[p]["sentiment_std"] for p in ["PSD","PNL","USR","UDMR"]
                if p in party_data and party_data[p].get("sentiment_std") is not None]
    iccp = round(1-sum(v**2 for v in gov_stds)/len(gov_stds),4) if gov_stds else 0
    ivs  = round(eef*(sum(v**2 for v in gov_stds)/len(gov_stds)),4) if gov_stds else 0

    indices = {
        "IRS":  {"value":irs,  "formula":"N_extremist/N_total","label":"Radicalizare Simbolica",
                 "interpretation":"ridicat" if irs>0.3 else "moderat" if irs>0.15 else "scazut"},
        "ICCP": {"value":iccp, "formula":"1-mean(sigma_gov^2)","label":"Coeziune Camp Politic",
                 "interpretation":"coeziv" if iccp>0.7 else "fragil" if iccp>0.5 else "fracturat"},
        "IVS":  {"value":ivs,  "formula":"EEF*mean(sigma^2)","label":"Volatilitate Simbolica",
                 "interpretation":"volatil" if ivs>0.2 else "stabil" if ivs<0.1 else "mediu"},
        "EEF":  {"value":eef,  "formula":"H/H_max","label":"Entropie Ecosistem",
                 "interpretation":eef_int},
    }

    # Polling ajustat
    baseline  = config["polling_baseline"]
    total_srm = sum(d.get("srm",0) for d in party_data.values()) or 1
    adj_polls = {}
    for p in config["partide"]:
        base = baseline.get(p, 5)
        if p not in party_data:
            adj_polls[p] = {"point":base,"lower":base-1,"upper":base+1,"delta":0,"valid":False}
            continue
        d = party_data[p]
        srm_share  = d.get("srm",0)/total_srm
        delta_srm  = (srm_share - 1/len(config["partide"])) * 4
        delta_sent = d["sentiment_mean"] * 1.5
        delta_isc  = (d["isc"] - 0.5) * 2
        total_delta = delta_srm + delta_sent + delta_isc
        ci_l = d["sentiment_ci_lower"] or d["sentiment_mean"]
        ci_u = d["sentiment_ci_upper"] or d["sentiment_mean"]
        adj_polls[p] = {
            "point": round(max(0.5, base+total_delta),2),
            "lower": round(max(0.5, base+ci_l*1.5+delta_srm+delta_isc),2),
            "upper": round(max(0.5, base+ci_u*1.5+delta_srm+delta_isc),2),
            "delta": round(total_delta,2),
            "valid": d["sufficient_data"],
        }
    total_pt = sum(v["point"] for v in adj_polls.values())
    if total_pt > 0:
        for p in adj_polls:
            adj_polls[p]["point"] = round(adj_polls[p]["point"]/total_pt*100,2)
            adj_polls[p]["lower"] = round(adj_polls[p]["lower"]/total_pt*100,2)
            adj_polls[p]["upper"] = round(adj_polls[p]["upper"]/total_pt*100,2)

    scenarios = generate_scenarios(adj_polls, eef, config)

    print("  Calcul disidenta parlamentara (3 componente)...")
    disidenta = compute_disidenta(votes_data, config)
    for p,d in disidenta.items():
        print(f"  {p}: SD={d['scor']:.4f} ({d['interpretare']})")

    warnings = [
        f"{p}: doar {d['article_count']} articole — sub pragul {config['praguri']['minim_articole_partid']}"
        for p,d in party_data.items() if not d["sufficient_data"]
    ]

    output = {
        "timestamp":          ts,
        "total_articles":     total_articles,
        "eef":                eef,
        "entropy_H":          H,
        "eef_interpretation": eef_int,
        "indices":            indices,
        "party_data":         {p:{k:v for k,v in d.items() if k!="relevant_sentences"}
                               for p,d in party_data.items()},
        "adj_polls":          adj_polls,
        "baseline":           baseline,
        "scenarios":          scenarios,
        "disidenta":          disidenta,
        "teme_dominante":     teme,
        "parl_items":         parl_items,
        "voturi_raw":         votes_data,
        "warnings":           warnings,
        "source_stats":       entity_data["ner_stats"],
    }

    with open(f"data/processed/analysis_{ts}.json","w",encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    with open("data/processed/ready_for_agent4.json","w",encoding="utf-8") as f:
        json.dump({"timestamp": ts}, f)

    print(f"[Agent 3] DONE — EEF={eef:.4f} IRS={irs:.4f} disidenta:{list(disidenta.keys())}")

if __name__ == "__main__":
    main()
