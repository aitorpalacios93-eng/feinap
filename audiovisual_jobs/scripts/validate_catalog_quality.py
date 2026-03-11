import argparse
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional
from datetime import datetime
import logging

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from db.connection import get_supabase_client, test_connection
from intelligence.role_classifier import RoleClassifier
from normalization.normalizer import Normalizer


class QualityValidator:
    """Valida la calidad de ofertas en el catálogo"""
    
    def __init__(self):
        self.classifier = RoleClassifier(min_role_score=4)
        self.normalizer = Normalizer()
        self.no_audiovisual_keywords = [
            "limpieza", "limpiadora", "camarera", "camarero", "hosteleria", "hostelería",
            "restaurante", "bar", "cafeteria", "administrativo", "administrativa", "oficina",
            "secretaria", "recepcionista", "ventas", "comercial", "marketing", "rrhh",
            "recursos humanos", "logistica", "logística", "almacen", "almacén", "conductor",
            "chofer", "mecanico", "mecánico", "fontanero", "electricista", "construccion",
            "construcción", "obra", "industria", "fabricacion", "fabricación",
            "produccion industrial", "producción industrial"
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
            for frase in ["ofrezco", "hago ", "realizo ", "servicios de", "trabajo freelance"]
        ):
            return True
        
        return False
    
    def _is_old_job(self, fecha_publicacion: Optional[str]) -> bool:
        """Determina si una oferta es muy antigua (antes de 2024)"""
        if not fecha_publicacion:
            return False
            
        try:
            from datetime import datetime
            
            fecha_obj = datetime.fromisoformat(
                fecha_publicacion.replace("Z", "+00:00")
            )
            return fecha_obj.year < 2024
        except Exception:
            return False
    
    def _get_jobs_for_validation(self, client) -> List[Dict[str, Any]]:
        """Obtiene ofertas del catálogo para validación"""
        try:
            return (
                client.table("ofertas_catalogo")
                .select("*", True)
                .execute()
                .data or []
            )
        except Exception as exc:
            print(f"ERROR obteniendo ofertas: {exc}")
            return []
    
    def _get_statistics(self, client) -> Dict[str, int]:
        """Obtiene estadísticas actuales del catálogo"""
        try:
            # Total de ofertas
            total = (
                client.table("ofertas_catalogo")
                .select("count(*)", True)
                .execute()
                .data[0]["count"]
                if client.table("ofertas_catalogo").select("count(*)").execute().data
                else 0
            )
            
            # Ofertas por rol
            roles = (
                client.table("ofertas_catalogo")
                .select("rol_canonico, count(*)", True)
                .group("rol_canonico")
                .execute()
                .data or []
            )
            
            # Ofertas legacy
            legacy_count = (
                client.table("ofertas_catalogo")
                .select("count(*)", True)
                .eq("legacy", True)
                .execute()
                .data[0]["count"]
                if client.table("ofertas_catalogo").select("count(*)").eq("legacy", True).execute().data
                else 0
            )
            
            # Ofertas irrelevantes
            irrelevant_count = 0
            for role in roles:
                if role["rol_canonico"] == "no_audiovisual":
                    irrelevant_count = role["count"]
                    break
            
            return {
                "total_ofertas": total,
                "ofertas_legacy": legacy_count,
                "ofertas_irrelevantes": irrelevant_count,
                "ofertas_relevantes": total - legacy_count - irrelevant_count,
                "desglose_roles": {r["rol_canonico"]: r["count"] for r in roles}
            }
            
        except Exception as exc:
            print(f"ERROR obteniendo estadísticas: {exc}")
            return {}
    
    def validate_catalog(self, apply: bool = False) -> Dict[str, int]:
        """Valida la calidad del catálogo completo"""
        print("Iniciando validación de catálogo...")
        
        try:
            client = get_supabase_client()
            test_connection(client)
        except Exception as exc:
            print(f"ERROR conexion Supabase: {exc}")
            return {"error": 1, "validadas": 0}
        
        # Obtener estadísticas iniciales
        stats = self._get_statistics(client)
        print(f"\nESTADÍSTICAS ACTUALES:")
        print(f"Total ofertas: {stats.get('total_ofertas', 0)}")
        print(f"Ofertas relevantes: {stats.get('ofertas_relevantes', 0)}")
        print(f"Ofertas legacy: {stats.get('ofertas_legacy', 0)}")
        print(f"Ofertas irrelevantes: {stats.get('ofertas_irrelevantes', 0)}")
        
        jobs = self._get_jobs_for_validation(client)
        print(f"\nValidando {len(jobs)} ofertas...")
        
        invalid_count = 0
        old_count = 0
        evaluated_count = 0
        
        for job in jobs:
            try:
                evaluated_count += 1
                
                # Verificar si es irrelevante
                if self._is_irrelevant_job(
                    job.get("titulo_puesto", ""), 
                    job.get("descripcion", "")
                ):
                    invalid_count += 1
                    if apply:
                        # Marcar como no_audiovisual
                        client.table("ofertas_catalogo")
                        .update({
                            "rol_canonico": "no_audiovisual",
                            "score_confianza": 0.0,
                            "es_relevante": False
                        })
                        .eq("id", job["id"])
                        .execute()
                    else:
                        print(f"PREVIEW: Inválida - {job.get('titulo_puesto', '')}")
                    continue
                
                # Verificar si es antigua
                if self._is_old_job(job.get("fecha_publicacion")):
                    old_count += 1
                    if apply:
                        # Marcar como legacy
                        client.table("ofertas_catalogo")
                        .update({
                            "rol_canonico": "legacy",
                            "score_confianza": 0.0,
                            "legacy": True,
                            "es_relevante_original": True
                        })
                        .eq("id", job["id"])
                        .execute()
                    else:
                        print(f"PREVIEW: Antigua - {job.get('titulo_puesto', '')} ({job.get('fecha_publicacion', '')})")
                    continue
                
            except Exception as exc:
                print(f"WARN: error validando oferta {job.get('id', '')}: {exc}")
        
        # Obtener estadísticas finales
        final_stats = self._get_statistics(client)
        
        print(f"\nRESUMEN VALIDACIÓN:")
        print(f"Ofertas evaluadas: {evaluated_count}")
        print(f"Ofertas marcadas como irrelevantes: {invalid_count}")
        print(f"Ofertas marcadas como antiguas: {old_count}")
        print(f"\nESTADÍSTICAS FINALES:")
        print(f"Total ofertas: {final_stats.get('total_ofertas', 0)}")
        print(f"Ofertas relevantes: {final_stats.get('ofertas_relevantes', 0)}")
        print(f"Ofertas legacy: {final_stats.get('ofertas_legacy', 0)}")
        print(f"Ofertas irrelevantes: {final_stats.get('ofertas_irrelevantes', 0)}")
        
        return {
            "error": 0,
            "validadas": evaluated_count,
            "marcadas_irrelevantes": invalid_count,
            "marcadas_antiguas": old_count,
            "stats_iniciales": stats,
            "stats_finales": final_stats
        }

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida y mejora la calidad del catálogo de ofertas audiovisuales"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplica cambios reales (sin esta flag solo muestra preview)",
    )
    args = parser.parse_args()
    
    validator = QualityValidator()
    result = validator.validate_catalog(apply=args.apply)
    
    if result.get("error", 0) == 0:
        return 0
    else:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())