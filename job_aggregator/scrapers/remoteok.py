import requests
from bs4 import BeautifulSoup
from typing import List, Optional
import re
import time

from models.job import JobOffer


class RemoteOKScraper:
    BASE_URL = "https://remoteok.com"

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

            url = f"{self.BASE_URL}/remote-jobs?search={keyword.replace(' ', '+')}"
            response = session.get(url, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                job_rows = soup.select("tr.job-row")

                for row in job_rows[:limit]:
                    job = self._parse_job_row(row)
                    if job:
                        jobs.append(job)

        except Exception as e:
            print(f"Error RemoteOK: {e}")

        return jobs

    def _parse_job_row(self, row) -> Optional[JobOffer]:
        try:
            title_elem = row.select_one("h2")
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)

            link_elem = row.select_one("a")
            url = link_elem.get("href", "") if link_elem else ""
            if url and not url.startswith("http"):
                url = self.BASE_URL + url

            company_elem = row.select_one("span.company")
            company = (
                company_elem.get_text(strip=True) if company_elem else "No especificada"
            )

            location_elem = row.select_one("span.location")
            location = location_elem.get_text(strip=True) if location_elem else "Remote"

            salary_elem = row.select_one("span.salary")
            salary = salary_elem.get_text(strip=True) if salary_elem else None

            tags = [tag.get_text(strip=True) for tag in row.select("div.tags span")]

            return JobOffer(
                title=title,
                company=company,
                location=location,
                salary=salary,
                description=" | ".join(tags),
                url=url,
                source="RemoteOK",
                date_posted=None,
                job_type="Remote",
                remote=True,
            )
        except Exception as e:
            return None
