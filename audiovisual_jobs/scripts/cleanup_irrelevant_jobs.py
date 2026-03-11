import argparse
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from db.connection import get_supabase_client, test_connection
from intelligence.role_classifier import RoleClassifier


class JobCleaner:
    """Limpia ofertas de trabajo irrelevantes y antiguas del catálogo"""

    def __init__(self):
        self.classifier = RoleClassifier(min_role_score=4)
        self.no_audiovisual_keywords = [
            "limpieza",
            "limpiadora",
            "camarera",
            "camarero",
            "hosteleria",
            "hostelería",
            "restaurante",
            "bar",
            "cafeteria",
            "administrativo",
            "administrativa",
            "oficina",
            "secretaria",
            "recepcionista",
            "ventas",
            "comercial",
            "marketing",
            "rrhh",
            "recursos humanos",
            "logistica",
            "logística",
            "almacen",
            "almacén",
            "conductor",
            "chofer",
            "mecanico",
            "mecánico",
            "fontanero",
            "electricista",
            "construccion",
            "construcción",
            "obra",
            "industria",
            "fabricacion",
            "fabricación",
            "produccion industrial",
            "producción industrial",
        ]

    def _is_irrelevant_job(self, titulo: str, descripcion: str) -> bool:
        """Determina si una oferta es irrelevante (no audiovisual)"""
        texto = (titulo + " " + descripcion).lower()

        # Verificar keywords de no audiovisual
        if any(keyword in texto for keyword in self.no_audiovisual_keywords):
            return True

        # Verificar si el título indica servicios
        titulo_lower = titulo.lower()
        if any(
            frase in titulo_lower
            for frase in [
                "ofrezco",
                "hago ",
                "realizo ",
                "servicios de",
                "trabajo freelance",
            ]
        ):
            return True

        return False

    def _is_old_job(self, fecha_publicacion: Optional[str]) -> bool:
        """Determina si una oferta es muy antigua (antes de 2024)"""
        if not fecha_publicacion:
            return False

        try:
            from datetime import datetime

            fecha_obj = datetime.fromisoformat(fecha_publicacion.replace("Z", "+00:00"))
            return fecha_obj.year < 2024
        except Exception:
            return False

    def _classify_job(self, oferta: Dict[str, Any]) -> Dict[str, Any]:
        """Clasifica una oferta y devuelve su clasificación"""
        titulo = oferta.get("titulo_puesto", "")
        descripcion = oferta.get("descripcion", "")

        return self.classifier.classify(titulo, descripcion)

    def _get_jobs_to_clean(self, client) -> List[Dict[str, Any]]:
        """Obtiene todas las ofertas del catálogo para evaluar"""
        try:
            return (
                client.table("ofertas_catalogo").select("*", True).execute().data or []
            )
        except Exception as exc:
            print(f"ERROR obteniendo ofertas: {exc}")
            return []

    def _delete_job(self, client, job_id: str) -> bool:
        """Elimina una oferta del catálogo"""
        try:
            client.table("ofertas_catalogo").delete().eq("id", job_id).execute()
            return True
        except Exception as exc:
            print(f"WARN: no se pudo borrar oferta {job_id}: {exc}")
            return False

    def _mark_as_legacy(self, client, job_id: str) -> bool:
        """Marca una oferta antigua pero relevante como legacy"""
        try:
            client.table("ofertas_catalogo").update(
                {
                    "rol_canonico": "legacy",
                    "score_confianza": 0.0,
                    "legacy": True,
                    "es_relevante_original": True,
                }
            ).eq("id", job_id).execute()
            return True
        except Exception as exc:
            print(f"WARN: no se pudo marcar como legacy oferta {job_id}: {exc}")
            return False

    def clean_jobs(self, apply: bool = False) -> Dict[str, int]:
        """Limpia el catálogo de ofertas irrelevantes y antiguas"""
        print("Iniciando limpieza de ofertas...")

        try:
            client = get_supabase_client()
            test_connection(client)
        except Exception as exc:
            print(f"ERROR conexion Supabase: {exc}")
            return {"error": 1, "deleted": 0, "marked_legacy": 0}

        jobs = self._get_jobs_to_clean(client)
        print(f"Total ofertas a evaluar: {len(jobs)}")

        deleted_count = 0
        marked_legacy_count = 0
        evaluated_count = 0

        for job in jobs:
            try:
                evaluated_count += 1

                # Clasificar la oferta
                classification = self._classify_job(job)
                is_relevant = classification.get("es_relevante", False)

                # Verificar si es irrelevante
                if self._is_irrelevant_job(
                    job.get("titulo_puesto", ""), job.get("descripcion", "")
                ):
                    if apply:
                        if self._delete_job(client, job["id"]):
                            deleted_count += 1
                    else:
                        print(
                            f"PREVIEW: Eliminando irrelevante - {job.get('titulo_puesto', '')}"
                        )
                    continue

                # Verificar si es antigua
                if self._is_old_job(job.get("fecha_publicacion")):
                    if is_relevant:
                        # Marcar como legacy si es relevante
                        if apply:
                            if self._mark_as_legacy(client, job["id"]):
                                marked_legacy_count += 1
                        else:
                            print(
                                f"PREVIEW: Marcando como legacy - {job.get('titulo_puesto', '')}"
                            )
                    else:
                        # Eliminar si no es relevante
                        if apply:
                            if self._delete_job(client, job["id"]):
                                deleted_count += 1
                        else:
                            print(
                                f"PREVIEW: Eliminando antigua e irrelevante - {job.get('titulo_puesto', '')}"
                            )
                    continue

            except Exception as exc:
                print(f"WARN: error procesando oferta {job.get('id', '')}: {exc}")

        print(f"\nResumen limpieza:")
        print(f"Ofertas evaluadas: {evaluated_count}")
        print(f"Ofertas eliminadas: {deleted_count}")
        print(f"Ofertas marcadas como legacy: {marked_legacy_count}")

        return {
            "error": 0,
            "deleted": deleted_count,
            "marked_legacy": marked_legacy_count,
            "evaluated": evaluated_count,
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Limpia ofertas de trabajo irrelevantes y antiguas del catálogo"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplica borrado real (sin esta flag solo muestra preview)",
    )
    args = parser.parse_args()

    cleaner = JobCleaner()
    result = cleaner.clean_jobs(apply=args.apply)

    if result.get("error", 0) == 0:
        return 0
    else:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
