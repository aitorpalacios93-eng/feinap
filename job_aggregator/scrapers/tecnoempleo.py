import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from datetime import datetime
import time

from models.job import JobOffer

class TecnoempleoScraper:
    BASE_URL = "https://www.tecnoempleo.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        })
    
    def search(self, keyword: str, limit: int = 50) -> List[JobOffer]:
        jobs = []
        page = 1
        
        while len(jobs) < limit:
            url = f"{self.BASE_URL}/busqueda-empleo.php?k={keyword}&pag={page}"
            
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code != 200:
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                job_rows = soup.select('div#results div.row')
                
                if not job_rows:
                    break
                
                for row in job_rows:
                    if len(jobs) >= limit:
                        break
                    
                    job = self._parse_job_row(row)
                    if job:
                        jobs.append(job)
                
                page += 1
                time.sleep(1)
                
            except Exception as e:
                print(f"Error fetching Tecnoempleo: {e}")
                break
        
        return jobs
    
    def _parse_job_row(self, row) -> Optional[JobOffer]:
        try:
            title_elem = row.select_one('h2 a')
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            url = title_elem.get('href', '')
            if url and not url.startswith('http'):
                url = self.BASE_URL + url
            
            company_elem = row.select_one('spanEmpresa')
            company = company_elem.get_text(strip=True) if company_elem else "No especificada"
            
            location_elem = row.select_one('span.location')
            location = location_elem.get_text(strip=True) if location_elem else "No especificada"
            
            salary_elem = row.select_one('span.salary')
            salary = salary_elem.get_text(strip=True) if salary_elem else None
            
            desc_elem = row.select_one('p.excerpt')
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            date_elem = row.select_one('span.date')
            date_posted = None
            if date_elem:
                date_str = date_elem.get_text(strip=True)
                date_posted = self._parse_date(date_str)
            
            remote = 'remoto' in description.lower() or 'remote' in description.lower() or 'teletrabajo' in description.lower()
            
            return JobOffer(
                title=title,
                company=company,
                location=location,
                salary=salary,
                description=description,
                url=url,
                source="Tecnoempleo",
                date_posted=date_posted,
                job_type="Tiempo completo",
                remote=remote
            )
        except Exception as e:
            print(f"Error parsing job row: {e}")
            return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        import re
        date_str = date_str.lower()
        
        match = re.search(r'(\d+)\s*d[ií]as?', date_str)
        if match:
            days = int(match.group(1))
            from datetime import timedelta
            return datetime.now() - timedelta(days=days)
        
        return None
