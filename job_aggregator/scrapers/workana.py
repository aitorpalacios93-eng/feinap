from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from typing import List, Optional
import re
import time

from models.job import JobOffer


class WorkanaScraper:
    BASE_URL = "https://www.workana.com"

    def search(
        self, keyword: str, location: str = "espana", limit: int = 50
    ) -> List[JobOffer]:
        jobs = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                context = browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                )
                page = context.new_page()

                url = f"{self.BASE_URL}/jobs?keyword={keyword.replace(' ', '+')}&page=1"
                page.goto(url, timeout=30000)
                page.wait_for_load_state("networkidle", timeout=15000)
                time.sleep(2)

                page_content = page.content()
                context.close()
                browser.close()

                soup = BeautifulSoup(page_content, "html.parser")
                job_cards = soup.select("div.job-card, li.job-item, article.job")

                for card in job_cards[:limit]:
                    job = self._parse_job_card(card)
                    if job:
                        jobs.append(job)

        except Exception as e:
            print(f"Error Workana: {e}")

        return jobs

    def _parse_job_card(self, card) -> Optional[JobOffer]:
        try:
            title_elem = card.select_one("h2.title a, h3.title a, a.job-title")
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            url = title_elem.get("href", "")
            if url and not url.startswith("http"):
                url = self.BASE_URL + url

            company_elem = card.select_one("span.name a, span.company-name")
            company = company_elem.get_text(strip=True) if company_elem else "Freelance"

            budget_elem = card.select_one("span.budget, div.budget")
            salary = budget_elem.get_text(strip=True) if budget_elem else None

            desc_elem = card.select_one("p.description, p.excerpt")
            description = desc_elem.get_text(strip=True) if desc_elem else ""

            return JobOffer(
                title=title,
                company=company,
                location="Remote",
                salary=salary,
                description=description[:500],
                url=url,
                source="Workana",
                date_posted=None,
                job_type="Freelance",
                remote=True,
            )
        except Exception as e:
            return None
