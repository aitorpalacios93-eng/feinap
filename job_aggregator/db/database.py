import sqlite3
from datetime import datetime
from typing import List, Optional
from models.job import JobOffer

class JobDatabase:
    def __init__(self, db_path: str = "jobs.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT,
                location TEXT,
                salary TEXT,
                description TEXT,
                url TEXT UNIQUE NOT NULL,
                source TEXT,
                date_posted TEXT,
                job_type TEXT,
                remote INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    
    def save_job(self, job: JobOffer) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO jobs 
                (title, company, location, salary, description, url, source, date_posted, job_type, remote)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.title, job.company, job.location, job.salary,
                job.description, job.url, job.source,
                job.date_posted.isoformat() if job.date_posted else None,
                job.job_type, 1 if job.remote else 0
            ))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error saving job: {e}")
            return False
        finally:
            conn.close()
    
    def save_jobs(self, jobs: List[JobOffer]) -> int:
        count = 0
        for job in jobs:
            if self.save_job(job):
                count += 1
        return count
    
    def get_jobs(self, source: Optional[str] = None, limit: int = 100) -> List[JobOffer]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if source:
            cursor.execute("SELECT * FROM jobs WHERE source = ? ORDER BY created_at DESC LIMIT ?", (source, limit))
        else:
            cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        jobs = []
        for row in rows:
            jobs.append(JobOffer(
                title=row['title'],
                company=row['company'],
                location=row['location'],
                salary=row['salary'],
                description=row['description'],
                url=row['url'],
                source=row['source'],
                date_posted=datetime.fromisoformat(row['date_posted']) if row['date_posted'] else None,
                job_type=row['job_type'],
                remote=bool(row['remote'])
            ))
        return jobs
    
    def search_jobs(self, keyword: str, limit: int = 100) -> List[JobOffer]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM jobs 
            WHERE title LIKE ? OR company LIKE ? OR description LIKE ?
            ORDER BY created_at DESC LIMIT ?
        """, (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        jobs = []
        for row in rows:
            jobs.append(JobOffer(
                title=row['title'],
                company=row['company'],
                location=row['location'],
                salary=row['salary'],
                description=row['description'],
                url=row['url'],
                source=row['source'],
                date_posted=datetime.fromisoformat(row['date_posted']) if row['date_posted'] else None,
                job_type=row['job_type'],
                remote=bool(row['remote'])
            ))
        return jobs
    
    def get_stats(self) -> dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT source, COUNT(*) as count FROM jobs GROUP BY source")
        by_source = dict(cursor.fetchall())
        
        cursor.execute("SELECT COUNT(*) FROM jobs")
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return {'total': total, 'by_source': by_source}
