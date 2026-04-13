import requests
from bs4 import BeautifulSoup
from typing import List, Optional
import re

from models.job import JobOffer


class WeRemotoScraper:
    BASE_URL = "https://weremoto.com"

    def search(
        self, keyword: str, location: str = "latam", limit: int = 50
    ) -> List[JobOffer]:
        jobs = []

        try:
            session = requests.Session()
            session.headers.update(
                {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
                }
            )

            url = f"{self.BASE_URL}/jobs?q={keyword.replace(' ', '+')}"
            response = session.get(url, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                job_cards = soup.select("div.job-listing, div.job-card, article.job")

                for card in job_cards[:limit]:
                    job = self._parse_job_card(card)
                    if job:
                        jobs.append(job)

        except Exception as e:
            print(f"Error WeRemoto: {e}")

        return jobs

    def _parse_job_card(self, card) -> Optional[JobOffer]:
        try:
            title_elem = card.select_one("h2, h3.title a, a.job-title")
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)

            link_elem = card.select_one("a")
            url = link_elem.get("href", "") if link_elem else ""
            if url and not url.startswith("http"):
                url = self.BASE_URL + url

            company_elem = card.select_one("span.company, div.company-name")
            company = (
                company_elem.get_text(strip=True) if company_elem else "No especificada"
            )

            location_elem = card.select_one("span.location, div.location")
            location = (
                location_elem.get_text(strip=True) if location_elem else "Remote LatAm"
            )

            salary_elem = card.select_one("span.salary, div.salary")
            salary = salary_elem.get_text(strip=True) if salary_elem else None

            desc_elem = card.select_one("p.description, p.excerpt")
            description = desc_elem.get_text(strip=True)[:500] if desc_elem else ""

            return JobOffer(
                title=title,
                company=company,
                location=location,
                salary=salary,
                description=description,
                url=url,
                source="WeRemoto",
                date_posted=None,
                job_type="Remote",
                remote=True,
            )
        except Exception as e:
            return None
