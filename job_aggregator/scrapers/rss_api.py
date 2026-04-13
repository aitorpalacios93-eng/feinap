"""
Tier 1 scrapers: RSS feeds y JSON APIs públicas.
Siempre incluyen fecha de publicación, no requieren browser.

Portales cubiertos:
  - RemoteOK     → JSON API pública
  - WorkingNomads → RSS feed
  - Jobspresso    → RSS feed
  - Remote.co     → RSS feed
  - Adzuna ES     → REST API (requiere ADZUNA_APP_ID / ADZUNA_APP_KEY en env)
"""

import os
import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Optional

from models.job import JobOffer


# ── Utilidades ────────────────────────────────────────────────────────────────

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _session(json_api: bool = False) -> requests.Session:
    s = requests.Session()
    headers = dict(_HEADERS)
    if json_api:
        headers["Accept"] = "application/json"
    s.headers.update(headers)
    return s


def _parse_struct_time(st) -> Optional[datetime]:
    if st:
        try:
            return datetime(*st[:6])
        except Exception:
            pass
    return None


# ── RemoteOK JSON API ─────────────────────────────────────────────────────────


class RemoteOKScraper:
    """
    RemoteOK ofrece una API JSON pública: https://remoteok.com/api
    Tags útiles: video, audio, film, photography, animation, design, media
    """

    API_URL = "https://remoteok.com/api"

    def search_api(self, tag: str = "video", limit: int = 30) -> List[JobOffer]:
        jobs: List[JobOffer] = []
        try:
            url = f"{self.API_URL}?tags={tag}"
            r = _session(json_api=True).get(url, timeout=15)
            if r.status_code != 200:
                return jobs
            data = r.json()
            # El primer elemento es metadata
            for item in data[1 : limit + 1]:
                if not isinstance(item, dict):
                    continue
                date_posted = None
                raw_date = item.get("date") or item.get("epoch")
                if raw_date:
                    try:
                        if isinstance(raw_date, (int, float)):
                            date_posted = datetime.utcfromtimestamp(raw_date)
                        else:
                            date_posted = datetime.fromisoformat(
                                str(raw_date).replace("Z", "+00:00")
                            )
                    except Exception:
                        pass

                jobs.append(
                    JobOffer(
                        title=item.get("position", ""),
                        company=item.get("company", "No especificada"),
                        location="Remote",
                        salary=item.get("salary"),
                        description=(item.get("description") or "")[:1000],
                        url=item.get("url")
                        or f"https://remoteok.com/remote-jobs/{item.get('id', '')}",
                        source="RemoteOK",
                        date_posted=date_posted,
                        job_type="Remote",
                        remote=True,
                        source_category="remoto_internacional",
                    )
                )
        except Exception as e:
            print(f"[RemoteOK] Error: {e}")
        return jobs


# ── RSS genérico ──────────────────────────────────────────────────────────────


class RSSJobScraper:
    """
    Scraper RSS genérico para portales de empleo remoto.
    Uso:
        scraper = RSSJobScraper("WorkingNomads", "https://www.workingnomads.com/feed", "remoto_internacional")
        jobs = scraper.get_jobs(limit=50)
    """

    def __init__(self, name: str, feed_url: str, source_category: str):
        self.name = name
        self.feed_url = feed_url
        self.source_category = source_category

    def get_jobs(self, limit: int = 50) -> List[JobOffer]:
        jobs: List[JobOffer] = []
        try:
            # Usar requests para descargar el feed (evita problemas SSL en macOS)
            try:
                r = _session().get(self.feed_url, timeout=20)
                feed = feedparser.parse(r.text)
            except Exception:
                feed = feedparser.parse(self.feed_url)
            for entry in feed.entries[:limit]:
                date_posted = _parse_struct_time(
                    getattr(entry, "published_parsed", None)
                    or getattr(entry, "updated_parsed", None)
                )

                desc = ""
                if hasattr(entry, "summary"):
                    desc = BeautifulSoup(entry.summary, "html.parser").get_text()[:1000]
                elif hasattr(entry, "content"):
                    desc = BeautifulSoup(
                        entry.content[0].value, "html.parser"
                    ).get_text()[:1000]

                url = getattr(entry, "link", "")
                if not url:
                    continue

                title = getattr(entry, "title", "").strip()
                company = self._extract_company(entry, desc)

                jobs.append(
                    JobOffer(
                        title=title,
                        company=company,
                        location="Remote",
                        salary=None,
                        description=desc,
                        url=url,
                        source=self.name,
                        date_posted=date_posted,
                        job_type="Remote",
                        remote=True,
                        source_category=self.source_category,
                    )
                )
        except Exception as e:
            print(f"[{self.name} RSS] Error: {e}")
        return jobs

    def _extract_company(self, entry, desc: str) -> str:
        # Intentar extraer empresa de los tags o del título
        for tag in getattr(entry, "tags", []):
            term = tag.get("term", "")
            if (
                term
                and len(term) > 1
                and term.lower() not in {"remote", "job", "jobs", "hiring", "work"}
            ):
                return term
        # Buscar patrón "at CompanyName" en título
        import re

        m = re.search(r"\bat\s+([A-Z][^–\-|]+?)(?:\s*[–\-|]|$)", entry.get("title", ""))
        if m:
            return m.group(1).strip()
        return "No especificada"


# Instancias predefinidas para los RSS más útiles
def WorkingNomadsScraper() -> RSSJobScraper:
    return RSSJobScraper(
        "WorkingNomads",
        "https://www.workingnomads.com/feed",
        "remoto_internacional",
    )


def JobspressoScraper() -> RSSJobScraper:
    return RSSJobScraper(
        "Jobspresso",
        "https://jobspresso.co/feed/",
        "remoto_internacional",
    )


def RemoteCoScraper() -> RSSJobScraper:
    return RSSJobScraper(
        "Remote.co",
        "https://remote.co/remote-jobs/feed/",
        "remoto_internacional",
    )


# ── Adzuna API ────────────────────────────────────────────────────────────────


class AdzunaScraper:
    """
    Adzuna API gratuita — 60+ ofertas de empleo ES con fecha incluida.
    App ID: 48d81a6e (añadir como secret ADZUNA_APP_ID en GitHub)
    App Key: añadir como secret ADZUNA_APP_KEY en GitHub
    """

    BASE_URL = "https://api.adzuna.com/v1/api/jobs/es/search"
    _DEFAULT_APP_ID = "48d81a6e"

    def search(self, keyword: str, limit: int = 20) -> List[JobOffer]:
        jobs: List[JobOffer] = []
        app_id = os.environ.get("ADZUNA_APP_ID") or self._DEFAULT_APP_ID
        app_key = os.environ.get("ADZUNA_APP_KEY")
        if not app_key:
            print("[Adzuna] ADZUNA_APP_KEY no configurada, saltando.")
            return jobs

        try:
            params = {
                "app_id": app_id,
                "app_key": app_key,
                "what": keyword,
                "results_per_page": min(limit, 50),
            }
            r = _session(json_api=True).get(self.BASE_URL, params=params, timeout=20)
            if r.status_code != 200:
                print(f"[Adzuna] HTTP {r.status_code}")
                return jobs

            data = r.json()
            for item in data.get("results", []):
                date_posted = None
                if item.get("created"):
                    try:
                        date_posted = datetime.fromisoformat(
                            item["created"].replace("Z", "+00:00")
                        )
                    except Exception:
                        pass

                salary_min = item.get("salary_min")
                salary_max = item.get("salary_max")
                salary = None
                if salary_min or salary_max:
                    salary = f"{salary_min or '?'} – {salary_max or '?'} €/año"

                jobs.append(
                    JobOffer(
                        title=item.get("title", ""),
                        company=item.get("company", {}).get(
                            "display_name", "No especificada"
                        ),
                        location=item.get("location", {}).get("display_name", "España"),
                        salary=salary,
                        description=(item.get("description") or "")[:1000],
                        url=item.get("redirect_url", ""),
                        source="Adzuna",
                        date_posted=date_posted,
                        job_type=item.get("contract_time", ""),
                        remote="remote" in (item.get("description") or "").lower()
                        or "teletrabajo" in (item.get("description") or "").lower(),
                        source_category="empleo_general_es",
                    )
                )
        except Exception as e:
            print(f"[Adzuna] Error: {e}")
        return jobs
