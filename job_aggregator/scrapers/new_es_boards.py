"""
Tier 2 scrapers: portales españoles de empleo vía requests + BeautifulSoup.
Todos incluyen extracción de fechas relativas (hace X días, ayer, hoy…).

Portales:
  - Domestika Jobs
  - Hacesfalta (ONG / social)
  - Infoempleo
  - Milanuncios Empleo
  - Talent.com España
  - RemotoJOB
  - TicJob
  - JobFluent
  - Shakers (freelance tech)
  - Feina Activa (SOC Catalunya)
"""
import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta
from typing import List, Optional

from models.job import JobOffer


# ── Utilidades compartidas ────────────────────────────────────────────────────

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
    """Convierte texto relativo ('hace 2 días', 'ayer', 'hoy'…) o absoluto a date."""
    if not text:
        return None
    text = text.lower().strip()
    today = date.today()

    if any(w in text for w in ["hoy", "today", "ahora", "now", "just now", "hace un momento"]):
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

    for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d de %B %Y"]:
        try:
            return datetime.strptime(text[:10], fmt).date()
        except Exception:
            continue
    return None


# ── Domestika Jobs ────────────────────────────────────────────────────────────

class DomestikaScraper:
    """
    https://www.domestika.org/es/jobs
    React/SSR — el HTML contiene JSON-LD o tarjetas renderizadas.
    """

    BASE_URL = "https://www.domestika.org"

    def search(self, keyword: str = "audiovisual", limit: int = 30) -> List[JobOffer]:
        jobs: List[JobOffer] = []
        try:
            url = f"{self.BASE_URL}/es/jobs?q={keyword.replace(' ', '+')}"
            r = _session().get(url, timeout=20)
            if r.status_code != 200:
                print(f"[Domestika] HTTP {r.status_code}")
                return jobs
            soup = BeautifulSoup(r.text, "html.parser")

            # Intentar JSON-LD primero
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    import json
                    data = json.loads(script.string or "")
                    items = data if isinstance(data, list) else data.get("itemListElement", [])
                    for item in items[:limit]:
                        j = item.get("item", item)
                        title = j.get("title") or j.get("name", "")
                        if not title:
                            continue
                        jobs.append(JobOffer(
                            title=title,
                            company=j.get("hiringOrganization", {}).get("name", "No especificada")
                            if isinstance(j.get("hiringOrganization"), dict) else "No especificada",
                            location=j.get("jobLocation", {}).get("address", {}).get("addressLocality", "No especificada")
                            if isinstance(j.get("jobLocation"), dict) else "No especificada",
                            salary=None,
                            description=(j.get("description") or "")[:1000],
                            url=j.get("url", ""),
                            source="Domestika",
                            date_posted=_parse_date(j.get("datePosted", "")),
                            job_type=j.get("employmentType"),
                            remote="remote" in (j.get("description") or "").lower(),
                            source_category="empleo_sectorial_creativo_audiovisual",
                        ))
                except Exception:
                    pass

            if jobs:
                return jobs[:limit]

            # Fallback: tarjetas HTML
            cards = soup.select("article.job-card, div[class*='JobCard'], li[class*='job']")
            for card in cards[:limit]:
                link = card.select_one("a[href]")
                title_el = card.select_one("h2, h3, [class*='title']")
                if not (link and title_el):
                    continue
                href = link.get("href", "")
                if not href.startswith("http"):
                    href = self.BASE_URL + href
                jobs.append(JobOffer(
                    title=title_el.get_text(strip=True),
                    company="No especificada",
                    location="No especificada",
                    salary=None,
                    description="",
                    url=href,
                    source="Domestika",
                    date_posted=None,
                    job_type=None,
                    remote=None,
                    source_category="empleo_sectorial_creativo_audiovisual",
                ))
        except Exception as e:
            print(f"[Domestika] Error: {e}")
        return jobs


# ── Hacesfalta ────────────────────────────────────────────────────────────────

class HacesfaltaScraper:
    """
    https://www.hacesfalta.org — empleos en sector social/ONG.
    """

    BASE_URL = "https://www.hacesfalta.org"

    def search(self, keyword: str = "audiovisual", limit: int = 30) -> List[JobOffer]:
        jobs: List[JobOffer] = []
        try:
            url = f"{self.BASE_URL}/oportunidades/empleo/?q={keyword.replace(' ', '+')}"
            r = _session().get(url, timeout=20)
            if r.status_code != 200:
                print(f"[Hacesfalta] HTTP {r.status_code}")
                return jobs
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select(
                "div.job-card, article.opportunity, li.offer-item, div.oferta"
            )
            for card in cards[:limit]:
                link = card.select_one("a[href]")
                title_el = card.select_one("h2, h3, .title, .job-title")
                if not (link and title_el):
                    continue
                href = link.get("href", "")
                if not href.startswith("http"):
                    href = self.BASE_URL + href
                date_el = card.select_one(".date, .fecha, time, [class*='date']")
                company_el = card.select_one(".company, .organization, .organización")
                jobs.append(JobOffer(
                    title=title_el.get_text(strip=True),
                    company=company_el.get_text(strip=True) if company_el else "ONG / Entidad social",
                    location="España",
                    salary=None,
                    description="",
                    url=href,
                    source="Hacesfalta",
                    date_posted=_parse_date(date_el.get_text(strip=True) if date_el else ""),
                    job_type=None,
                    remote=None,
                    source_category="empleo_general_es",
                ))
        except Exception as e:
            print(f"[Hacesfalta] Error: {e}")
        return jobs


# ── Infoempleo ────────────────────────────────────────────────────────────────

class InfoempleoScraper:
    """
    https://www.infoempleo.com — segundo portal más grande de España.
    Estructura real: las ofertas están en h2 > a[href*=ofertasdetrabajo]
    """

    BASE_URL = "https://www.infoempleo.com"

    def search(self, keyword: str = "audiovisual", limit: int = 25) -> List[JobOffer]:
        jobs: List[JobOffer] = []
        try:
            kw = keyword.replace(" ", "+")
            url = f"{self.BASE_URL}/trabajo/ofertas/?busqueda={kw}"
            r = _session().get(url, timeout=20)
            if r.status_code != 200:
                print(f"[Infoempleo] HTTP {r.status_code}")
                return jobs
            soup = BeautifulSoup(r.text, "html.parser")

            # Selector real verificado: h2 > a con href que contiene "ofertasdetrabajo"
            job_links = soup.select('h2 > a[href*="ofertasdetrabajo"]')
            for link in job_links[:limit]:
                title = link.get_text(strip=True)
                href = link.get("href", "")
                if not href.startswith("http"):
                    href = self.BASE_URL + href

                # Subir al contenedor padre para extraer empresa/fecha
                card = link.parent.parent if link.parent and link.parent.parent else link.parent
                company_el = card.find(class_=lambda c: c and (
                    "empresa" in c.lower() or "company" in c.lower()
                )) if card else None
                date_el = card.find(
                    lambda t: t.name in ("time", "span") and t.get("class") and any(
                        "date" in cl.lower() or "fecha" in cl.lower()
                        for cl in t.get("class", [])
                    )
                ) if card else None

                jobs.append(JobOffer(
                    title=title,
                    company=company_el.get_text(strip=True) if company_el else "No especificada",
                    location="España",
                    salary=None,
                    description="",
                    url=href,
                    source="Infoempleo",
                    date_posted=_parse_date(date_el.get_text(strip=True) if date_el else ""),
                    job_type=None,
                    remote=None,
                    source_category="empleo_general_es",
                ))
        except Exception as e:
            print(f"[Infoempleo] Error: {e}")
        return jobs


# ── Milanuncios Empleo ────────────────────────────────────────────────────────

class MilanunciosScraper:
    """
    https://www.milanuncios.com/ofertas-de-empleo/ — clasificados de empleo.
    URL corregida en SOP: /trabajo-en-barcelona/?q=audiovisual
    """

    BASE_URL = "https://www.milanuncios.com"

    def search(self, keyword: str = "audiovisual", limit: int = 25) -> List[JobOffer]:
        jobs: List[JobOffer] = []
        try:
            kw = keyword.replace(" ", "-")
            url = f"{self.BASE_URL}/ofertas-de-empleo/?q={keyword.replace(' ', '+')}&demanda=n"
            r = _session().get(url, timeout=20)
            if r.status_code != 200:
                print(f"[Milanuncios] HTTP {r.status_code}")
                return jobs
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select(
                "article.ma-AdCard, div.ma-AdCardV2, li[class*='ad'], article[class*='ad']"
            )
            for card in cards[:limit]:
                link = card.select_one("a[href]")
                title_el = card.select_one(
                    "h2, h3, .ma-AdCard-title, [class*='title'], [class*='Title']"
                )
                if not (link and title_el):
                    continue
                href = link.get("href", "")
                if not href.startswith("http"):
                    href = self.BASE_URL + href
                date_el = card.select_one(
                    "time, .date, .fecha, [class*='date'], [class*='Date']"
                )
                location_el = card.select_one(".location, .ma-AdLocation, [class*='location']")
                jobs.append(JobOffer(
                    title=title_el.get_text(strip=True),
                    company="Particular / Empresa",
                    location=location_el.get_text(strip=True) if location_el else "España",
                    salary=None,
                    description="",
                    url=href,
                    source="Milanuncios",
                    date_posted=_parse_date(date_el.get_text(strip=True) if date_el else ""),
                    job_type=None,
                    remote=None,
                    source_category="empleo_general_es",
                ))
        except Exception as e:
            print(f"[Milanuncios] Error: {e}")
        return jobs


# ── Talent.com España ─────────────────────────────────────────────────────────

class TalentComScraper:
    """
    https://es.talent.com — agregador de empleo con buena cobertura ES.
    Estructura real verificada: article[class*="JobCard_card"]
    """

    BASE_URL = "https://es.talent.com"

    def search(self, keyword: str = "audiovisual", limit: int = 25) -> List[JobOffer]:
        jobs: List[JobOffer] = []
        try:
            url = f"{self.BASE_URL}/jobs?k={keyword.replace(' ', '+')}&l=Spain"
            r = _session().get(url, timeout=20)
            if r.status_code != 200:
                print(f"[Talent.com] HTTP {r.status_code}")
                return jobs
            soup = BeautifulSoup(r.text, "html.parser")

            # Selector real verificado
            cards = soup.select('article[class*="JobCard_card"]')
            for card in cards[:limit]:
                link = card.find("a", href=True)
                title_el = card.find(["h2", "h3"])
                if not (link and title_el):
                    continue
                href = link.get("href", "")
                if not href.startswith("http"):
                    href = self.BASE_URL + href

                # Fecha: texto "hace X días" en el atributo o texto de la tarjeta
                date_text = ""
                for el in card.find_all(string=True):
                    if "hace" in el.lower() or "última" in el.lower():
                        date_text = el.strip()
                        break

                company_el = card.find(class_=lambda c: c and (
                    "company" in c.lower() or "employer" in c.lower()
                    or "empName" in (c if isinstance(c, str) else " ".join(c))
                ))

                jobs.append(JobOffer(
                    title=title_el.get_text(strip=True),
                    company=company_el.get_text(strip=True) if company_el else "No especificada",
                    location="España",
                    salary=None,
                    description="",
                    url=href,
                    source="Talent.com",
                    date_posted=_parse_date(date_text),
                    job_type=None,
                    remote=None,
                    source_category="empleo_general_es",
                ))
        except Exception as e:
            print(f"[Talent.com] Error: {e}")
        return jobs


# ── RemotoJOB ─────────────────────────────────────────────────────────────────

class RemotoJobScraper:
    """
    https://www.remotojob.es — portal de teletrabajo en español.
    """

    BASE_URL = "https://www.remotojob.es"

    def search(self, keyword: str = "video", limit: int = 30) -> List[JobOffer]:
        jobs: List[JobOffer] = []
        try:
            url = f"{self.BASE_URL}/jobs?q={keyword.replace(' ', '+')}"
            r = _session().get(url, timeout=20)
            if r.status_code != 200:
                print(f"[RemotoJOB] HTTP {r.status_code}")
                return jobs
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select(
                "article, li[class*='job'], div[class*='job-card'], div[class*='JobCard']"
            )
            for card in cards[:limit]:
                link = card.select_one("a[href]")
                title_el = card.select_one("h2, h3, [class*='title']")
                if not (link and title_el):
                    continue
                href = link.get("href", "")
                if not href.startswith("http"):
                    href = self.BASE_URL + href
                date_el = card.select_one("time, .date, [class*='date']")
                company_el = card.select_one(".company, [class*='company']")
                jobs.append(JobOffer(
                    title=title_el.get_text(strip=True),
                    company=company_el.get_text(strip=True) if company_el else "No especificada",
                    location="Remoto España",
                    salary=None,
                    description="",
                    url=href,
                    source="RemotoJOB",
                    date_posted=_parse_date(date_el.get_text(strip=True) if date_el else ""),
                    job_type="Remoto",
                    remote=True,
                    source_category="empleo_general_es",
                ))
        except Exception as e:
            print(f"[RemotoJOB] Error: {e}")
        return jobs


# ── TicJob ────────────────────────────────────────────────────────────────────

class TicjobScraper:
    """
    https://www.ticjob.es — empleos tecnológicos en España.
    """

    BASE_URL = "https://www.ticjob.es"

    def search(self, keyword: str = "audiovisual", limit: int = 25) -> List[JobOffer]:
        jobs: List[JobOffer] = []
        try:
            url = f"{self.BASE_URL}/busqueda/?q={keyword.replace(' ', '+')}&pag=1"
            r = _session().get(url, timeout=20)
            if r.status_code != 200:
                print(f"[TicJob] HTTP {r.status_code}")
                return jobs
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select("div.oferta, article.job, li.job-item, div[class*='oferta']")
            for card in cards[:limit]:
                link = card.select_one("a[href]")
                title_el = card.select_one("h2, h3, .title, [class*='title']")
                if not (link and title_el):
                    continue
                href = link.get("href", "")
                if not href.startswith("http"):
                    href = self.BASE_URL + href
                date_el = card.select_one("time, .date, .fecha, [class*='date']")
                company_el = card.select_one(".empresa, .company, [class*='empresa']")
                location_el = card.select_one(".location, .ubicacion")
                jobs.append(JobOffer(
                    title=title_el.get_text(strip=True),
                    company=company_el.get_text(strip=True) if company_el else "No especificada",
                    location=location_el.get_text(strip=True) if location_el else "España",
                    salary=None,
                    description="",
                    url=href,
                    source="TicJob",
                    date_posted=_parse_date(date_el.get_text(strip=True) if date_el else ""),
                    job_type=None,
                    remote=None,
                    source_category="empleo_sectorial_creativo_audiovisual",
                ))
        except Exception as e:
            print(f"[TicJob] Error: {e}")
        return jobs


# ── JobFluent ─────────────────────────────────────────────────────────────────

class JobFluentScraper:
    """
    https://jobfluent.com — empleos en startups españolas.
    """

    BASE_URL = "https://jobfluent.com"

    def search(self, keyword: str = "audiovisual", limit: int = 25) -> List[JobOffer]:
        jobs: List[JobOffer] = []
        try:
            url = (
                f"{self.BASE_URL}/es-ES/jobs"
                f"?q={keyword.replace(' ', '+')}&l=Spain"
            )
            r = _session().get(url, timeout=20)
            if r.status_code != 200:
                print(f"[JobFluent] HTTP {r.status_code}")
                return jobs
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select(
                "li[class*='job'], article[class*='job'], div[class*='JobCard']"
            )
            for card in cards[:limit]:
                link = card.select_one("a[href]")
                title_el = card.select_one("h2, h3, [class*='title'], [class*='Title']")
                if not (link and title_el):
                    continue
                href = link.get("href", "")
                if not href.startswith("http"):
                    href = self.BASE_URL + href
                date_el = card.select_one("time, [class*='date'], [class*='Date']")
                company_el = card.select_one("[class*='company'], [class*='Company']")
                jobs.append(JobOffer(
                    title=title_el.get_text(strip=True),
                    company=company_el.get_text(strip=True) if company_el else "No especificada",
                    location="España",
                    salary=None,
                    description="",
                    url=href,
                    source="JobFluent",
                    date_posted=_parse_date(date_el.get_text(strip=True) if date_el else ""),
                    job_type=None,
                    remote=None,
                    source_category="empleo_sectorial_creativo_audiovisual",
                ))
        except Exception as e:
            print(f"[JobFluent] Error: {e}")
        return jobs


# ── Shakers ───────────────────────────────────────────────────────────────────

class ShakersScraper:
    """
    https://www.shakersworks.com — proyectos tech/creativo en España.
    Nota: SPA Angular — puede requerir Playwright si requests devuelve vacío.
    """

    BASE_URL = "https://www.shakersworks.com"

    def search(self, keyword: str = "video", limit: int = 25) -> List[JobOffer]:
        jobs: List[JobOffer] = []
        try:
            url = f"{self.BASE_URL}/proyectos?search={keyword.replace(' ', '+')}"
            r = _session().get(url, timeout=20)
            if r.status_code != 200:
                print(f"[Shakers] HTTP {r.status_code}")
                return jobs
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select(
                "article[class*='project'], div[class*='ProjectCard'], li[class*='project']"
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
                jobs.append(JobOffer(
                    title=title_el.get_text(strip=True),
                    company="Shakers Client",
                    location="Remoto",
                    salary=None,
                    description="",
                    url=href,
                    source="Shakers",
                    date_posted=_parse_date(date_el.get_text(strip=True) if date_el else ""),
                    job_type="Freelance",
                    remote=True,
                    source_category="automation_n8n_ai",
                ))
        except Exception as e:
            print(f"[Shakers] Error: {e}")
        return jobs


# ── Feina Activa (SOC Catalunya) ──────────────────────────────────────────────

class FeineActivaScraper:
    """
    https://feinaactiva.gencat.cat — servicio público de empleo catalán.
    Intenta la API interna primero, luego HTML si está disponible.
    """

    API_URL = "https://feinaactiva.gencat.cat/api/ofertes"

    def search(self, keyword: str = "audiovisual", limit: int = 25) -> List[JobOffer]:
        jobs: List[JobOffer] = []
        try:
            # Intentar API JSON interna
            params = {"q": keyword, "pagina": 1, "resultatsPagina": limit}
            r = _session().get(self.API_URL, params=params, timeout=20)
            if r.status_code == 200:
                try:
                    data = r.json()
                    items = data.get("ofertes") or data.get("results") or (
                        data if isinstance(data, list) else []
                    )
                    for item in items[:limit]:
                        if not isinstance(item, dict):
                            continue
                        jobs.append(JobOffer(
                            title=item.get("titol") or item.get("title", ""),
                            company=item.get("empresa") or item.get("company", "No especificada"),
                            location=item.get("municipi") or item.get("location", "Catalunya"),
                            salary=None,
                            description=(item.get("descripcio") or item.get("description", ""))[:1000],
                            url=item.get("url") or item.get("link", ""),
                            source="Feina Activa",
                            date_posted=_parse_date(item.get("dataPublicacio") or item.get("date", "")),
                            job_type=None,
                            remote=None,
                            source_category="empleo_general_es",
                        ))
                    if jobs:
                        return jobs
                except Exception:
                    pass
        except Exception as e:
            print(f"[Feina Activa] Error: {e}")
        return jobs
