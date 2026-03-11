import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from datetime import datetime
import time

from models.job import JobOffer

class LinkedInScraper:
    BASE_URL = "https://www.linkedin.com/jobs-guest"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        })
    
    def search(self, keyword: str, location: str = "Spain", limit: int = 50) -> List[JobOffer]:
        jobs = []
        start = 0
        
        while len(jobs) < limit:
            url = f"{self.BASE_URL}/jobs/api/seeMoreJobPostings/search?keywords={keyword}&location={location}&start={start}"
            
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code != 200:
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.select('li')
                
                if not job_cards:
                    break
                
                for card in job_cards:
                    if len(jobs) >= limit:
                        break
                    
                    job = self._parse_job_card(card)
                    if job:
                        jobs.append(job)
                
                start += 25
                time.sleep(2)
                
            except Exception as e:
                print(f"Error fetching LinkedIn: {e}")
                break
        
        return jobs
    
    def _parse_job_card(self, card) -> Optional[JobOffer]:
        try:
            title_elem = card.select_one('h3.base-search-card__title')
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            
            link_elem = card.select_one('a.base-search-card__full-link')
            if not link_elem:
                return None
            
            url = link_elem.get('href', '')
            
            company_elem = card.select_one('h4.base-search-card__subtitle')
            company = company_elem.get_text(strip=True) if company_elem else "No especificada"
            
            location_elem = card.select_one('span.job-search-card__location')
            location = location_elem.get_text(strip=True) if location_elem else "No especificada"
            
            date_elem = card.select_one('time.job-search-card__listdate')
            date_posted = None
            if date_elem:
                date_str = date_elem.get('datetime', '')
                if date_str:
                    date_posted = datetime.fromisoformat(date_str)
            
            metadata_elem = card.select_one('div.base-search-card__metadata')
            salary = None
            if metadata_elem:
                salary_elem = metadata_elem.select_one('span.job-card-container__marker-container')
                if salary_elem:
                    salary = salary_elem.get_text(strip=True)
            
            remote = 'remote' in location.lower() or 'teletrabajo' in location.lower()
            
            return JobOffer(
                title=title,
                company=company,
                location=location,
                salary=salary,
                description="",
                url=url,
                source="LinkedIn",
                date_posted=date_posted,
                job_type=None,
                remote=remote
            )
        except Exception as e:
            print(f"Error parsing job card: {e}")
            return None
