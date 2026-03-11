from abc import ABC, abstractmethod
from typing import List, Dict, Any
import logging

from config.settings import settings


class BaseScraper(ABC):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.ofertas_extraidas: List[Dict[str, Any]] = []

    @abstractmethod
    def scrape(self) -> Any:
        """Método abstracto que debe devolver lista de diccionarios con campos:
        - titulo_puesto: str
        - empresa: str
        - ubicacion: str
        - descripcion: str
        - enlace_fuente: str
        - tipo_fuente: str
        - fecha_publicacion: date (opcional)
        """
        pass

    def normalizar_oferta(self, oferta: Dict[str, Any]) -> Dict[str, Any]:
        defaults = {
            "titulo_puesto": "",
            "empresa": "",
            "ubicacion": "",
            "descripcion": "",
            "enlace_fuente": "",
            "tipo_fuente": self.__class__.__name__.replace("Scraper", "").lower(),
        }
        return {**defaults, **oferta}

    def filtrar_audiovisual(self, texto: str) -> bool:
        if not texto:
            return False

        negativo = [
            # Contenido sexual/adulto
            "desnudo",
            "desnuda",
            "nude",
            "desnud",
            "escort",
            "prostituta",
            "puta",
            "whore",
            "onlyfans",
            "only fans",
            "contenido adulto",
            "sexual",
            "erótico",
            "erotico",
            "sexo",
            "masturba",
            "porno",
            "xxx",
            "webcam",
            "cam girl",
            "cam shows",
            "acompañante",
            "acompanante",
            # Trabajos dudosos/estafas
            "dinero fácil",
            "dinero facil",
            "easy money",
            "cashhh",
            "cash money",
            "dinero rápido",
            "trabaja desde casa",
            "trabajo desde casa",
            "gana desde casa",
            "sin experiencia necesaria",
            "ingresos pasivos",
            "multiplica tu dinero",
            "inversión garantizada",
            "garantizado 100%",
            "oportunidad única",
            "actúa ahora",
            "dinero extra",
            "renta básica",
            "pago por adelantado",
            "envía dinero",
            "transferencia bancaria",
            # Reclutamiento sospechoso
            "solo mujeres",
            "only women",
            "women only",
            "solo chicas",
            "solo jovencitas",
            "mayor de edad",
            "18 años",
            "18 years",
            "mayor de 18",
            "over 18",
            "se buscan chicas",
            "se necesitan chicas",
            "casting para adultos",
            # Fotografía/modelaje dudoso
            "posar",
            "posez",
            "pose desnuda",
            "book fotográfico",
            "sesión fotográfica privada",
            "fotografía artística",
            "fotografia artistica",
            "modelaje íntimo",
            "modelaje intimo",
            "figura completa",
            "full body",
            "sin ropa",
            "sin vestimenta",
            "implied nude",
            "topless",
            "bottomless",
            # Otros
            "copas",
            "strip",
            "striptease",
            "novia",
            "pareja",
            "girlfriend",
            "sugar",
            "sugar daddy",
            "sugar baby",
            "amateur",
            "amateur content",
            "contenido exclusivo",
            "contenido privado",
            "suscripción mensual",
            "suscripcion mensual",
        ]
        texto_lower = texto.lower()

        # Contar coincidencias negativas
        coincidencias_negativas = sum(1 for kw in negativo if kw in texto_lower)

        # Si hay 2 o más coincidencias negativas, rechazar
        if coincidencias_negativas >= 2:
            self.logger.debug(
                f"🚫 RECHAZADO ({coincidencias_negativas} flags): {texto[:80]}"
            )
            return False

        # Si hay 1 coincidencia muy fuerte, rechazar también
        palabras_fuertes = ["desnudo", "escort", "prostituta", "onlyfans", "sexual"]
        if any(palabra in texto_lower for palabra in palabras_fuertes):
            self.logger.debug(f"🚫 RECHAZADO (palabra fuerte): {texto[:80]}")
            return False

        keywords = [kw.lower().strip() for kw in settings.KEYWORDS_FILTRO if kw.strip()]
        texto_lower = texto.lower()
        return any(kw in texto_lower for kw in keywords)

    def es_oferta_vigente(self, fecha_str: str, dias_max: int = 30) -> bool:
        """Determina si una oferta sigue vigente basado en su fecha"""
        if not fecha_str:
            return True  # Si no hay fecha, asumir vigente

        try:
            from datetime import datetime

            fecha = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
            dias = (datetime.now() - fecha).days
            return dias <= dias_max
        except:
            return True

    def es_persona_buscando_trabajo(self, titulo: str, descripcion: str = "") -> bool:
        """
        Detecta si una oferta es realmente una persona buscando trabajo
        en lugar de una empresa ofreciendo empleo.
        Retorna True si es persona buscando trabajo (debe ser filtrada).
        """
        texto = (titulo + " " + descripcion).lower()

        # Palabras que indican "yo busco trabajo"
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

        # Palabras que indican "empresa busca trabajador"
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

        # Si parece buscar trabajo y NO parece empresa, es ruído
        if es_busca_trabajo and not es_empresa:
            self.logger.debug(f"🚫 FILTRADO - Persona buscando trabajo: {titulo[:60]}")
            return True

        return False

    def validar_calidad_oferta(self, oferta: Dict[str, Any]) -> bool:
        """
        Valida la calidad general de una oferta antes de guardarla.
        Retorna True si la oferta pasa todos los filtros de calidad.
        """
        titulo = oferta.get("titulo_puesto", "")
        descripcion = oferta.get("descripcion", "")
        source = oferta.get("source_domain", "").lower()

        # 1. Filtrar personas buscando trabajo
        if self.es_persona_buscando_trabajo(titulo, descripcion):
            return False

        # 2. Filtrar ofertas con título sospechoso de servicios
        titulo_lower = titulo.lower()
        if any(
            frase in titulo_lower
            for frase in [
                "ofrezco",
                "hago",
                "realizo",
                "servicios de",
                "trabajo freelance",
            ]
        ):
            self.logger.debug(f"🚫 FILTRADO - Título indica servicios: {titulo[:60]}")
            return False

        # 3. Para Milanuncios, requerir más validación
        if "milanuncios" in source:
            # Si el título es muy corto o genérico, requerir descripción real
            if len(titulo) < 15 and (
                not descripcion or "extraída automáticamente" in descripcion
            ):
                self.logger.debug(
                    f"🚫 FILTRADO - Milanuncios sin contenido real: {titulo[:60]}"
                )
                return False

        # 4. Rechazar descripciones genéricas sin información útil
        if descripcion and len(descripcion) < 50:
            palabras_rechazo = ["contactar", "llamar", "whatsapp", "tlf", "teléfono"]
            if all(p in descripcion.lower() for p in ["contactar", "whatsapp"]):
                self.logger.debug(
                    f"🚫 FILTRADO - Solo datos de contacto: {titulo[:60]}"
                )
                return False

        return True
