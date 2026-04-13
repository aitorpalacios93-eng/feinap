from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class JobOffer:
    title: str
    company: str
    location: str
    salary: Optional[str]
    description: str
    url: str
    source: str
    date_posted: Optional[datetime]
    job_type: Optional[str]
    remote: Optional[bool]
    source_category: Optional[str] = None  # empleo_general_es, freelance_multiservicio, etc.

    def to_dict(self):
        return {
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'salary': self.salary,
            'description': self.description[:500] if self.description else '',
            'url': self.url,
            'source': self.source,
            'date_posted': self.date_posted.isoformat() if self.date_posted else None,
            'job_type': self.job_type,
            'remote': self.remote,
            'source_category': self.source_category,
        }
