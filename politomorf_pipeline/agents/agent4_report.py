"""
Agent 4 — Report Generator + Email
Responsabilitati:
- Genereaza raport HTML complet cu toate sectiunile
- Exporta CSV per partid + CSV disidenta + JSON arhiva
- Trimite email cu attachments
- Salveaza in data/reports/
"""

import json, yaml, csv, os, smtplib
from pathlib import Path
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def load_config():
    with open("config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)

def sc(s):
    if s is None: return "#888"
    if s > 0.15: return "#1b5e20"
    if s < -0.15: return "#b71c1c"
    return "#e65100"

def ic(label):
    neg = ["ridicat","fragil","fracturat","volatil","haos","fragmentat","disidenta","criza"]
    pos = ["scazut","coeziv","stabil","concentrat","fier"]
    if any(l in label.lower() for l in neg): return "#b71c1c"
    if any(l in label.lower() for l in pos): return "#1b5e20"
    return "#e65100"

# ── HTML BUILDER ──────────────────────────────────────────────────

def build_html(analysis, config):
    today     = datetime.now(timezone.utc).strftime("%d %B %Y")
    n         = analysis["total_articles"]
    eef       = analysis["eef"]
    eef_int   = analysis["eef_interpretation"]
    pd        = analysis["party_data"]
    indices   = analysis["indices"]
    adj       = analysis["adj_polls"]
    baseline  = analysis["baseline"]
    scenarios = analysis["scenarios"]
    diz       = analysis["disidenta"]
    teme      = analysis["teme_dominante"]
    parl      = analysis["parl_items"]
    voturi    = analysis["voturi_raw"]
    warnings  = analysis["warnings"]
    src_stats = analysis.get("source_stats", {})

    # ── Avertizari
    warn_html = ""
    if warnings:
        warn_html = "<div style='background:#fff3e0;border-left:4px solid #ff9800;padding:12px;border-radius:4px;margin:16px 0'><b>⚠️ Avertizari metodologice:</b><ul>"
        for w in warnings:
            warn_html += f"<li style='font-size:13px'>{w}</li>"
        warn_html += f"<li style='font-size:13px'>Prag minim indici valizi: {config['praguri']['minim_articole_partid']} articole/partid</li></ul></div>"

    # ── I. Partide
    rows_p = ""
    for p, d in sorted(pd.items(), key=lambda x: -x[1]["article_count"]):
        srm  = d.get("srm",0)
        isc  = d.get("isc",0)
        sent = d.get("sentiment_mean",0)
        ci_l = d.get("sentiment_ci_lower")
        ci_u = d.get("sentiment_ci_upper")
        ci_s = f"[{ci_l:+.3f}, {ci_u:+.3f}]" if ci_l is not None else "N/A"
        warn = " ⚠️" if not d["sufficient_data"] else ""
        rows_p += (f"<tr><td style='padding:7px 10px;font-weight:bold'>{p}{warn}</td>"
                   f"<td style='text-align:center'>{d['article_count']}</td>"
                   f"<td style='text-align:center'>{d['mentions_total']}</td>"
                   f"<td style='text-align:center;color:{sc(sent)};font-weight:bold'>{sent:+.4f}</td>"
                   f"<td style='text-align:center;font-size:12px'>{ci_s}</td>"
                   f"<td style='text-align:center'>{srm:.3f}</td>"
                   f"<td style='text-align:center'>{isc:.3f}</td>"
                   f"<td style='font-size:12px;color:#666'>{d['bloc']}</td></tr>")

    # ── II. Indici
    rows_i = ""
    for k, idx in indices.items():
        color = ic(idx["interpretation"])
        rows_i += (f"<tr><td style='padding:6px 10px;font-weight:bold'>{k}</td>"
                   f"<td>{idx['label']}</td>"
                   f"<td style='font-family:monospace;font-size:11px;color:#666'>{idx['formula']}</td>"
                   f"<td style='text-align:center;font-weight:bold'>{idx['value']:.4f}</td>"
                   f"<td style='color:{color};font-weight:bold'>{idx['interpretation'].upper()}</td></tr>")

    # ── III. Polling
    rows_poll = ""
    for p, v in sorted(adj.items(), key=lambda x: -x[1]["point"]):
        base  = baseline.get(p, 0)
        delta = v["delta"]
        dc    = "#1b5e20" if delta>0 else "#b71c1c" if delta<0 else "#555"
        valid = "" if v.get("valid",True) else " ⚠️"
        rows_poll += (f"<tr><td style='padding:6px 10px;font-weight:bold'>{p}{valid}</td>"
                      f"<td style='text-align:center'>{base}%</td>"
                      f"<td style='text-align:center;font-weight:bold'>{v['point']}%</td>"
                      f"<td style='text-align:center;font-size:12px;color:#666'>[{v['lower']}%, {v['upper']}%]</td>"
                      f"<td style='text-align:center;color:{dc};font-weight:bold'>{delta:+.2f}pp</td></tr>")

    # ── IV. Scenarii
    rows_sc = ""
    for key, sc_data in scenarios.items():
        seats_str = " | ".join(f"{p}:{s}" for p,s in sorted(sc_data["seats"].items(), key=lambda x:-x[1]))
        coal_str  = "<br>".join(f"{'✅' if c['viable'] else '❌'} <b>{c['name']}</b> ({c['seats']} mandate)"
                                for c in sc_data["coalitions"]) or "Nicio majoritate clara"
        rows_sc += (f"<tr><td style='padding:8px 10px;font-weight:bold'>{sc_data['label']}</td>"
                    f"<td style='font-size:12px'>{seats_str}</td>"
                    f"<td style='font-size:12px'>{coal_str}</td>"
                    f"<td style='text-align:center;font-weight:bold'>{int(sc_data['prob']*100)}%</td></tr>")

    # ── V. Disidenta
    rows_diz = ""
    for p, d in sorted(diz.items(), key=lambda x: -x[1]["scor"]):
        color = "#b71c1c" if d["scor"]>0.15 else "#e65100" if d["scor"]>0.05 else "#1b5e20"
        exemple = "<br>".join(f"<span style='font-size:11px;color:#888'>{e}</span>" for e in d.get("exemple",[]))
        rows_diz += (f"<tr><td style='padding:7px 10px;font-weight:bold'>{p}</td>"
                     f"<td style='text-align:center;color:{color};font-weight:bold'>{d['scor']:.4f}</td>"
                     f"<td style='text-align:center'>{d['scor_vot_explicit']:.4f}</td>"
                     f"<td style='text-align:center'>{d['scor_absenteism']:.4f}</td>"
                     f"<td style='text-align:center'>{d.get('prezenta_medie','?')}%</td>"
                     f"<td style='color:{color};font-weight:bold'>{d['interpretare'].upper()}</td></tr>"
                     + (f"<tr><td colspan='6' style='padding:2px 10px 6px'>{exemple}</td></tr>" if exemple else ""))

    if not rows_diz:
        rows_diz = "<tr><td colspan='6' style='text-align:center;color:#888;padding:10px'>Date voturi nominale indisponibile azi</td></tr>"

    # ── VI. Intelligence Board — Teme
    max_score = max((t[1] for t in teme), default=1) or 1
    teme_bars = ""
    for tema, score in teme[:8]:
        w = int(score/max_score*180)
        teme_bars += (f"<div style='display:flex;align-items:center;margin:5px 0'>"
                      f"<span style='width:200px;font-size:13px'>{tema}</span>"
                      f"<div style='background:#1F3864;width:{w}px;height:18px;border-radius:3px;margin:0 8px'></div>"
                      f"<span style='font-size:12px;color:#666'>{score}</span></div>")

    # ── VI. Dominanta
    dom_rows = ""
    if pd:
        max_art = max(d["article_count"] for d in pd.values()) or 1
        for p, d in sorted(pd.items(), key=lambda x: -x[1]["article_count"]):
            vol = round(d["article_count"]/max_art, 2)
            sent = d.get("sentiment_mean",0)
            ton = "pozitiv" if sent>0.1 else "negativ" if sent<-0.1 else "neutru"
            tc  = "#1b5e20" if ton=="pozitiv" else "#b71c1c" if ton=="negativ" else "#e65100"
            warn = " ⚠️" if not d["sufficient_data"] else ""
            dom_rows += (f"<tr><td style='padding:5px 10px;font-weight:bold'>{p}{warn}</td>"
                         f"<td style='text-align:center'>{d['article_count']}</td>"
                         f"<td style='text-align:center'>{vol:.2f}</td>"
                         f"<td style='text-align:center;color:{tc};font-weight:bold'>{ton.upper()}</td>"
                         f"<td style='text-align:center'>{abs(sent):.3f}</td></tr>")

    # ── VII. Ordine de zi
    parl_rows = ""
    for item in parl[:15]:
        parties_str = ", ".join(f"<b>{p}</b>" for p in item.get("parties",{}).keys()) or "—"
        org = "🔵 Organica" if item.get("is_organica") else ""
        parl_rows += (f"<tr><td style='padding:5px 8px;font-size:12px'>{item.get('proj_nr','')}</td>"
                      f"<td style='padding:5px 8px;font-size:12px'>{item.get('text','')[:120]}...</td>"
                      f"<td style='padding:5px 8px;font-size:12px'>{parties_str}</td>"
                      f"<td style='padding:5px 8px;font-size:12px'>{org}</td></tr>")

    # ── VIII. Voturi recente
    vot_rows = ""
    for vot in voturi[:6]:
        org = "🔵" if vot.get("is_organica") else ""
        vot_rows += (f"<tr><td style='padding:5px 8px;font-size:12px'>{org} "
                     f"<a href='{vot.get('url','')}' style='color:#1F3864'>{vot.get('titlu','?')[:70]}</a></td>"
                     f"<td style='text-align:center;font-size:12px'>{vot.get('total',{}).get('pentru',0)}</td>"
                     f"<td style='text-align:center;font-size:12px;color:#b71c1c'>{vot.get('total',{}).get('contra',0)}</td>"
                     f"<td style='text-align:center;font-size:12px'>{vot.get('total',{}).get('abtinere',0)}</td>"
                     f"<td style='text-align:center;font-size:12px'>{vot.get('total',{}).get('absent',0)}</td></tr>")
    if not vot_rows:
        vot_rows = "<tr><td colspan='5' style='text-align:center;color:#888;padding:10px'>Nu s-au detectat voturi nominale azi</td></tr>"

    src_str = " | ".join(f"{k}:{v}" for k,v in src_stats.items()) if src_stats else ""

    return f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'></head>
<body style="font-family:Arial,sans-serif;max-width:900px;margin:auto;color:#222">

<div style="background:#1F3864;padding:24px;border-radius:8px 8px 0 0">
  <h1 style="color:white;margin:0;font-size:22px">🇷🇴 POLITOMORF AGENT v4.0 — {today}</h1>
  <p style="color:#aac4e8;margin:8px 0 0;font-size:13px">
    Antropologie Politica Computationala | {n} articole politice
    | EEF: <b style="color:white">{eef:.4f}</b> ({eef_int})
  </p>
</div>
<div style="padding:24px;border:1px solid #ddd;border-top:none">

{warn_html}

<h2 style="color:#1F3864;border-bottom:2px solid #1F3864;padding-bottom:6px">
  I. Analiza Media — Sentiment ABSA + 95% CI Bootstrap
</h2>
<table style="width:100%;border-collapse:collapse;font-size:13px">
  <tr style="background:#f2f4f7;font-weight:bold">
    <th style="padding:8px 10px;text-align:left">Partid</th>
    <th>Articole</th><th>Mentiuni</th><th>Sentiment ABSA</th>
    <th>95% CI</th><th>SRM</th><th>ISC</th><th>Bloc</th>
  </tr>{rows_p}
</table>
<p style="font-size:11px;color:#888;margin-top:4px">
  ⚠️=date insuficiente | ABSA=sentiment specific partidului |
  SRM=V·|A|·exp(-0.15σ²) | ISC=1-σ²
</p>

<h2 style="color:#1F3864;border-bottom:2px solid #1F3864;padding-bottom:6px;margin-top:28px">
  II. Indici Antropologie Politica Computationala
</h2>
<table style="width:100%;border-collapse:collapse;font-size:13px">
  <tr style="background:#f2f4f7;font-weight:bold">
    <th style="padding:8px 10px;text-align:left">Indice</th>
    <th>Descriere</th><th>Formula</th><th>Valoare</th><th>Interpretare</th>
  </tr>{rows_i}
</table>

<h2 style="color:#1F3864;border-bottom:2px solid #1F3864;padding-bottom:6px;margin-top:28px">
  III. Polling Ajustat cu CI Propagat
</h2>
<table style="width:70%;border-collapse:collapse;font-size:13px">
  <tr style="background:#f2f4f7;font-weight:bold">
    <th style="padding:8px 10px;text-align:left">Partid</th>
    <th>Baseline</th><th>Ajustat</th><th>CI [low, up]</th><th>Delta</th>
  </tr>{rows_poll}
</table>

<h2 style="color:#1F3864;border-bottom:2px solid #1F3864;padding-bottom:6px;margin-top:28px">
  IV. Scenarii Electorale
</h2>
<table style="width:100%;border-collapse:collapse;font-size:13px">
  <tr style="background:#f2f4f7;font-weight:bold">
    <th style="padding:8px 10px;text-align:left">Scenariu</th>
    <th>Mandate</th><th>Coalitii posibile</th><th>Prob.</th>
  </tr>{rows_sc}
</table>
<p style="font-size:11px;color:#888;margin-top:4px">Prag 5% | 330 mandate | Hare-Niemeyer</p>

<h2 style="color:#b71c1c;border-bottom:2px solid #b71c1c;padding-bottom:6px;margin-top:28px">
  V. Disidenta Parlamentara — SD = SVE×0.6 + SA×0.4
</h2>
<div style="background:#fff3e0;padding:10px;border-radius:4px;margin-bottom:12px;font-size:12px">
  <b>C1 Vot Explicit:</b> SVE = voturi_contra_linie×w / prezenti×w_total |
  <b>C2 Absenteism:</b> SA = (grup-prezenti) / grup |
  <b>Ponderare:</b> organica=2.0, popular=1.5, ordinar=1.0
</div>
<table style="width:100%;border-collapse:collapse;font-size:13px">
  <tr style="background:#f2f4f7;font-weight:bold">
    <th style="padding:8px 10px;text-align:left">Partid</th>
    <th>SD Final</th><th>C1 Vot Explicit</th><th>C2 Absenteism</th>
    <th>Prezenta medie</th><th>Interpretare</th>
  </tr>{rows_diz}
</table>

<h2 style="color:#1F3864;border-bottom:2px solid #1F3864;padding-bottom:6px;margin-top:28px">
  VI. Intelligence Board — Teme Dominante + Dominanta Politica
</h2>
<div style="display:flex;flex-wrap:wrap;gap:16px">
  <div style="flex:1;min-width:280px;background:#f0f4ff;padding:16px;border-radius:8px">
    <h3 style="color:#1F3864;margin-top:0">Teme Dominante Azi</h3>
    {teme_bars if teme_bars else "<p style='color:#888'>Date insuficiente</p>"}
  </div>
  <div style="flex:1;min-width:280px;background:#f0f4ff;padding:16px;border-radius:8px">
    <h3 style="color:#1F3864;margin-top:0">Cine Domina Scena Politica</h3>
    <table style="width:100%;border-collapse:collapse;font-size:13px">
      <tr style="background:#e8edf5;font-weight:bold">
        <th style="padding:5px">Partid</th><th>Art.</th><th>Volum</th><th>Ton</th><th>Intens.</th>
      </tr>{dom_rows}
    </table>
  </div>
</div>

<h2 style="color:#1F3864;border-bottom:2px solid #1F3864;padding-bottom:6px;margin-top:28px">
  VII. Ordine de Zi — Camera Deputatilor
</h2>
<table style="width:100%;border-collapse:collapse;font-size:12px">
  <tr style="background:#f2f4f7;font-weight:bold">
    <th style="padding:6px 8px;width:120px">Nr. proiect</th>
    <th>Descriere</th><th>Partide</th><th>Tip</th>
  </tr>{parl_rows if parl_rows else "<tr><td colspan='4' style='text-align:center;color:#888;padding:10px'>Date indisponibile azi</td></tr>"}
</table>

<h2 style="color:#1F3864;border-bottom:2px solid #1F3864;padding-bottom:6px;margin-top:28px">
  VIII. Voturi Nominale Recente — Camera Deputatilor
</h2>
<table style="width:100%;border-collapse:collapse;font-size:12px">
  <tr style="background:#f2f4f7;font-weight:bold">
    <th style="padding:6px 8px;text-align:left">Proiect</th>
    <th>Pentru</th><th>Contra</th><th>Abtineri</th><th>Absenti</th>
  </tr>{vot_rows}
</table>

<div style="background:#e8f5e9;border-left:4px solid #2e7d32;padding:12px;margin:20px 0;border-radius:4px;font-size:12px">
  <b>Nota metodologica:</b> Toate formulele sunt documentate si afisate.
  ABSA = Aspect-Based Sentiment Analysis (propozitii specifice partidului).
  CI = Bootstrap 95% (n={config['praguri']['bootstrap_n']}).
  Disidenta = 3 componente: vot explicit + absenteism + ponderare contextuala.
  Concluziile cu ⚠️ sunt speculative din cauza datelor insuficiente.
</div>

<p style="font-size:11px;color:#aaa;border-top:1px solid #eee;padding-top:10px">
  Politomorf Agent v4.0 | OSF: 10.17605/OSF.IO/HYDNZ |
  Metodologie: <a href="https://osf.io/hydnz">osf.io/hydnz</a><br>
  Date colectate automat — nu reprezinta o predictie electorala certificata.
</p>
</div>
</body></html>"""

# ── CSV EXPORTS ───────────────────────────────────────────────────

def save_csvs(analysis, ts):
    Path("data/reports").mkdir(parents=True, exist_ok=True)
    files = []

    # CSV partide
    path = Path(f"data/reports/partide_{ts}.csv")
    pd   = analysis["party_data"]
    with open(path,"w",newline="",encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "partid","articole","mentiuni","sentiment","ci_lower","ci_upper",
            "std","srm","isc","bloc","sufficient"
        ])
        writer.writeheader()
        for p,d in pd.items():
            writer.writerow({
                "partid":    p,
                "articole":  d["article_count"],
                "mentiuni":  d["mentions_total"],
                "sentiment": d.get("sentiment_mean",0),
                "ci_lower":  d.get("sentiment_ci_lower",""),
                "ci_upper":  d.get("sentiment_ci_upper",""),
                "std":       d.get("sentiment_std",""),
                "srm":       d.get("srm",0),
                "isc":       d.get("isc",0),
                "bloc":      d["bloc"],
                "sufficient":d["sufficient_data"],
            })
    files.append(path)

    # CSV disidenta
    diz  = analysis["disidenta"]
    path2 = Path(f"data/reports/disidenta_{ts}.csv")
    with open(path2,"w",newline="",encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "partid","scor_final","vot_explicit","absenteism",
            "prezenta_medie","n_voturi","interpretare","formula"
        ])
        writer.writeheader()
        for p,d in diz.items():
            writer.writerow({
                "partid":        p,
                "scor_final":    d["scor"],
                "vot_explicit":  d["scor_vot_explicit"],
                "absenteism":    d["scor_absenteism"],
                "prezenta_medie":d.get("prezenta_medie",""),
                "n_voturi":      d["n_voturi"],
                "interpretare":  d["interpretare"],
                "formula":       d["formula"],
            })
    files.append(path2)

    # JSON arhiva
    path3 = Path(f"data/reports/politomorf_v4_{ts}.json")
    with open(path3,"w",encoding="utf-8") as f:
        json.dump({k:v for k,v in analysis.items() if k!="voturi_raw"}, f, ensure_ascii=False, indent=2)
    files.append(path3)

    return files

# ── EMAIL ─────────────────────────────────────────────────────────

def send_email(config, html_body, attachments):
    gmail_user = os.environ.get("GMAIL_USER", config["email"].get("sender",""))
    gmail_pass = os.environ.get("GMAIL_APP_PASSWORD", config["email"].get("password",""))
    recipient  = os.environ.get("EMAIL_RECIPIENT", config["email"].get("recipient",""))
    today      = datetime.now(timezone.utc).strftime("%d %b %Y")

    msg = MIMEMultipart("mixed")
    msg["From"]    = gmail_user
    msg["To"]      = recipient
    msg["Subject"] = f"Politomorf Agent v4.0 — {today}"
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    for path in attachments:
        p = Path(path)
        if p.exists():
            with open(p,"rb") as f:
                part = MIMEBase("application","octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f'attachment; filename="{p.name}"')
            msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, gmail_pass)
        server.sendmail(gmail_user, recipient, msg.as_string())
    print(f"  Email trimis la {recipient}")

# ── MAIN ──────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print("[Agent 4] REPORT GENERATOR — pornit")
    config = load_config()

    with open("data/processed/ready_for_agent4.json", encoding="utf-8") as f:
        signal = json.load(f)
    ts = signal["timestamp"]

    with open(f"data/processed/analysis_{ts}.json", encoding="utf-8") as f:
        analysis = json.load(f)

    print("  Generare HTML...")
    html = build_html(analysis, config)

    print("  Export CSV + JSON...")
    attachments = save_csvs(analysis, ts)

    print("  Salvare raport HTML...")
    html_path = Path(f"data/reports/report_{ts}.html")
    html_path.write_text(html, encoding="utf-8")

    print("  Trimitere email...")
    send_email(config, html, attachments)

    print(f"[Agent 4] DONE — raport {html_path.name}")

if __name__ == "__main__":
    main()
