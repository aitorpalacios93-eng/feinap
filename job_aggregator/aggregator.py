from scrapers.infojobs import InfoJobsScraper
from scrapers.indeed import IndeedScraper
from scrapers.tecnoempleo import TecnoempleoScraper
from scrapers.linkedin import LinkedInScraper
from models.job import JobOffer
from db.database import JobDatabase
from typing import List

class JobAggregator:
    def __init__(self, db_path: str = "jobs.db"):
        self.db = JobDatabase(db_path)
        self.scrapers = {
            'infojobs': InfoJobsScraper(),
            'indeed': IndeedScraper(),
            'tecnoempleo': TecnoempleoScraper(),
            'linkedin': LinkedInScraper(),
        }
    
    def search_all(self, keyword: str, location: str = "Spain", limit_per_source: int = 25) -> List[JobOffer]:
        all_jobs = []
        
        scrapers_config = {
            'infojobs': {'location': location, 'limit': limit_per_source},
            'indeed': {'location': location, 'limit': limit_per_source},
            'linkedin': {'location': location, 'limit': limit_per_source},
            'tecnoempleo': {'limit': limit_per_source},
        }
        
        for source, config in scrapers_config.items():
            print(f"Buscando en {source}...")
            try:
                scraper = self.scrapers[source]
                if source == 'linkedin' or source == 'indeed':
                    jobs = scraper.search(keyword, location=config.get('location', 'Spain'), limit=config['limit'])
                elif source == 'tecnoempleo':
                    jobs = scraper.search(keyword, limit=config['limit'])
                else:
                    jobs = scraper.search(keyword, location=config.get('location', 'espana'), limit=config['limit'])
                
                print(f"  -> {len(jobs)} ofertas encontradas")
                all_jobs.extend(jobs)
                
            except Exception as e:
                print(f"Error en {source}: {e}")
        
        return all_jobs
    
    def search_and_save(self, keyword: str, location: str = "Spain", limit_per_source: int = 25) -> int:
        jobs = self.search_all(keyword, location, limit_per_source)
        saved = self.db.save_jobs(jobs)
        print(f"Total guardadas: {saved} ofertas")
        return saved
    
    def get_jobs(self, source: str = None, limit: int = 100):
        return self.db.get_jobs(source, limit)
    
    def search_jobs(self, keyword: str, limit: int = 100):
        return self.db.search_jobs(keyword, limit)
    
    def get_stats(self):
        return self.db.get_stats()
