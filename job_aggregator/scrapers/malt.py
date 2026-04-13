import requests
from bs4 import BeautifulSoup
from typing import List, Optional
import re
import time

from models.job import JobOffer


class MaltScraper:
    BASE_URL = "https://www.malt.com"

    def search(
        self, keyword: str, location: str = "remote", limit: int = 50
    ) -> List[JobOffer]:
        jobs = []

        try:
            session = requests.Session()
            session.headers.update(
                {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                }
            )

            url = f"{self.BASE_URL}/search/missions?query={keyword.replace(' ', '+')}"
            response = session.get(url, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                job_cards = soup.select("div.mission-card, div.search-result-item")

                for card in job_cards[:limit]:
                    job = self._parse_job_card(card)
                    if job:
                        jobs.append(job)

        except Exception as e:
            print(f"Error Malt: {e}")

        return jobs

    def _parse_job_card(self, card) -> Optional[JobOffer]:
        try:
            title_elem = card.select_one("h3, h2.title")
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)

            link_elem = card.select_one("a")
            url = link_elem.get("href", "") if link_elem else ""
            if url and not url.startswith("http"):
                url = self.BASE_URL + url

            company_elem = card.select_one("span.company-name, span.client")
            company = (
                company_elem.get_text(strip=True) if company_elem else "No especificada"
            )

            rate_elem = card.select_one("span.rate, div.rate")
            salary = rate_elem.get_text(strip=True) if rate_elem else None

            desc_elem = card.select_one("p.description, p.excerpt")
            description = desc_elem.get_text(strip=True)[:500] if desc_elem else ""

            return JobOffer(
                title=title,
                company=company,
                location="Remote",
                salary=salary,
                description=description,
                url=url,
                source="Malt",
                date_posted=None,
                job_type="Freelance",
                remote=True,
            )
        except Exception as e:
            return None
