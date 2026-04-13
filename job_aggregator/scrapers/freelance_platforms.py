"""
Tier 2 scrapers: plataformas freelance.

Portales:
  - Malt.es         (misiones freelance, fix URL de malt.com → malt.es)
  - Workana         (LATAM + España, requests en lugar de Playwright)
  - Freelancer.es   (proyectos de freelance)
  - PeoplePerHour   (proyectos freelance globales)
  - SoyFreelancer   (España + LATAM)
"""
import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta
from typing import List, Optional

from models.job import JobOffer


_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": _UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    })
    return s


def _parse_date(text: str) -> Optional[date]:
    if not text:
        return None
    text = text.lower().strip()
    today = date.today()
    if any(w in text for w in ["hoy", "today", "ahora", "now", "just now"]):
        return today
    if any(w in text for w in ["ayer", "yesterday"]):
        return today - timedelta(days=1)
    m = re.search(r"(\d+)\s*(hora|hour|día|dia|day|semana|week|mes|month)", text)
    if m:
        n, unit = int(m.group(1)), m.group(2)
        if "hora" in unit or "hour" in unit:
            return today
        if "día" in unit or "dia" in unit or "day" in unit:
            return today - timedelta(days=n)
        if "semana" in unit or "week" in unit:
            return today - timedelta(weeks=n)
        if "mes" in unit or "month" in unit:
            return today - timedelta(days=n * 30)
    for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
        try:
            return datetime.strptime(text[:10], fmt).date()
        except Exception:
            continue
    return None


# ── Malt.es ───────────────────────────────────────────────────────────────────

class MaltEsScraper:
    """
    https://www.malt.es — plataforma freelance líder en España/Europa.
    Usa requests; si retorna vacío, la URL puede necesitar ajuste de sesión.
    """

    BASE_URL = "https://www.malt.es"

    def search(self, keyword: str, location: str = "remote", limit: int = 25) -> List[JobOffer]:
        jobs: List[JobOffer] = []
        try:
            url = f"{self.BASE_URL}/search/missions?query={keyword.replace(' ', '+')}"
            r = _session().get(url, timeout=20)
            if r.status_code != 200:
                print(f"[Malt.es] HTTP {r.status_code}")
                return jobs
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select(
                "article[class*='mission'], div[class*='MissionCard'], li[class*='mission']"
            )
            for card in cards[:limit]:
                link = card.select_one("a[href]")
                title_el = card.select_one("h2, h3, [class*='title'], [class*='Title']")
                if not (link and title_el):
                    continue
                href = link.get("href", "")
                if not href.startswith("http"):
                    href = self.BASE_URL + href
                rate_el = card.select_one("[class*='rate'], [class*='Rate'], [class*='price']")
                date_el = card.select_one("time, [class*='date']")
                desc_el = card.select_one("p, [class*='description']")
                jobs.append(JobOffer(
                    title=title_el.get_text(strip=True),
                    company="Cliente Malt",
                    location="Remoto",
                    salary=rate_el.get_text(strip=True) if rate_el else None,
                    description=desc_el.get_text(strip=True)[:500] if desc_el else "",
                    url=href,
                    source="Malt.es",
                    date_posted=_parse_date(date_el.get_text(strip=True) if date_el else ""),
                    job_type="Freelance",
                    remote=True,
                    source_category="freelance_multiservicio",
                ))
        except Exception as e:
            print(f"[Malt.es] Error: {e}")
        return jobs


# ── Workana ───────────────────────────────────────────────────────────────────

class WorkanaScraper:
    """
    https://www.workana.com — freelance LATAM y España.
    Versión requests (más rápida que Playwright, sin browser overhead).
    Si retorna vacío, Workana puede requerir cookies de sesión.
    """

    BASE_URL = "https://www.workana.com"

    def search(self, keyword: str, location: str = "es", limit: int = 25) -> List[JobOffer]:
        jobs: List[JobOffer] = []
        try:
            url = f"{self.BASE_URL}/jobs?search={keyword.replace(' ', '+')}&language=es&page=1"
            r = _session().get(url, timeout=20)
            if r.status_code != 200:
                print(f"[Workana] HTTP {r.status_code}")
                return jobs
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select("div[class*='jobs-list'] > div, article.job, div.job-card")
            for card in cards[:limit]:
                link = card.select_one("a[href]")
                title_el = card.select_one("h2, h3, .job-title, [class*='title']")
                if not (link and title_el):
                    continue
                href = link.get("href", "")
                if not href.startswith("http"):
                    href = self.BASE_URL + href
                budget_el = card.select_one("[class*='budget'], [class*='price']")
                date_el = card.select_one("time, [class*='date'], [class*='time']")
                desc_el = card.select_one("p, [class*='description']")
                jobs.append(JobOffer(
                    title=title_el.get_text(strip=True),
                    company="Cliente Workana",
                    location="Remoto",
                    salary=budget_el.get_text(strip=True) if budget_el else None,
                    description=desc_el.get_text(strip=True)[:500] if desc_el else "",
                    url=href,
                    source="Workana",
                    date_posted=_parse_date(date_el.get_text(strip=True) if date_el else ""),
                    job_type="Freelance",
                    remote=True,
                    source_category="freelance_multiservicio",
                ))
        except Exception as e:
            print(f"[Workana] Error: {e}")
        return jobs


# ── Freelancer.es ─────────────────────────────────────────────────────────────

class FreelancerESScraper:
    """
    https://www.freelancer.es — proyectos freelance en español.
    """

    BASE_URL = "https://www.freelancer.es"

    def search(self, keyword: str, limit: int = 25) -> List[JobOffer]:
        jobs: List[JobOffer] = []
        try:
            url = f"{self.BASE_URL}/jobs/{keyword.replace(' ', '-').lower()}/"
            r = _session().get(url, timeout=20)
            if r.status_code != 200:
                # Intentar búsqueda directa
                url = f"{self.BASE_URL}/jobs/search/?q={keyword.replace(' ', '+')}"
                r = _session().get(url, timeout=20)
            if r.status_code != 200:
                print(f"[Freelancer.es] HTTP {r.status_code}")
                return jobs
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select(
                "div[class*='JobSearchCard'], li[class*='job-item'], article.project"
            )
            for card in cards[:limit]:
                link = card.select_one("a[href]")
                title_el = card.select_one("h2, h3, [class*='title']")
                if not (link and title_el):
                    continue
                href = link.get("href", "")
                if not href.startswith("http"):
                    href = self.BASE_URL + href
                budget_el = card.select_one("[class*='budget'], [class*='price'], [class*='amount']")
                date_el = card.select_one("time, [class*='date'], [class*='time']")
                desc_el = card.select_one("p, [class*='description']")
                jobs.append(JobOffer(
                    title=title_el.get_text(strip=True),
                    company="Cliente Freelancer",
                    location="Remoto",
                    salary=budget_el.get_text(strip=True) if budget_el else None,
                    description=desc_el.get_text(strip=True)[:500] if desc_el else "",
                    url=href,
                    source="Freelancer.es",
                    date_posted=_parse_date(date_el.get_text(strip=True) if date_el else ""),
                    job_type="Freelance",
                    remote=True,
                    source_category="freelance_multiservicio",
                ))
        except Exception as e:
            print(f"[Freelancer.es] Error: {e}")
        return jobs


# ── PeoplePerHour ─────────────────────────────────────────────────────────────

class PeoplePerHourScraper:
    """
    https://www.peopleperhour.com — proyectos freelance internacionales.
    """

    BASE_URL = "https://www.peopleperhour.com"

    def search(self, keyword: str, limit: int = 25) -> List[JobOffer]:
        jobs: List[JobOffer] = []
        try:
            url = f"{self.BASE_URL}/freelance-jobs?keyword={keyword.replace(' ', '+')}"
            r = _session().get(url, timeout=20)
            if r.status_code != 200:
                print(f"[PeoplePerHour] HTTP {r.status_code}")
                return jobs
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select(
                "li[class*='listing'], article[class*='job'], div[class*='HourlyJob']"
            )
            for card in cards[:limit]:
                link = card.select_one("a[href]")
                title_el = card.select_one("h2, h3, [class*='title']")
                if not (link and title_el):
                    continue
                href = link.get("href", "")
                if not href.startswith("http"):
                    href = self.BASE_URL + href
                budget_el = card.select_one("[class*='budget'], [class*='price']")
                date_el = card.select_one("time, [class*='date']")
                jobs.append(JobOffer(
                    title=title_el.get_text(strip=True),
                    company="Cliente PPH",
                    location="Remoto",
                    salary=budget_el.get_text(strip=True) if budget_el else None,
                    description="",
                    url=href,
                    source="PeoplePerHour",
                    date_posted=_parse_date(date_el.get_text(strip=True) if date_el else ""),
                    job_type="Freelance",
                    remote=True,
                    source_category="freelance_multiservicio",
                ))
        except Exception as e:
            print(f"[PeoplePerHour] Error: {e}")
        return jobs


# ── SoyFreelancer ─────────────────────────────────────────────────────────────

class SoyFreelancerScraper:
    """
    https://www.soyfreelancer.com — plataforma freelance España + LATAM.
    """

    BASE_URL = "https://www.soyfreelancer.com"

    def search(self, keyword: str, limit: int = 25) -> List[JobOffer]:
        jobs: List[JobOffer] = []
        try:
            url = f"{self.BASE_URL}/trabajos?q={keyword.replace(' ', '+')}"
            r = _session().get(url, timeout=20)
            if r.status_code != 200:
                print(f"[SoyFreelancer] HTTP {r.status_code}")
                return jobs
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select(
                "article.project, div[class*='project'], li[class*='job']"
            )
            for card in cards[:limit]:
                link = card.select_one("a[href]")
                title_el = card.select_one("h2, h3, [class*='title']")
                if not (link and title_el):
                    continue
                href = link.get("href", "")
                if not href.startswith("http"):
                    href = self.BASE_URL + href
                date_el = card.select_one("time, [class*='date']")
                budget_el = card.select_one("[class*='budget'], [class*='price'], [class*='presupuesto']")
                jobs.append(JobOffer(
                    title=title_el.get_text(strip=True),
                    company="Cliente SoyFreelancer",
                    location="Remoto",
                    salary=budget_el.get_text(strip=True) if budget_el else None,
                    description="",
                    url=href,
                    source="SoyFreelancer",
                    date_posted=_parse_date(date_el.get_text(strip=True) if date_el else ""),
                    job_type="Freelance",
                    remote=True,
                    source_category="freelance_multiservicio",
                ))
        except Exception as e:
            print(f"[SoyFreelancer] Error: {e}")
        return jobs
