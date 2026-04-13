"""
Supabase backend para Job Aggregator.
Escribe en la tabla 'ofertas_empleo' existente.
Deduplicación por enlace_fuente (UNIQUE index).
"""
import os
import logging
from datetime import datetime, date
from typing import List, Optional

log = logging.getLogger(__name__)


class SupabaseDB:
    def __init__(self):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL y SUPABASE_KEY/SUPABASE_SERVICE_KEY son necesarios")
        from supabase import create_client
        self.client = create_client(url, key)

    def save_job(self, job) -> bool:
        """Guarda una oferta. Retorna True si es nueva, False si ya existía."""
        if not job.url:
            return False
        try:
            date_pub = None
            if job.date_posted:
                d = job.date_posted
                if isinstance(d, datetime):
                    date_pub = d.date().isoformat()
                elif isinstance(d, date):
                    date_pub = d.isoformat()

            modalidad = None
            if job.remote is True:
                modalidad = "remoto"
            elif job.remote is False:
                modalidad = "presencial"

            data = {
                "titulo_puesto":  (job.title or "")[:500],
                "empresa":        (job.company or "No especificada")[:255],
                "ubicacion":      (job.location or "No especificada")[:255],
                "descripcion":    (job.description or "")[:3000],
                "enlace_fuente":  job.url.strip()[:1000],
                "tipo_fuente":    "web",
                "source_domain":  (job.source or "")[:100],
                "fecha_publicacion": date_pub,
                "modalidad":      modalidad,
                "offer_type":     (job.source_category or "empleo")[:100],
                "last_seen_at":   datetime.utcnow().isoformat(),
                "pais":           "ES",
            }

            result = self.client.table("ofertas_empleo").upsert(
                data,
                on_conflict="enlace_fuente",
            ).execute()
            return bool(result.data)

        except Exception as e:
            err = str(e)
            # Conflicto de unicidad en (titulo_puesto, empresa) → misma oferta vista en otro portal
            if "23505" in err or "unique" in err.lower() or "duplicate" in err.lower():
                return False
            log.warning(f"DB error [{job.source}] {job.url[:60]}: {e}")
            return False

    def save_jobs(self, jobs: List) -> int:
        new = 0
        for job in jobs:
            if self.save_job(job):
                new += 1
        return new

    def log_run(self, run_type: str, stats: dict, status: str = "completed") -> None:
        try:
            self.client.table("ingestion_runs").insert({
                "run_type":     run_type,
                "trigger":      "scheduled",
                "status":       status,
                "stats":        stats,
                "finished_at":  datetime.utcnow().isoformat(),
            }).execute()
        except Exception as e:
            log.debug(f"No se pudo registrar el run: {e}")

    def get_recent_count(self, days: int = 7) -> int:
        """Cuenta ofertas activas de los últimos N días."""
        try:
            from datetime import timedelta
            cutoff = (date.today() - timedelta(days=days)).isoformat()
            result = self.client.table("ofertas_empleo")\
                .select("id", count="exact")\
                .gte("last_seen_at", cutoff)\
                .execute()
            return result.count or 0
        except Exception:
            return -1
