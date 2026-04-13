import os
import requests
from typing import List, Optional
from datetime import datetime

from models.job import JobOffer


class JoobleAPI:
    # La API de Jooble usa la key en la URL: https://jooble.org/api/{key}
    # Usar variable de entorno JOOBLE_API_KEY si está disponible
    _DEFAULT_KEY = "957ae3d7-45a8-4854-8d3e-a977b0d44792"

    def __init__(self):
        self.api_key = os.environ.get("JOOBLE_API_KEY") or self._DEFAULT_KEY

    def search(
        self, keyword: str, location: str = "Spain", limit: int = 20
    ) -> List[JobOffer]:
        jobs = []

        # Jooble funciona mejor con location en inglés
        location_map = {
            "españa": "Spain",
            "espana": "Spain",
            "madrid": "Madrid",
            "barcelona": "Barcelona",
            "valencia": "Valencia",
            "sevilla": "Seville",
            "bilbao": "Bilbao",
        }
        location_lower = location.lower().strip()
        if location_lower in location_map:
            location = location_map[location_lower]

        try:
            headers = {"Content-Type": "application/json"}
            data = {
                "keywords": keyword,
                "location": location,
                "radius": 50,
                "limit": limit,
                "page": 1,
            }

            # URL correcta: POST https://jooble.org/api/{api_key}
            response = requests.post(
                f"https://jooble.org/api/{self.api_key}",
                json=data,
                headers=headers,
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                jobs_data = result.get("jobs", [])

                for item in jobs_data:
                    # Extraer fecha de publicación si está disponible
                    date_posted = None
                    raw_date = item.get("updated") or item.get("date")
                    if raw_date:
                        try:
                            date_posted = datetime.fromisoformat(
                                str(raw_date).replace("Z", "+00:00")
                            )
                        except Exception:
                            pass

                    company = item.get("company")
                    if isinstance(company, dict):
                        company = company.get("name", "No especificada")
                    else:
                        company = str(company or "No especificada")

                    salary = item.get("salary")
                    if isinstance(salary, dict):
                        salary = salary.get("salary", "")
                    else:
                        salary = str(salary or "")

                    job_type = item.get("type")
                    if isinstance(job_type, dict):
                        job_type = job_type.get("name", "")
                    else:
                        job_type = str(job_type or "")

                    job = JobOffer(
                        title=item.get("title", ""),
                        company=company,
                        location=item.get("location", "No especificada"),
                        salary=salary or None,
                        description=item.get("description", "")[:500],
                        url=item.get("link", ""),
                        source="Jooble",
                        date_posted=date_posted,
                        job_type=job_type or None,
                        remote="remote" in item.get("location", "").lower()
                        or "teletrabajo" in item.get("description", "").lower(),
                        source_category="empleo_general_es",
                    )
                    jobs.append(job)

        except Exception as e:
            print(f"Jooble API error: {e}")

        return jobs
