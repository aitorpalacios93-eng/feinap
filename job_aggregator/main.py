#!/usr/bin/env python3
"""
Job Aggregator v2 — GitHub Actions entrypoint
Ejecuta 3x/día: 08:00, 12:00, 16:00 UTC (10h, 14h, 18h hora España)

Tiers:
  1 → RSS + JSON APIs     (RemoteOK, WorkingNomads, Jobspresso, Remote.co, Jooble, Adzuna)
  2 → HTML / requests     (Tecnoempleo, Domestika, Hacesfalta, Infoempleo, Milanuncios,
                           Talent.com, RemotoJOB, TicJob, JobFluent, Shakers, Feina Activa,
                           WeRemoto, Mandy, ProductionHub, Malt.es, Workana,
                           Freelancer.es, PeoplePerHour, SoyFreelancer)
  3 → Playwright          (InfoJobs, Indeed)

Base de datos: Supabase (tabla ofertas_empleo) si SUPABASE_URL está disponible,
               SQLite jobs.db en local.
"""

import os
import sys
import json
import time
import logging
import signal
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, date
from typing import List

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("main")

# ── Directorio raíz ───────────────────────────────────────────────────────────
_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _ROOT)

# ── Config ────────────────────────────────────────────────────────────────────
MAX_DAYS_OLD = int(os.environ.get("MAX_DAYS_OLD", "14"))
LIMIT = int(os.environ.get("OFFERS_PER_PORTAL", "25"))

with open(os.path.join(_ROOT, "config", "keywords.json")) as f:
    KW = json.load(f)

KW_AV = KW["audiovisual"]  # Keywords audiovisual
KW_CREAT = KW["creative_remote"]  # Video editor remoto
KW_N8N = KW["n8n_automation"]  # n8n / automatización
KW_UGC = KW["ugc"]  # UGC creator
KW_VA = KW["virtual_assistant"]  # Asistente virtual
KW_MKT = KW["marketing"]  # Marketing digital


# ── DB ─────────────────────────────────────────────────────────────────────────
USE_SUPABASE = bool(os.environ.get("SUPABASE_URL"))


def _get_db():
    if USE_SUPABASE:
        from db.supabase_db import SupabaseDB

        return SupabaseDB()
    else:
        from db.database import JobDatabase

        return JobDatabase(os.path.join(_ROOT, "jobs.db"))


# ── Helpers ───────────────────────────────────────────────────────────────────


def is_recent(job) -> bool:
    """True si la oferta es reciente o su fecha es desconocida."""
    if not job.date_posted:
        return True
    cutoff = date.today() - timedelta(days=MAX_DAYS_OLD)
    d = (
        job.date_posted.date()
        if isinstance(job.date_posted, datetime)
        else job.date_posted
    )
    return d >= cutoff


def run(name: str, fn, *args, **kwargs) -> List:
    """Ejecuta un scraper con manejo de errores y timeout."""

    def _run_with_timeout():
        result = [None]
        error = [None]

        def _target():
            try:
                result[0] = fn(*args, **kwargs) or []
            except Exception as e:
                error[0] = e

        thread = threading.Thread(target=_target)
        thread.daemon = True
        thread.start()
        thread.join(timeout=60)  # 60s timeout por scraper

        if thread.is_alive():
            log.warning(f"  [{name}] TIMEOUT (>60s) - saltando")
            return []
        if error[0]:
            log.warning(f"  [{name}] FAILED: {error[0]}")
            return []
        return result[0] or []

    try:
        t0 = time.time()
        jobs = _run_with_timeout()
        elapsed = time.time() - t0
        log.info(f"  [{name}] {len(jobs)} ofertas ({elapsed:.1f}s)")
        return jobs
    except Exception as exc:
        log.warning(f"  [{name}] FAILED: {exc}")
        return []


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> int:
    log.info("=" * 62)
    log.info("Job Aggregator v2 — inicio")
    log.info(f"Supabase: {'SI' if USE_SUPABASE else 'NO (SQLite local)'}")
    log.info(f"Filtro fechas: últimos {MAX_DAYS_OLD} días")
    t_start = datetime.utcnow()
    all_jobs: List = []

    # ══════════════════════════════════════════════════════════════
    # TIER 1: RSS / JSON APIs — rápido, siempre incluyen fecha
    # ══════════════════════════════════════════════════════════════
    log.info("── TIER 1: APIs y RSS ──")

    from scrapers.rss_api import (
        RemoteOKScraper,
        RSSJobScraper,
        WorkingNomadsScraper,
        JobspressoScraper,
        RemoteCoScraper,
        AdzunaScraper,
    )
    from scrapers.jooble_api import JoobleAPI

    # RemoteOK JSON API — portales: remoto_internacional
    rok = RemoteOKScraper()
    for tag in ["video", "audio", "film"]:
        all_jobs += run("RemoteOK", rok.search_api, tag, limit=LIMIT)

    # RSS feeds de empleo remoto
    for scraper_fn in [WorkingNomadsScraper, JobspressoScraper, RemoteCoScraper]:
        scraper = scraper_fn()
        all_jobs += run(scraper.name, scraper.get_jobs, limit=LIMIT)

    # Jooble API — audiovisual + marketing (Barcelona y remoto)
    jooble = JoobleAPI()
    for kw in KW_AV[:2]:
        all_jobs += run("Jooble", jooble.search, kw, location="España", limit=20)
    for kw in KW_MKT[:3]:
        all_jobs += run("Jooble-MKT", jooble.search, kw, location="Barcelona", limit=20)
        all_jobs += run("Jooble-MKT-Remote", jooble.search, kw, location="Remote", limit=20)

    # Adzuna API (opcional, necesita secrets ADZUNA_APP_ID + ADZUNA_APP_KEY)
    if os.environ.get("ADZUNA_APP_ID"):
        adzuna = AdzunaScraper()
        for kw in KW_AV[:4]:
            all_jobs += run("Adzuna", adzuna.search, kw, limit=20)
        for kw in KW_MKT[:3]:
            all_jobs += run("Adzuna-MKT", adzuna.search, kw, limit=20)

    # ══════════════════════════════════════════════════════════════
    # TIER 2: HTML + requests — sin browser
    # ══════════════════════════════════════════════════════════════
    log.info("── TIER 2: HTML scrapers ──")

    # Portales de empleo españoles
    from scrapers.tecnoempleo import TecnoempleoScraper
    from scrapers.weremoto import WeRemotoScraper
    from scrapers.mandy import MandyScraper
    from scrapers.productionhub import ProductionHubScraper
    from scrapers.new_es_boards import (
        DomestikaScraper,
        HacesfaltaScraper,
        InfoempleoScraper,
        MilanunciosScraper,
        TalentComScraper,
        RemotoJobScraper,
        TicjobScraper,
        JobFluentScraper,
        ShakersScraper,
        FeineActivaScraper,
    )
    from scrapers.freelance_platforms import (
        MaltEsScraper,
        WorkanaScraper,
        FreelancerESScraper,
        PeoplePerHourScraper,
        SoyFreelancerScraper,
    )

    # Tecnoempleo — IT + audiovisual + marketing Spain
    tecno = TecnoempleoScraper()
    for kw in ["audiovisual", "video"]:
        all_jobs += run("Tecnoempleo", tecno.search, kw, limit=LIMIT)
    for kw in KW_MKT[:2]:
        all_jobs += run("Tecnoempleo-MKT", tecno.search, kw, limit=LIMIT)

    # Domestika Jobs — solo 1 búsqueda
    all_jobs += run("Domestika", DomestikaScraper().search, "video", limit=LIMIT)

    # Infoempleo — audiovisual + marketing
    ie = InfoempleoScraper()
    for kw in KW_AV[:1]:
        all_jobs += run("Infoempleo", ie.search, kw, limit=LIMIT)
    for kw in KW_MKT[:2]:
        all_jobs += run("Infoempleo-MKT", ie.search, kw, limit=LIMIT)

    # Talent.com — audiovisual + marketing
    for kw in KW_AV[:1]:
        all_jobs += run("Talent.com", TalentComScraper().search, kw, limit=LIMIT)
    for kw in KW_MKT[:2]:
        all_jobs += run("Talent.com-MKT", TalentComScraper().search, kw, limit=LIMIT)

    # TicJob — solo 1
    all_jobs += run("TicJob", TicjobScraper().search, "video", limit=LIMIT)

    # Feina Activa — audiovisual + marketing (Barcelona/Catalunya)
    all_jobs += run(
        "FeineActiva", FeineActivaScraper().search, "audiovisual", limit=LIMIT
    )
    for kw in KW_MKT[:2]:
        all_jobs += run("FeineActiva-MKT", FeineActivaScraper().search, kw, limit=LIMIT)

    # ProductionHub — solo 1
    all_jobs += run(
        "ProductionHub", ProductionHubScraper().search, "video", limit=LIMIT
    )

    # ── Freelance platforms (solo Malt) ──
    malt = MaltEsScraper()
    for kw in ["editor video", "n8n"]:
        all_jobs += run("Malt.es", malt.search, kw, limit=LIMIT)
    for kw in ["marketing digital", "community manager"]:
        all_jobs += run("Malt.es-MKT", malt.search, kw, limit=LIMIT)

    # ══════════════════════════════════════════════════════════════
    # TIER 3: Playwright — anti-bot portals
    # ══════════════════════════════════════════════════════════════
    log.info("── TIER 3: Playwright ──")

    from scrapers.infojobs import InfoJobsScraper
    from scrapers.indeed import IndeedScraper

    infojobs = InfoJobsScraper(use_playwright=True)
    for kw in KW_AV[:2]:
        all_jobs += run(
            "InfoJobs", infojobs.search, kw, location="barcelona", limit=LIMIT
        )
        all_jobs += run(
            "InfoJobs-Remote", infojobs.search, kw, location="remoto", limit=LIMIT
        )
    for kw in KW_MKT[:2]:
        all_jobs += run(
            "InfoJobs-MKT", infojobs.search, kw, location="barcelona", limit=LIMIT
        )
        all_jobs += run(
            "InfoJobs-MKT-Remote", infojobs.search, kw, location="remoto", limit=LIMIT
        )

    indeed = IndeedScraper()
    for kw in KW_AV[:1]:
        all_jobs += run("Indeed", indeed.search, kw, location="España", limit=LIMIT)
    for kw in KW_MKT[:1]:
        all_jobs += run("Indeed-MKT", indeed.search, kw, location="Barcelona", limit=LIMIT)

    # ══════════════════════════════════════════════════════════════
    # FILTRO + DEDUPLICACIÓN
    # ══════════════════════════════════════════════════════════════
    log.info("── Procesando resultados ──")
    total_raw = len(all_jobs)

    # 1. Filtrar por fecha
    recent = [j for j in all_jobs if is_recent(j)]
    log.info(f"Scraped: {total_raw} → recientes (≤{MAX_DAYS_OLD}d): {len(recent)}")

    # 2. Deduplicar por URL
    seen: set = set()
    unique: List = []
    for j in recent:
        u = (j.url or "").strip()
        if u and u not in seen:
            seen.add(u)
            unique.append(j)
    log.info(f"Tras dedup URL: {len(recent)} → {len(unique)}")

    # ══════════════════════════════════════════════════════════════
    # GUARDAR EN BD
    # ══════════════════════════════════════════════════════════════
    log.info("── Guardando ──")
    try:
        db = _get_db()
        saved = db.save_jobs(unique)
        log.info(f"Nuevas en BD: {saved}")
    except Exception as exc:
        log.error(f"Error al guardar: {exc}")
        saved = 0

    # Log del run en Supabase
    stats = {
        "total_scraped": total_raw,
        "after_date_filter": len(recent),
        "unique_urls": len(unique),
        "saved_new": saved,
        "elapsed_s": round((datetime.utcnow() - t_start).total_seconds(), 1),
    }
    if USE_SUPABASE:
        try:
            from db.supabase_db import SupabaseDB

            SupabaseDB().log_run("full", stats)
        except Exception:
            pass

    log.info(f"=== FIN: {stats} ===")

    # ══════════════════════════════════════════════════════════════
    # SEGUNDA CAPA: Validación + resumen con Groq IA
    # ══════════════════════════════════════════════════════════════
    log.info("── Validación IA (Groq) ──")
    ai_result = {"top_offers": unique[:5], "summary": "", "validated_jobs": unique, "failed": True}
    try:
        from validators.groq_validator import validate_and_summarize
        ai_result = validate_and_summarize(unique)
    except Exception as exc:
        log.warning(f"Groq validator error: {exc}")

    # ══════════════════════════════════════════════════════════════
    # ENVIAR EMAIL DE NOTIFICACIÓN
    # ══════════════════════════════════════════════════════════════
    _send_email_notification(unique, stats, ai_result)

    return 0


def _job_card_html(j, highlight: bool = False) -> str:
    """Genera el HTML de una tarjeta de oferta."""
    border_color = "#e63946" if highlight else "#4a90d9"
    relevance = getattr(j, "_ai_relevance", "")
    salary = getattr(j, "_ai_salary", None)
    contract = getattr(j, "_ai_contract", "")
    ai_summary = getattr(j, "_ai_summary", "")
    requirements = getattr(j, "_ai_requirements", [])

    extras = ""
    if contract and contract != "desconocido":
        extras += f'<span style="background:#f0f4ff;color:#4a90d9;padding:2px 8px;border-radius:12px;font-size:12px;margin-right:6px">{contract}</span>'
    if salary:
        extras += f'<span style="background:#f0fff4;color:#38a169;padding:2px 8px;border-radius:12px;font-size:12px;margin-right:6px">{salary}</span>'
    if relevance == "alta":
        extras += '<span style="background:#fff5f5;color:#e63946;padding:2px 8px;border-radius:12px;font-size:12px">★ Relevante</span>'

    req_html = ""
    if requirements:
        req_items = "".join(f"<li>{r}</li>" for r in requirements[:4])
        req_html = f'<ul style="margin:6px 0 0 0;padding-left:18px;font-size:13px;color:#555">{req_items}</ul>'

    summary_html = f'<p style="margin:6px 0 0 0;font-size:13px;color:#444;font-style:italic">{ai_summary}</p>' if ai_summary else ""

    return f"""
<div style="border-left:4px solid {border_color};padding:12px 16px;margin-bottom:12px;background:#fafafa;border-radius:0 6px 6px 0">
  <a href="{j.url or '#'}" style="font-size:16px;font-weight:bold;color:#1a1a2e;text-decoration:none">{j.title or 'Sin título'}</a>
  <div style="margin-top:4px;font-size:13px;color:#666">
    <strong>{j.company or 'Empresa desconocida'}</strong>
    {' · ' + (j.location or '') if j.location else ''}
    {' · ' + str(j.source or '') if j.source else ''}
    {' · ' + str(j.date_posted or '') if j.date_posted else ''}
  </div>
  <div style="margin-top:8px">{extras}</div>
  {summary_html}
  {req_html}
</div>"""


def _group_jobs_by_category(jobs: List) -> dict:
    """Agrupa ofertas por categoría según source/keywords."""
    groups = {"audiovisual": [], "marketing": [], "freelance": [], "remoto": [], "otros": []}
    for j in jobs:
        src = (getattr(j, "source", "") or "").lower()
        title = (getattr(j, "title", "") or "").lower()
        loc = (getattr(j, "location", "") or "").lower()
        if any(x in src for x in ["malt", "workana", "freelancer", "peopleperhour", "soyfreelancer"]):
            groups["freelance"].append(j)
        elif any(x in src for x in ["remoteok", "workingnomads", "jobspresso", "remoteco", "weremoto", "remoto"]) or "remot" in loc:
            groups["remoto"].append(j)
        elif any(x in title for x in ["marketing", "community", "seo", "social media", "content", "brand", "paid"]):
            groups["marketing"].append(j)
        elif any(x in title for x in ["video", "audio", "camara", "foto", "produccion", "montaje", "editor", "realizador"]):
            groups["audiovisual"].append(j)
        else:
            groups["otros"].append(j)
    return groups


def _send_email_notification(jobs: List, stats: dict, ai_result: dict = None):
    """Envía email HTML con las nuevas ofertas y resumen IA."""
    from_email = os.environ.get("ALERT_EMAIL_FROM")
    from_password = os.environ.get("ALERT_EMAIL_PASSWORD")
    to_email = os.environ.get("ALERT_EMAIL_TO", "aitorpalacios93@gmail.com")

    log.info(f"Email config - From: {from_email}, To: {to_email}")

    if not from_email or not from_password:
        log.warning("Email no configurado: ALERT_EMAIL_FROM/PASSWORD no definidos")
        return

    if ai_result is None:
        ai_result = {"top_offers": jobs[:5], "summary": "", "validated_jobs": jobs, "failed": True}

    try:
        today = datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")

        if not jobs:
            subject = "FeinaAP: No hay nuevas ofertas"
            html_body = f"""
<html><body style="font-family:Arial,sans-serif;max-width:680px;margin:auto;color:#222">
  <div style="background:#1a1a2e;color:white;padding:20px 24px;border-radius:8px 8px 0 0">
    <h1 style="margin:0;font-size:22px">FeinaAP</h1>
    <p style="margin:4px 0 0 0;opacity:0.8">{today}</p>
  </div>
  <div style="padding:24px;border:1px solid #eee;border-top:none;border-radius:0 0 8px 8px">
    <p>No se han encontrado nuevas ofertas en esta ejecución.</p>
    <p style="font-size:12px;color:#999">Stats: {stats}</p>
  </div>
</body></html>"""
            plain_body = f"FeinaAP {today}\nNo hay nuevas ofertas.\nStats: {stats}"
        else:
            top_offers = ai_result.get("top_offers", jobs[:5])
            ai_summary = ai_result.get("summary", "")
            ai_failed = ai_result.get("failed", True)
            groups = _group_jobs_by_category(jobs)

            subject = f"FeinaAP: {len(jobs)} nuevas ofertas — {today[:5]}"

            # Cabecera
            summary_block = ""
            if ai_summary and not ai_failed:
                summary_block = f"""
<div style="background:#f0f7ff;border-left:4px solid #4a90d9;padding:14px 18px;margin-bottom:20px;border-radius:0 6px 6px 0">
  <strong style="color:#4a90d9">Resumen del mercado laboral (IA)</strong>
  <p style="margin:8px 0 0 0;color:#333;font-size:14px">{ai_summary}</p>
</div>"""

            # Top ofertas
            top_cards = "".join(_job_card_html(j, highlight=True) for j in top_offers[:3])

            # Ofertas por categoría
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
<html><body style="font-family:Arial,sans-serif;max-width:680px;margin:auto;color:#222;line-height:1.5">
  <div style="background:#1a1a2e;color:white;padding:20px 24px;border-radius:8px 8px 0 0">
    <h1 style="margin:0;font-size:22px">FeinaAP</h1>
    <p style="margin:4px 0 0 0;opacity:0.8">{today} · <strong>{len(jobs)} nuevas ofertas</strong></p>
  </div>
  <div style="padding:24px;border:1px solid #eee;border-top:none;border-radius:0 0 8px 8px">
    {summary_block}
    <h2 style="color:#e63946;margin-top:0">Top ofertas destacadas</h2>
    {top_cards}
    {category_sections}
    {more_text}
    <hr style="border:none;border-top:1px solid #eee;margin:24px 0">
    <p style="font-size:11px;color:#aaa">Stats: scraped={stats.get('total_scraped',0)} · filtradas={stats.get('after_date_filter',0)} · únicas={stats.get('unique_urls',0)} · guardadas={stats.get('saved_new',0)} · {stats.get('elapsed_s',0)}s · IA={'OK' if not ai_failed else 'sin Groq'}</p>
  </div>
</body></html>"""

            # Fallback texto plano
            plain_lines = [f"FeinaAP — {today} — {len(jobs)} nuevas ofertas"]
            if ai_summary:
                plain_lines += ["", "RESUMEN IA:", ai_summary]
            plain_lines += ["", "TOP OFERTAS:"]
            for j in top_offers[:3]:
                plain_lines.append(f"- {j.title} | {j.company or ''} | {j.url}")
            plain_lines += ["", f"Stats: {stats}"]
            plain_body = "\n".join(plain_lines)

        # Enviar
        msg = MIMEMultipart("alternative")
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(plain_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(from_email, from_password)
        server.send_message(msg)
        server.quit()

        log.info(f"Email enviado a {to_email}")
    except Exception as e:
        import traceback

        log.error(f"Error enviando email: {e}")
        log.error(f"Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    sys.exit(main())
