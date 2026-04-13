import requests
from bs4 import BeautifulSoup
from typing import List, Optional

from models.job import JobOffer


class ProductionHubScraper:
    BASE_URL = "https://www.productionhub.com"

    def search(
        self, keyword: str, location: str = "remote", limit: int = 50
    ) -> List[JobOffer]:
        jobs = []

        try:
            session = requests.Session()
            session.headers.update(
                {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                }
            )

            url = f"{self.BASE_URL}/jobs?keywords={keyword.replace(' ', '+')}"
            response = session.get(url, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                job_cards = soup.select("div.job-listing, div.job-result, article.job")

                for card in job_cards[:limit]:
                    job = self._parse_job_card(card)
                    if job:
                        jobs.append(job)

        except Exception as e:
            print(f"Error ProductionHUB: {e}")

        return jobs

    def _parse_job_card(self, card) -> Optional[JobOffer]:
        try:
            title_elem = card.select_one("h2 a, h3 a, a.job-title")
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)

            link_elem = title_elem
            url = link_elem.get("href", "") if link_elem else ""
            if url and not url.startswith("http"):
                url = self.BASE_URL + url

            company_elem = card.select_one("span.company, div.company")
            company = (
                company_elem.get_text(strip=True) if company_elem else "No especificada"
            )

            location_elem = card.select_one("span.location, div.location")
            location = (
                location_elem.get_text(strip=True)
                if location_elem
                else "No especificada"
            )

            desc_elem = card.select_one("p.description, p.excerpt")
            description = desc_elem.get_text(strip=True)[:500] if desc_elem else ""

            remote = "remote" in location.lower() or "home" in location.lower()

            return JobOffer(
                title=title,
                company=company,
                location=location,
                salary=None,
                description=description,
                url=url,
                source="ProductionHUB",
                date_posted=None,
                job_type="Producción audiovisual",
                remote=remote,
            )
        except Exception as e:
            return None
