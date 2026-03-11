import requests
from typing import List, Optional
from datetime import datetime

from models.job import JobOffer

class ApifyScraper:
    ACTORS = {
        'infojobs': 'cH8FNFtV7pT6d2L3k',  # Placeholder
        'indeed': 'WQZbbGFm5oS5W7jBx',
        'linkedin': 'aIGJvFa7BvmqGrC3n',
    }
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "https://api.apify.com/v2"
    
    def search(self, source: str, keyword: str, location: str = "Spain", limit: int = 50) -> List[JobOffer]:
        if not self.api_key:
            return self._search_fallback(source, keyword, location, limit)
        
        actor_id = self.ACTORS.get(source)
        if not actor_id:
            return []
        
        try:
            url = f"{self.base_url}/acts/{actor_id}/runs"
            
            input_data = {
                "keyword": keyword,
                "location": location,
                "limit": limit
            }
            
            response = requests.post(
                url,
                json=input_data,
                params={"token": self.api_key},
                timeout=30
            )
            
            if response.status_code == 201:
                run_id = response.json()['data']['id']
                return self._wait_for_results(run_id, limit)
                
        except Exception as e:
            print(f"Apify error: {e}")
        
        return []
    
    def _wait_for_results(self, run_id: str, limit: int) -> List[JobOffer]:
        import time
        
        max_wait = 120
        elapsed = 0
        
        while elapsed < max_wait:
            try:
                url = f"{self.base_url}/runs/{run_id}/status"
                response = requests.get(url, params={"token": self.api_key}, timeout=10)
                
                if response.status_code == 200:
                    status = response.json()['data']['status']
                    
                    if status == 'SUCCEEDED':
                        return self._get_dataset(run_id, limit)
                    elif status in ['FAILED', 'ABORTED']:
                        break
                
                time.sleep(5)
                elapsed += 5
                
            except Exception as e:
                print(f"Error waiting: {e}")
                break
        
        return []
    
    def _get_dataset(self, run_id: str, limit: int) -> List[JobOffer]:
        try:
            url = f"{self.base_url}/runs/{run_id}/dataset/items"
            response = requests.get(url, params={"token": self.api_key, "limit": limit}, timeout=30)
            
            if response.status_code == 200:
                items = response.json()
                return self._parse_items(items)
                
        except Exception as e:
            print(f"Error getting results: {e}")
        
        return []
    
    def _parse_items(self, items: List[dict]) -> List[JobOffer]:
        jobs = []
        
        for item in items:
            try:
                job = JobOffer(
                    title=item.get('title', ''),
                    company=item.get('company', 'No especificada'),
                    location=item.get('location', 'No especificada'),
                    salary=item.get('salary'),
                    description=item.get('description', ''),
                    url=item.get('url', ''),
                    source=item.get('source', 'Apify'),
                    date_posted=None,
                    job_type=item.get('jobType'),
                    remote=item.get('remote', False)
                )
                jobs.append(job)
            except:
                pass
        
        return jobs
    
    def _search_fallback(self, source: str, keyword: str, location: str, limit: int) -> List[JobOffer]:
        print(f"Apify API key no configurada. Usa --api-key o configura APIFY_API_KEY")
        return []
