import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from datetime import datetime
import time

from models.job import JobOffer

class JoobleScraper:
    BASE_URL = "https://es.jooble.org"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        })
    
    def search(self, keyword: str, location: str = "España", limit: int = 50) -> List[JobOffer]:
        jobs = []
        page = 1
        
        while len(jobs) < limit:
            url = f"{self.BASE_URL}/jobs-{keyword.lower().replace(' ', '-')}?p={page}&l={location}"
            
            try:
                response = self.session.get(url, timeout=15)
                if response.status_code != 200:
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.select('div._1khB9')
                
                if not job_cards:
                    job_cards = soup.select('div[data-id]')
                
                if not job_cards:
                    break
                
                for card in job_cards:
                    if len(jobs) >= limit:
                        break
                    
                    job = self._parse_job_card(card)
                    if job:
                        jobs.append(job)
                
                page += 1
                time.sleep(2)
                
            except Exception as e:
                print(f"Error fetching Jooble: {e}")
                break
        
        return jobs
    
    def _parse_job_card(self, card) -> Optional[JobOffer]:
        try:
            title_elem = card.select_one('a._896a') or card.select_one('a')
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            url = title_elem.get('href', '')
            if url and not url.startswith('http'):
                url = self.BASE_URL + url
            
            company_elem = card.select_one('span._1boa5')
            company = company_elem.get_text(strip=True) if company_elem else "No especificada"
            
            location_elem = card.select_one('span._1x4fd')
            location = location_elem.get_text(strip=True) if location_elem else "No especificada"
            
            salary_elem = card.select_one('span._1t51r')
            salary = salary_elem.get_text(strip=True) if salary_elem else None
            
            desc_elem = card.select_one('p._1mHHc')
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            remote = 'remoto' in description.lower() or 'remote' in description.lower() or 'teletrabajo' in description.lower()
            
            return JobOffer(
                title=title,
                company=company,
                location=location,
                salary=salary,
                description=description,
                url=url,
                source="Jooble",
                date_posted=None,
                job_type=None,
                remote=remote
            )
        except Exception as e:
            return None
