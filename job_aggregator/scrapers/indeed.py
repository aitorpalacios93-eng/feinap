import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from datetime import datetime
import time

from models.job import JobOffer

class IndeedScraper:
    BASE_URL = "https://www.indeed.com"
    
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
            url = f"{self.BASE_URL}/jobs?q={keyword}&l={location}&start={start}"
            
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code != 200:
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.select('div.job-card-container')
                
                if not job_cards:
                    break
                
                for card in job_cards:
                    if len(jobs) >= limit:
                        break
                    
                    job = self._parse_job_card(card)
                    if job:
                        jobs.append(job)
                
                start += 10
                time.sleep(1)
                
            except Exception as e:
                print(f"Error fetching Indeed: {e}")
                break
        
        return jobs
    
    def _parse_job_card(self, card) -> Optional[JobOffer]:
        try:
            title_elem = card.select_one('h2.jobTitle a')
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            url = title_elem.get('href', '')
            if url and not url.startswith('http'):
                url = self.BASE_URL + url
            
            company_elem = card.select_one('span.companyName')
            company = company_elem.get_text(strip=True) if company_elem else "No especificada"
            
            location_elem = card.select_one('div.companyLocation')
            location = location_elem.get_text(strip=True) if location_elem else "No especificada"
            
            salary_elem = card.select_one('div.salary-snippet-container')
            salary = salary_elem.get_text(strip=True) if salary_elem else None
            
            desc_elem = card.select_one('div.job-snippet')
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            date_elem = card.select_one('span.date')
            date_posted = None
            if date_elem:
                date_str = date_elem.get_text(strip=True)
                date_posted = self._parse_date(date_str)
            
            remote = 'remote' in description.lower() or 'teletrabajo' in description.lower() or 'home' in description.lower()
            
            return JobOffer(
                title=title,
                company=company,
                location=location,
                salary=salary,
                description=description,
                url=url,
                source="Indeed",
                date_posted=date_posted,
                job_type=None,
                remote=remote
            )
        except Exception as e:
            print(f"Error parsing job card: {e}")
            return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        import re
        date_str = date_str.lower()
        
        match = re.search(r'(\d+)\s*day', date_str)
        if match:
            days = int(match.group(1))
            return datetime.now() - timedelta(days=days)
        
        match = re.search(r'(\d+)\s*hour', date_str)
        if match:
            hours = int(match.group(1))
            return datetime.now() - timedelta(hours=hours)
        
        return None


from datetime import timedelta
