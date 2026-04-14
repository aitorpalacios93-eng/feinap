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

    # Jooble API — solo las keywords principales
    jooble = JoobleAPI()
    jooble_kws = KW_AV[:2]  # Solo 2 keywords
    for kw in jooble_kws:
        all_jobs += run("Jooble", jooble.search, kw, location="España", limit=20)

    # Adzuna API (opcional, necesita secrets ADZUNA_APP_ID + ADZUNA_APP_KEY)
    if os.environ.get("ADZUNA_APP_ID"):
        adzuna = AdzunaScraper()
        for kw in KW_AV[:4]:
            all_jobs += run("Adzuna", adzuna.search, kw, limit=20)

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

    # Tecnoempleo — IT + audiovisual Spain
    tecno = TecnoempleoScraper()
    for kw in ["audiovisual", "video"]:
        all_jobs += run("Tecnoempleo", tecno.search, kw, limit=LIMIT)

    # Domestika Jobs — solo 1 búsqueda
    all_jobs += run("Domestika", DomestikaScraper().search, "video", limit=LIMIT)

    # Infoempleo — solo 1 keyword
    ie = InfoempleoScraper()
    for kw in KW_AV[:1]:
        all_jobs += run("Infoempleo", ie.search, kw, limit=LIMIT)

    # Talent.com — solo 1
    for kw in KW_AV[:1]:
        all_jobs += run("Talent.com", TalentComScraper().search, kw, limit=LIMIT)

    # TicJob — solo 1
    all_jobs += run("TicJob", TicjobScraper().search, "video", limit=LIMIT)

    # Feina Activa — solo 1
    all_jobs += run(
        "FeineActiva", FeineActivaScraper().search, "audiovisual", limit=LIMIT
    )

    # ProductionHub — solo 1
    all_jobs += run(
        "ProductionHub", ProductionHubScraper().search, "video", limit=LIMIT
    )

    # ── Freelance platforms (solo Malt) ──
    malt = MaltEsScraper()
    for kw in ["editor video", "n8n"]:
        all_jobs += run("Malt.es", malt.search, kw, limit=LIMIT)

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

    indeed = IndeedScraper()
    for kw in KW_AV[:1]:
        all_jobs += run("Indeed", indeed.search, kw, location="España", limit=LIMIT)

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
    # ENVIAR EMAIL DE NOTIFICACIÓN
    # ══════════════════════════════════════════════════════════════
    _send_email_notification(unique, stats)

    return 0


def _send_email_notification(jobs: List, stats: dict):
    """Envía email con las nuevas ofertas."""
    from_email = os.environ.get("ALERT_EMAIL_FROM")
    from_password = os.environ.get("ALERT_EMAIL_PASSWORD")
    to_email = os.environ.get("ALERT_EMAIL_TO", "aitorpalacios93@gmail.com")

    log.info(f"Email config - From: {from_email}, To: {to_email}")

    if not from_email or not from_password:
        log.warning("Email no configurado: ALERT_EMAIL_FROM/PASSWORD no definidos")
        return

    try:
        # Construir cuerpo del email
        if not jobs:
            subject = "FeinaAP: No hay nuevas ofertas"
            body = f"""Hola,

No se han encontrado nuevas ofertas de empleo en esta ejecución.

---
Stats: {stats}
"""
        else:
            jobs_limited = jobs[:30]  # Máximo 30 ofertas en el email
            jobs_list = "\n\n".join(
                f"🎬 **{j.title}**\n{j.company or 'Empresa desconocida'}\n📍 {j.location or 'Sin ubicación'}\n🔗 {j.url}"
                for j in jobs_limited
            )
            more = f"\n... y {len(jobs) - 30} más" if len(jobs) > 30 else ""
            subject = f"FeinaAP: {len(jobs)} nuevas ofertas de empleo"
            body = f"""Hola,

Se han encontrado **{len(jobs)}** nuevas ofertas de empleo:{jobs_list}{more}

---
Stats: {stats}
"""

        # Enviar
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

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
