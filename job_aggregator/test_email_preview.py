#!/usr/bin/env python3
"""
Test script — simula el flujo end-to-end: Tier 1 (RSS) + Groq mock + email HTML.

Genera un email HTML para previsualización y opcionalmente lo envía.

Uso:
  python test_email_preview.py              # Genera y guarda HTML
  python test_email_preview.py --send       # También envía por email
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Directorio raíz
_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _ROOT)

# Config
MAX_DAYS_OLD = 14
with open(os.path.join(_ROOT, "config", "keywords.json")) as f:
    KW = json.load(f)

print("=" * 62)
print("Test Email Preview — Job Aggregator v2")
print("=" * 62)

# ── TIER 1: Fetch real RSS data ──
print("\n[1/4] Fetching Tier 1 RSS data...")

from scrapers.rss_api import RemoteOKScraper, WorkingNomadsScraper, JobspressoScraper

all_jobs = []

# RemoteOK — video + audio
rok = RemoteOKScraper()
for tag in ["video", "audio"]:
    jobs = rok.search_api(tag, limit=10)
    all_jobs.extend(jobs)
    print(f"  RemoteOK '{tag}': {len(jobs)} ofertas")

# RSS feeds
for scraper_cls in [WorkingNomadsScraper, JobspressoScraper]:
    scraper = scraper_cls()
    jobs = scraper.get_jobs(limit=10)
    all_jobs.extend(jobs)
    print(f"  {scraper.name}: {len(jobs)} ofertas")

print(f"\n✓ Total scraped: {len(all_jobs)}")

# ── DEDUPLICAR ──
print("\n[2/4] Deduplicating by URL...")
seen = set()
unique = []
for j in all_jobs:
    u = (j.url or "").strip()
    if u and u not in seen:
        seen.add(u)
        unique.append(j)

print(f"✓ Unique: {len(unique)}")

# ── GROQ MOCK O REAL ──
print("\n[3/4] Validating with Groq (or mock)...")

from validators.groq_validator import validate_and_summarize

ai_result = validate_and_summarize(unique)
print(f"✓ Top offers: {len(ai_result['top_offers'])}")
print(f"✓ Summary: {bool(ai_result['summary'])}")
print(f"✓ Failed: {ai_result['failed']}")

# ── EMAIL HTML ──
print("\n[4/4] Generating HTML email...")

# Import email builders from main
from main import _job_card_html, _group_jobs_by_category

today = datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")
stats = {
    "total_scraped": len(all_jobs),
    "after_date_filter": len(unique),
    "unique_urls": len(unique),
    "saved_new": 0,
    "elapsed_s": 0.0,
}

top_offers = ai_result.get("top_offers", unique[:5])
ai_summary = ai_result.get("summary", "")
ai_failed = ai_result.get("failed", True)
groups = _group_jobs_by_category(unique[:40])

# Resumen block
summary_block = ""
if ai_summary and not ai_failed:
    summary_block = f"""
<div style="background:#f0f7ff;border-left:4px solid #4a90d9;padding:14px 18px;margin-bottom:20px;border-radius:0 6px 6px 0">
  <strong style="color:#4a90d9">Resumen del mercado laboral (IA)</strong>
  <p style="margin:8px 0 0 0;color:#333;font-size:14px">{ai_summary}</p>
</div>"""
else:
    summary_block = f"""
<div style="background:#fff8f0;border-left:4px solid #ff9900;padding:14px 18px;margin-bottom:20px;border-radius:0 6px 6px 0">
  <strong style="color:#ff9900">Resumen IA (sin Groq)</strong>
  <p style="margin:8px 0 0 0;color:#333;font-size:14px">Se encontraron {len(unique)} ofertas únicas en {len(all_jobs)} total scraped. Agrupadoras por categoría abajo.</p>
</div>"""

# Top ofertas
top_cards = "".join(_job_card_html(j, highlight=True) for j in top_offers[:3])

# Categorías
category_sections = ""
category_names = {
    "audiovisual": "Audiovisual",
    "marketing": "Marketing",
    "freelance": "Freelance",
    "remoto": "Remoto / Internacional",
    "otros": "Otros",
}
for cat_key, cat_label in category_names.items():
    cat_jobs = groups.get(cat_key, [])
    if not cat_jobs:
        continue
    cards = "".join(_job_card_html(j) for j in cat_jobs)
    category_sections += f"""
<h3 style="color:#1a1a2e;border-bottom:2px solid #eee;padding-bottom:6px;margin-top:28px">{cat_label} ({len(cat_jobs)})</h3>
{cards}"""

more_text = ""

html_body = f"""
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: Arial, sans-serif; max-width: 680px; margin: 0 auto; color: #222; line-height: 1.5; }}
    a {{ color: #4a90d9; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <div style="background:#1a1a2e;color:white;padding:20px 24px;border-radius:8px 8px 0 0">
    <h1 style="margin:0;font-size:22px">FeinaAP</h1>
    <p style="margin:4px 0 0 0;opacity:0.8">{today} · <strong>{len(unique)} nuevas ofertas</strong></p>
  </div>
  <div style="padding:24px;border:1px solid #eee;border-top:none;border-radius:0 0 8px 8px">
    {summary_block}
    <h2 style="color:#e63946;margin-top:0">Top ofertas destacadas</h2>
    {top_cards}
    {category_sections}
    {more_text}
    <hr style="border:none;border-top:1px solid #eee;margin:24px 0">
    <p style="font-size:11px;color:#aaa">Stats: scraped={stats.get('total_scraped',0)} · filtradas={stats.get('after_date_filter',0)} · únicas={stats.get('unique_urls',0)} · IA={'OK' if not ai_failed else 'sin Groq'}</p>
  </div>
</body>
</html>"""

# Guardar HTML
html_file = Path(_ROOT) / "email_preview.html"
html_file.write_text(html_body, encoding="utf-8")
print(f"✓ HTML guardado en: {html_file}")

# ── ENVIAR (opcional) ──
if "--send" in sys.argv:
    print("\n[5/5] Sending email...")
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import smtplib

    from_email = os.environ.get("ALERT_EMAIL_FROM")
    from_password = os.environ.get("ALERT_EMAIL_PASSWORD")
    to_email = os.environ.get("ALERT_EMAIL_TO", "aitorpalacios93@gmail.com")

    if not from_email or not from_password:
        print("✗ Email no configurado (ALERT_EMAIL_FROM/PASSWORD)")
        print(f"  Abre manualmente: {html_file}")
    else:
        try:
            plain_body = f"FeinaAP — {today} — {len(unique)} nuevas ofertas\n\nAbre el HTML en: {html_file}"
            msg = MIMEMultipart("alternative")
            msg["From"] = from_email
            msg["To"] = to_email
            msg["Subject"] = f"FeinaAP TEST: {len(unique)} nuevas ofertas — {today[:5]}"
            msg.attach(MIMEText(plain_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(from_email, from_password)
            server.send_message(msg)
            server.quit()
            print(f"✓ Email enviado a {to_email}")
        except Exception as e:
            print(f"✗ Error: {e}")
            print(f"  Abre manualmente: {html_file}")
else:
    print(f"\nAbre el email en tu navegador:")
    print(f"  open {html_file}")
    print(f"\nO envía por SMTP:")
    print(f"  python test_email_preview.py --send")

print("\n" + "=" * 62)
