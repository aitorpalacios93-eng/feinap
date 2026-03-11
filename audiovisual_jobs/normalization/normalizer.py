import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from dateutil import parser as dt_parser
import requests

from config.settings import settings
from intelligence.role_classifier import RoleClassifier
from scrapers.base import BaseScraper


class DateParser:
    """Parser robusto para fechas de ofertas de empleo"""

    @staticmethod
    def parse_fecha(fecha_str: Optional[str]) -> Optional[str]:
        """
        Parsea fecha de publicación de oferta.
        Retorna fecha en formato YYYY-MM-DD o None si no se puede parsear.
        """
        if not fecha_str or not fecha_str.strip():
            return None

        fecha_str = fecha_str.strip()

        # Patrón para fechas RFC/RSS como "Tue, 03 Mar 2026 08:40:16 +0000"
        rfc_date = re.match(
            r"[A-Za-z]{3},\s+(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})",
            fecha_str
        )
        if rfc_date:
            try:
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(fecha_str)
                return dt.date().isoformat()
            except Exception:
                pass

        patrones_fecha = [
            (r"(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})", "dd/mm/yyyy"),
            (r"(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})", "yyyy/mm/dd"),
            (r"hace\s*(\d+)\s*(día|dias|días|hora|horas|semana|semanas|mes|meses)", "relativo"),
            (r"(\d+)\s*(día|dias|días|hora|horas|semana|semanas|mes|meses)\s*atrás", "relativo"),
            (r"ayer", "ayer"),
            (r"hoy", "hoy"),
        ]

        for patron, tipo in patrones_fecha:
            match = re.search(patron, fecha_str.lower())
            if match:
                if tipo == "relativo":
                    return DateParser._parse_fecha_relativa(match.group(1), match.group(2))
                elif tipo == "ayer":
                    return (datetime.now() - timedelta(days=1)).date().isoformat()
                elif tipo == "hoy":
                    return datetime.now().date().isoformat()

        try:
            parsed = dt_parser.parse(fecha_str, fuzzy=True, default=datetime.now())
            if parsed.year < 2000 or parsed.year > 2030:
                parsed = parsed.replace(year=datetime.now().year)
            return parsed.date().isoformat()
        except Exception:
            return None

    @staticmethod
    def _parse_fecha_relativa(cantidad: str, unidad: str) -> str:
        """Parsea fechas relativas como 'hace 3 días'"""
        try:
            cantidad_int = int(cantidad)
        except ValueError:
            cantidad_int = 1

        unidad = unidad.lower()
        ahora = datetime.now()

        if "hora" in unidad:
            fecha = ahora - timedelta(hours=cantidad_int)
        elif "día" in unidad or "dia" in unidad:
            fecha = ahora - timedelta(days=cantidad_int)
        elif "semana" in unidad:
            fecha = ahora - timedelta(weeks=cantidad_int)
        elif "mes" in unidad:
            fecha = ahora - timedelta(days=cantidad_int * 30)
        else:
            fecha = ahora

        return fecha.date().isoformat()

    @staticmethod
    def es_fecha_valida(fecha_str: Optional[str]) -> bool:
        """Verifica si una fecha es válida y no demasiado antigua"""
        if not fecha_str:
            return False

        try:
            fecha = datetime.fromisoformat(fecha_str)
            dias_antiguedad = (datetime.now() - fecha).days
            return dias_antiguedad <= 60
        except Exception:
            return False


class QualityChecker:
    """Valida la calidad de ofertas antes de guardarlas"""

    @staticmethod
    def es_persona_buscando_trabajo(titulo: str, descripcion: str = "") -> bool:
        """Detecta si es una persona buscando trabajo vs empresa ofreciendo"""
        texto = (titulo + " " + descripcion).lower()

        busco_trabajo = [
            "busco empleo",
            "busco trabajo",
            "necesito trabajo",
            "necesito empleo",
            "en busca de empleo",
            "en busca de trabajo",
            "ofrezco mis servicios",
            "ofrezco servicios de",
            "freelance disponible",
            "disponible freelance",
            "disponible para trabajar",
            "autónomo busca",
            "autonimo busca",
            "profesional busca",
            "busco proyecto",
            "busco colaborar",
            "busco oportunidad",
            "busco incorporarme",
            "realizo trabajos de",
            "hago vídeos",
            "hago videos",
            "hago edición",
            "hago edicion",
            "trabajo freelance",
            "trabajo como freelance",
            "soy freelance",
            "camarógrafo freelance",
            "camara freelance",
            "editor freelance",
            "realizador freelance",
            "operador freelance",
        ]

        empresa_busca = [
            "se busca",
            "se necesita",
            "contratamos",
            "incorporamos",
            "únete al equipo",
            "formar parte",
            "vacante",
            "puesto disponible",
            "oportunidad laboral",
            "empresa busca",
            "startup busca",
            "productora busca",
            "agencia busca",
            "estudio busca",
            "buscamos",
            "necesitamos",
            "personal de",
            "equipo de",
        ]

        es_busca_trabajo = any(frase in texto for frase in busco_trabajo)
        es_empresa = any(frase in texto for frase in empresa_busca)

        return es_busca_trabajo and not es_empresa

    @staticmethod
    def validar_calidad(oferta: Dict[str, Any]) -> tuple[bool, str]:
        """
        Valida calidad de oferta. Retorna (pasa_filtro, razon).
        """
        titulo = oferta.get("titulo_puesto", "")
        descripcion = oferta.get("descripcion", "")
        source = oferta.get("source_domain", "").lower()

        # 1. Filtrar personas buscando trabajo
        if QualityChecker.es_persona_buscando_trabajo(titulo, descripcion):
            return False, "Persona buscando trabajo (no empresa ofreciendo)"

        # 2. Filtrar títulos de servicios
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
            return False, "Título indica oferta de servicios"

        # 3. Filtrar ofertas no audiovisuales (PERO PERMITIR HOSTELERIA)
        texto = (titulo + " " + descripcion).lower()
        no_audiovisual_keywords = [
            # ADMINISTRATIVO
            "limpieza",
            "limpiadora",
            "administrativo",
            "administrativa",
            "oficina",
            "secretaria",
            "recepcionista",
            # VENTAS/MARKETING
            "ventas",
            "comercial",
            "marketing",
            "rrhh",
            "recursos humanos",
            # INDUSTRIA
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
            # HOSTELERÍA - ELIMINADO PARA PERMITIR ESTAS OFERTAS
            "atención al cliente",
            "tienda",
            "dependiente",
            "dependienta",
            "vendedor",
            "vendedora",
            "cajero",
            "cajera",
            # CUIDADO DE PERSONAS
            "cuidadora",
            "cuidador",
            "cuidados",
            "personas mayores",
            "ancianos",
            "geriatría",
            "auxiliar geriatría",
            "enfermería",
            "enfermero",
            "enfermera",
            "asistencia domicilio",
            "servicio doméstico",
            "limpieza hogar",
            # OTROS NO AUDIOVISUALES
            "guardia de seguridad",
            "seguridad",
            "operario",
            "operaria",
            "peón",
            "repartidor",
            "mensajero",
            "mozo",
        ]

        if any(keyword in texto for keyword in no_audiovisual_keywords):
            # RECHAZAR todo lo que no sea audiovisual
            return (
                False,
                "Oferta no relacionada con audiovisual",
            )

        # 4. Filtrar ofertas con título demasiado corto o genérico
        if len(titulo) < 4:
            return False, "Título demasiado corto"

        # 5. Filtrar ofertas con solo datos de contacto
        if descripcion and len(descripcion) < 80:
            desc_lower = descripcion.lower()
            if (
                sum(
                    1
                    for p in ["contactar", "whatsapp", "teléfono", "llamar", "email"]
                    if p in desc_lower
                )
                >= 3
            ):
                return False, "Solo contiene datos de contacto"

        # 6. Filtrar mensajes spam/generales de Telegram
        spam_patterns = [
            "esto te interesa",
            "feria virtual de empleo",
            "próxima semana",
            "reunión",
            "evento",
            "webinar",
            "charla",
            "taller",
            "curso gratuit",
            "inscribete",
            "apúntate",
            "no te pierdas",
            "está celebración",
            "del xx al xx",
            "confianz",  # mensaje spam genérico
            "gracias por tu interés",
            "te contactaremos",
            "consulta nuestra web",
            "visita nuestra página",
        ]
        if any(pattern in texto for pattern in spam_patterns):
            return False, "Mensaje spam o evento genérico"

        # 7. FILTRO ELIMINADO: El score_confianza aquí siempre es 0 porque se calcula después.

        # 8. FILTRO ELIMINADO: No rechazar ofertas si contienen 'extraída automáticamente'.

        return True, "Pasa validación"


class Normalizer:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.classifier = RoleClassifier(min_role_score=settings.MIN_ROLE_SCORE)
        self.ubicaciones_validas = [
            "barcelona",
            "bcn",
            "girona",
            "lleida",
            "tarragona",
            "catalunya",
            "cataluña",
            "catalonia",
            "badalona",
            "sant cugat",
            "hospitalet",
            "sabadell",
            "tarragona",
            "reus",
            "tortosa",
            "lleida",
            "burgos",
        ]

    def _normalizar_url(self, url: Optional[str]) -> str:
        return self.classifier.canonical_url(url or "")

    def _limpiar_texto(self, texto: Optional[str]) -> str:
        if not texto:
            return ""
        texto = re.sub(r"\s+", " ", texto)
        texto = texto.replace("\n", " ").replace("\r", " ")
        emoji_pattern = re.compile(
            "["
            "\U0001f600-\U0001f64f"
            "\U0001f300-\U0001f5ff"
            "\U0001f680-\U0001f6ff"
            "\U0001f1e0-\U0001f1ff"
            "\U00002702-\U000027b0"
            "\U000024c2-\U0001f251"
            "]+",
            flags=re.UNICODE,
        )
        texto = emoji_pattern.sub(r"", texto)
        return texto.strip()

    def _extraer_ubicacion(
        self, texto: Optional[str], ubicacion_actual: Optional[str]
    ) -> str:
        if ubicacion_actual and ubicacion_actual.strip():
            return self._limpiar_texto(ubicacion_actual)

        if not texto:
            return "Cataluña (Sin especificar)"

        texto_lower = texto.lower()
        for ubi in self.ubicaciones_validas:
            if ubi in texto_lower:
                if ubi in ["bcn"]:
                    return "Barcelona"
                if ubi in ["catalunya", "cataluña", "catalonia"]:
                    return "Cataluña"
                return ubi.capitalize()

        return "Cataluña (Sin especificar)"

    def _extraer_titulo(self, titulo: Optional[str], texto: Optional[str]) -> str:
        if titulo and titulo.strip() and len(titulo.strip()) > 3:
            return self._limpiar_texto(titulo)[:200]

        if texto:
            primera_linea = texto.split("\n")[0].split(".")[0]
            titulo_extraido = primera_linea.strip()[:100]
            if len(titulo_extraido) > 3:
                return titulo_extraido

        return "Sin título"

    def _extraer_empresa(
        self, texto: Optional[str], empresa_actual: Optional[str]
    ) -> str:
        if empresa_actual and empresa_actual.strip():
            return self._limpiar_texto(empresa_actual)

        if not texto:
            return ""

        patrones_empresa = [
            r"(?:empresa|company|organización|organitzacio)\s*[:\-]?\s*([A-Z][^\n,]{2,50})",
            r"(?:busquem|busca|requiere|contrata)\s+([A-Z][^\n,]{2,50})",
        ]

        for patron in patrones_empresa:
            match = re.search(patron, texto, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return ""

    def normalizar_oferta(self, oferta: Dict[str, Any]) -> Dict[str, Any]:
        try:
            oferta_limpia = {
                "titulo_puesto": self._extraer_titulo(
                    oferta.get("titulo_puesto"), oferta.get("descripcion")
                ),
                "empresa": self._extraer_empresa(
                    oferta.get("descripcion"), oferta.get("empresa")
                ),
                "ubicacion": self._extraer_ubicacion(
                    oferta.get("descripcion"), oferta.get("ubicacion")
                ),
                "descripcion": self._limpiar_texto(oferta.get("descripcion")),
                "enlace_fuente": oferta.get("enlace_fuente", "").strip(),
                "tipo_fuente": oferta.get("tipo_fuente", "web"),
            }

            if oferta.get("fecha_publicacion"):
                fecha_parseada = DateParser.parse_fecha(oferta.get("fecha_publicacion"))
                if fecha_parseada:
                    oferta_limpia["fecha_publicacion"] = fecha_parseada

            # Clasificación por rol + geofiltro (incluye remoto en español, excluye LATAM)
            clasificacion = self.classifier.evaluate_offer(oferta_limpia)
            oferta_limpia.update(
                {
                    "rol_canonico": clasificacion.get("rol_canonico"),
                    "subrol": clasificacion.get("subrol"),
                    "score_confianza": clasificacion.get("score_confianza", 0.0),
                    "modalidad": clasificacion.get("modalidad", "no_especificado"),
                    "pais": clasificacion.get("pais"),
                    "es_latam": clasificacion.get("es_latam", False),
                    "remoto_espana": clasificacion.get("remoto_espana", False),
                    "source_domain": clasificacion.get("source_domain", ""),
                    "hash_fingerprint": clasificacion.get("hash_fingerprint", ""),
                    "extraction_method": oferta.get("extraction_method")
                    or oferta.get("tipo_fuente", "web"),
                    "last_seen_at": datetime.now(timezone.utc).isoformat(),
                    "first_seen_at": oferta.get("first_seen_at")
                    or datetime.now(timezone.utc).isoformat(),
                    "_keep": clasificacion.get("keep", False),
                }
            )

            if oferta_limpia["modalidad"] == "remoto" and (
                not oferta_limpia.get("ubicacion")
                or oferta_limpia.get("ubicacion") == "Cataluña (Sin especificar)"
            ):
                oferta_limpia["ubicacion"] = "Remoto (España)"

            oferta_limpia["enlace_fuente"] = self._normalizar_url(
                oferta_limpia.get("enlace_fuente")
            )

            return oferta_limpia

        except Exception as e:
            self.logger.warning(f"Error normalizando oferta: {e}")
            return {
                "titulo_puesto": "Error en normalización",
                "empresa": "",
                "ubicacion": "Cataluña (Sin especificar)",
                "descripcion": "",
                "enlace_fuente": oferta.get("enlace_fuente", ""),
                "tipo_fuente": oferta.get("tipo_fuente", "web"),
            }

    def normalizar_lista(self, ofertas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        self.logger.info(f"Normalizando {len(ofertas)} ofertas...")
        ofertas_normalizadas = []
        seen_urls = set()
        seen_title_company = set()
        descartadas_relevancia = 0
        descartadas_dedupe = 0
        descartadas_calidad = 0

        for oferta in ofertas:
            try:
                if not oferta.get("enlace_fuente"):
                    self.logger.debug("Oferta sin enlace, omitiendo")
                    continue

                # Validación de calidad ANTES de normalizar
                pasa_calidad, razon = QualityChecker.validar_calidad(oferta)
                if not pasa_calidad:
                    descartadas_calidad += 1
                    self.logger.debug(f"🚫 Oferta descartada por calidad: {razon}")
                    continue

                oferta_norm = self.normalizar_oferta(oferta)

                if not oferta_norm.get("_keep"):
                    descartadas_relevancia += 1
                    continue

                normalized_url = oferta_norm.get("enlace_fuente", "")
                if normalized_url in seen_urls:
                    descartadas_dedupe += 1
                    continue

                title_company_key = (
                    (oferta_norm.get("titulo_puesto") or "").strip().lower(),
                    (oferta_norm.get("empresa") or "").strip().lower(),
                )
                if all(title_company_key) and title_company_key in seen_title_company:
                    descartadas_dedupe += 1
                    continue

                seen_urls.add(normalized_url)
                if all(title_company_key):
                    seen_title_company.add(title_company_key)

                oferta_norm.pop("_keep", None)
                ofertas_normalizadas.append(oferta_norm)

            except Exception as e:
                self.logger.warning(f"Error procesando oferta: {e}")
                continue

        self.logger.info(f"Normalizadas {len(ofertas_normalizadas)} ofertas")
        self.logger.info(
            "Descartadas: %s por rol/geografía, %s por duplicados, %s por calidad",
            descartadas_relevancia,
            descartadas_dedupe,
            descartadas_calidad,
        )
        return ofertas_normalizadas


def normalizar_ofertas(ofertas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalizer = Normalizer()
    return normalizer.normalizar_lista(ofertas)
