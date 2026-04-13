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

KW_AV    = KW["audiovisual"]       # Keywords audiovisual
KW_CREAT = KW["creative_remote"]   # Video editor remoto
KW_N8N   = KW["n8n_automation"]    # n8n / automatización
KW_UGC   = KW["ugc"]               # UGC creator
KW_VA    = KW["virtual_assistant"] # Asistente virtual


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
    d = job.date_posted.date() if isinstance(job.date_posted, datetime) else job.date_posted
    return d >= cutoff


def run(name: str, fn, *args, **kwargs) -> List:
    """Ejecuta un scraper con manejo de errores y logging."""
    try:
        t0 = time.time()
        jobs = fn(*args, **kwargs) or []
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
        RemoteOKScraper, RSSJobScraper,
        WorkingNomadsScraper, JobspressoScraper, RemoteCoScraper,
        AdzunaScraper,
    )
    from scrapers.jooble_api import JoobleAPI

    # RemoteOK JSON API — portales: remoto_internacional
    rok = RemoteOKScraper()
    for tag in ["video", "audio", "film", "photography", "animation", "media"]:
        all_jobs += run("RemoteOK", rok.search_api, tag, limit=LIMIT)

    # RSS feeds de empleo remoto
    for scraper_fn in [WorkingNomadsScraper, JobspressoScraper, RemoteCoScraper]:
        scraper = scraper_fn()
        all_jobs += run(scraper.name, scraper.get_jobs, limit=LIMIT)

    # Jooble API — agrega InfoJobs, Indeed, LinkedIn, Monster, Milanuncios y 30+ portales ES
    jooble = JoobleAPI()
    jooble_kws = KW_AV[:5] + KW_N8N[:2] + KW_VA[:2] + KW_UGC[:1]
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
        DomestikaScraper, HacesfaltaScraper, InfoempleoScraper,
        MilanunciosScraper, TalentComScraper, RemotoJobScraper,
        TicjobScraper, JobFluentScraper, ShakersScraper, FeineActivaScraper,
    )
    from scrapers.freelance_platforms import (
        MaltEsScraper, WorkanaScraper, FreelancerESScraper,
        PeoplePerHourScraper, SoyFreelancerScraper,
    )

    # Tecnoempleo — IT + audiovisual Spain
    tecno = TecnoempleoScraper()
    for kw in ["audiovisual", "video", "sonido", "n8n"]:
        all_jobs += run("Tecnoempleo", tecno.search, kw, limit=LIMIT)

    # Domestika Jobs — creativo / audiovisual
    all_jobs += run("Domestika", DomestikaScraper().search, "audiovisual", limit=LIMIT)
    all_jobs += run("Domestika", DomestikaScraper().search, "video", limit=LIMIT)

    # Hacesfalta — social / ONG
    all_jobs += run("Hacesfalta", HacesfaltaScraper().search, "audiovisual", limit=LIMIT)

    # Infoempleo — gran portal generalista ES
    ie = InfoempleoScraper()
    for kw in KW_AV[:4]:
        all_jobs += run("Infoempleo", ie.search, kw, limit=LIMIT)

    # Milanuncios — clasificados
    all_jobs += run("Milanuncios", MilanunciosScraper().search, "audiovisual", limit=LIMIT)
    all_jobs += run("Milanuncios", MilanunciosScraper().search, "editor video", limit=LIMIT)

    # Talent.com España — agregador
    for kw in KW_AV[:3]:
        all_jobs += run("Talent.com", TalentComScraper().search, kw, limit=LIMIT)

    # RemotoJOB — teletrabajo ES
    all_jobs += run("RemotoJOB", RemotoJobScraper().search, "video", limit=LIMIT)
    all_jobs += run("RemotoJOB", RemotoJobScraper().search, "audiovisual", limit=LIMIT)

    # TicJob — tech ES
    all_jobs += run("TicJob", TicjobScraper().search, "audiovisual", limit=LIMIT)
    all_jobs += run("TicJob", TicjobScraper().search, "n8n", limit=LIMIT)

    # JobFluent — startups ES
    all_jobs += run("JobFluent", JobFluentScraper().search, "audiovisual", limit=LIMIT)

    # Shakers — proyectos tech freelance ES
    shakers = ShakersScraper()
    for kw in ["n8n", "automatizacion", "video editor"]:
        all_jobs += run("Shakers", shakers.search, kw, limit=LIMIT)

    # Feina Activa — SOC Catalunya
    all_jobs += run("FeineActiva", FeineActivaScraper().search, "audiovisual", limit=LIMIT)

    # WeRemoto — remoto LATAM
    all_jobs += run("WeRemoto", WeRemotoScraper().search, "video editor", limit=LIMIT)

    # Mandy — producción audiovisual internacional
    all_jobs += run("Mandy", MandyScraper().search, "video", limit=LIMIT)

    # ProductionHub — producción audiovisual EE.UU. / global
    all_jobs += run("ProductionHub", ProductionHubScraper().search, "video", limit=LIMIT)

    # ── Freelance platforms ──
    malt = MaltEsScraper()
    for kw in ["editor video", "n8n", "asistente virtual", "videografo"]:
        all_jobs += run("Malt.es", malt.search, kw, limit=LIMIT)

    workana = WorkanaScraper()
    for kw in ["video", "n8n", "automatizacion", "asistente virtual"]:
        all_jobs += run("Workana", workana.search, kw, limit=LIMIT)

    freelancer = FreelancerESScraper()
    for kw in ["video editing", "n8n", "asistente virtual", "audiovisual"]:
        all_jobs += run("Freelancer.es", freelancer.search, kw, limit=LIMIT)

    pph = PeoplePerHourScraper()
    for kw in ["video editor", "content creator", "virtual assistant"]:
        all_jobs += run("PeoplePerHour", pph.search, kw, limit=LIMIT)

    all_jobs += run("SoyFreelancer", SoyFreelancerScraper().search, "audiovisual", limit=LIMIT)
    all_jobs += run("SoyFreelancer", SoyFreelancerScraper().search, "video", limit=LIMIT)

    # ══════════════════════════════════════════════════════════════
    # TIER 3: Playwright — anti-bot portals
    # ══════════════════════════════════════════════════════════════
    log.info("── TIER 3: Playwright ──")

    from scrapers.infojobs import InfoJobsScraper
    from scrapers.indeed import IndeedScraper

    infojobs = InfoJobsScraper(use_playwright=True)
    for kw in KW_AV[:4]:
        all_jobs += run("InfoJobs", infojobs.search, kw, location="barcelona", limit=LIMIT)
    # También buscar n8n y VA en InfoJobs
    for kw in KW_N8N[:2] + KW_VA[:1]:
        all_jobs += run("InfoJobs", infojobs.search, kw, location="espana", limit=LIMIT)

    indeed = IndeedScraper()
    for kw in KW_AV[:3] + KW_N8N[:1]:
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
        "total_scraped":    total_raw,
        "after_date_filter": len(recent),
        "unique_urls":      len(unique),
        "saved_new":        saved,
        "elapsed_s":        round((datetime.utcnow() - t_start).total_seconds(), 1),
    }
    if USE_SUPABASE:
        try:
            from db.supabase_db import SupabaseDB
            SupabaseDB().log_run("full", stats)
        except Exception:
            pass

    log.info(f"=== FIN: {stats} ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
