from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from typing import List, Optional
from datetime import datetime
import re
import time

from models.job import JobOffer

class InfoJobsScraper:
    BASE_URL = "https://www.infojobs.net"
    
    def __init__(self, use_playwright: bool = True):
        self.use_playwright = use_playwright
    
    def search(self, keyword: str, location: str = "espana", limit: int = 50) -> List[JobOffer]:
        jobs = []
        
        if self.use_playwright:
            jobs = self._search_with_playwright(keyword, location, limit)
        else:
            jobs = self._search_with_requests(keyword, location, limit)
        
        return jobs
    
    def _search_with_playwright(self, keyword: str, location: str, limit: int) -> List[JobOffer]:
        jobs = []
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                url = f"{self.BASE_URL}/job-search/offers.html?keyword={keyword}&province={location}"
                page.goto(url, timeout=30000)
                page.wait_for_load_state("networkidle", timeout=15000)
                time.sleep(2)
                
                page_content = page.content()
                browser.close()
                
                soup = BeautifulSoup(page_content, 'html.parser')
                job_cards = soup.select('div.card-container')
                
                for card in job_cards[:limit]:
                    job = self._parse_job_card(card)
                    if job:
                        jobs.append(job)
                
        except Exception as e:
            print(f"Error with Playwright: {e}")
        
        return jobs
    
    def _search_with_requests(self, keyword: str, location: str, limit: int) -> List[JobOffer]:
        import requests
        
        jobs = []
        try:
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            })
            
            url = f"{self.BASE_URL}/job-search/offers.html?keyword={keyword}&province={location}"
            response = session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.select('div.card-container')
                
                for card in job_cards[:limit]:
                    job = self._parse_job_card(card)
                    if job:
                        jobs.append(job)
                        
        except Exception as e:
            print(f"Error fetching: {e}")
        
        return jobs
    
    def _parse_job_card(self, card) -> Optional[JobOffer]:
        try:
            title_elem = card.select_one('h2.title a')
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            url = title_elem.get('href', '')
            if url and not url.startswith('http'):
                url = self.BASE_URL + url
            
            company_elem = card.select_one('span[itemprop="name"]')
            company = company_elem.get_text(strip=True) if company_elem else "No especificada"
            
            location_elem = card.select_one('span[itemprop="addressLocality"]')
            location = location_elem.get_text(strip=True) if location_elem else "No especificada"
            
            salary_elem = card.select_one('span[itemprop="value"]')
            salary = salary_elem.get_text(strip=True) if salary_elem else None
            
            desc_elem = card.select_one('p.description')
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            remote = 'teletrabajo' in description.lower() or 'remoto' in description.lower()
            
            return JobOffer(
                title=title,
                company=company,
                location=location,
                salary=salary,
                description=description,
                url=url,
                source="InfoJobs",
                date_posted=None,
                job_type=None,
                remote=remote
            )
        except Exception as e:
            return None
