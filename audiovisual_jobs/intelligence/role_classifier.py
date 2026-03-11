import hashlib
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


class RoleClassifier:
    """Clasificador híbrido (reglas + score) para roles audiovisuales.

    Objetivo fase 1:
    - Clasificar ofertas en roles canónicos
    - Incluir remoto en español
    - Excluir LATAM
    """

    ROLE_KEYWORDS: Dict[str, List[Tuple[str, int]]] = {
        "edicion_post": [
            ("editor de video", 5),
            ("editor de vídeo", 5),
            ("editor", 4),
            ("editora", 4),
            ("edicion", 4),
            ("edición", 4),
            ("montador", 4),
            ("postproduccion", 4),
            ("postproducción", 4),
            ("premiere", 3),
            ("davinci", 3),
            ("resolve", 3),
            ("after effects", 3),
            ("colorista", 3),
            ("etalonaje", 3),
            ("final cut", 3),
        ],
        "realizacion": [
            ("realizador", 5),
            ("realizadora", 5),
            ("realizacion", 4),
            ("realización", 4),
            ("realitzador", 4),
            ("regidor", 3),
            ("regidora", 3),
            ("asistente de direccion", 3),
            ("asistente de dirección", 3),
            ("direction assistant", 2),
        ],
        "operador_camara_video": [
            ("operador de camara", 5),
            ("operador de cámara", 5),
            ("camera operator", 5),
            ("camara", 3),
            ("cámara", 3),
            ("camarografo", 4),
            ("camarógrafo", 4),
            ("videografo", 4),
            ("videógrafo", 4),
            ("foquista", 4),
            ("auxiliar de camara", 4),
            ("auxiliar de cámara", 4),
            ("steadicam", 3),
            ("operador eng", 4),
            ("operador video", 4),
        ],
        "operador_sonido": [
            ("operador de sonido", 5),
            ("tecnico de sonido", 5),
            ("técnico de sonido", 5),
            ("sonidista", 4),
            ("microfonista", 4),
            ("boom operator", 4),
            ("audio engineer", 3),
            ("mezclador de sonido", 3),
        ],
        "ayudante_produccion": [
            ("ayudante de produccion", 6),
            ("ayudante de producción", 6),
            ("auxiliar de produccion", 5),
            ("auxiliar de producción", 5),
            ("production assistant", 5),
            ("runner", 4),
            ("pa", 2),
            ("asistente de produccion", 5),
            ("asistente de producción", 5),
        ],
        "produccion": [
            ("produccion audiovisual", 4),
            ("producción audiovisual", 4),
            ("coordinador de produccion", 4),
            ("coordinador de producción", 4),
            ("jefe de produccion", 4),
            ("jefe de producción", 4),
            ("line producer", 4),
            ("production coordinator", 4),
            ("coordinacion de rodaje", 3),
            ("coordinación de rodaje", 3),
        ],
        "relacionados": [
            ("script", 3),
            ("continuista", 3),
            (" media manager", 3),
            ("ingesta", 3),
            ("data wrangler", 3),
            ("audiovisual", 2),
            ("rodaje", 2),
            ("produccion de contenidos", 2),
            ("producción de contenidos", 2),
        ],
        "cocinero": [
            ("cocinero", 10),
            ("jefe de cocina", 10),
            ("chef de partie", 10),
            ("cocinero/a", 10),
            ("cocina", 5),
            ("ayudante de cocina", 8),
            ("ayudante de reposteria", 8),
            ("bartender", 6),
            ("barista", 6),
        ],
        "no_audiovisual": [
            ("limpieza", 10),
            ("limpiadora", 10),
            ("administrativo", 8),
            ("administrativa", 8),
            ("oficina", 8),
            ("secretaria", 8),
            ("recepcionista", 8),
            ("ventas", 8),
            ("comercial", 8),
            ("marketing", 6),
            ("rrhh", 6),
            ("recursos humanos", 6),
            ("logistica", 6),
            ("logística", 6),
            ("almacen", 6),
            ("almacén", 6),
            ("conductor", 6),
            ("chofer", 6),
            ("mecanico", 6),
            ("mecánico", 6),
            ("fontanero", 6),
            ("electricista", 6),
            ("construccion", 6),
            ("construcción", 6),
            ("obra", 6),
            ("industria", 6),
            ("fabricacion", 6),
            ("fabricación", 6),
            ("produccion industrial", 6),
            ("producción industrial", 6),
            # Cuidado de personas
            ("cuidadora", 10),
            ("cuidador", 10),
            ("cuidados", 5),
            ("personas mayores", 10),
            ("ancianos", 10),
            ("geriatria", 10),
            ("auxiliar geriatria", 10),
            ("enfermeria", 10),
            ("enfermero", 10),
            ("enfermera", 10),
            ("asistencia domicilio", 10),
            ("servicio doméstico", 10),
            ("limpieza hogar", 10),
        ],
    }

    LATAM_TERMS = [
        "mexico",
        "méxico",
        "argentina",
        "colombia",
        "chile",
        "peru",
        "perú",
        "ecuador",
        "bolivia",
        "uruguay",
        "paraguay",
        "venezuela",
        "costa rica",
        "guatemala",
        "honduras",
        "el salvador",
        "nicaragua",
        "panama",
        "panamá",
        "republica dominicana",
        "república dominicana",
        "latam",
        "latinoamerica",
        "latinoamérica",
    ]

    SPAIN_TERMS = [
        "espana",
        "españa",
        "barcelona",
        "girona",
        "lleida",
        "tarragona",
        "catalunya",
        "cataluña",
        "madrid",
        "valencia",
        "sevilla",
        "bilbao",
        "zaragoza",
        "malaga",
        "málaga",
        "palma",
        "vigo",
        "santiago de compostela",
        "alicante",
    ]

    INTERNATIONAL_TERMS = [
        "uk",
        "united kingdom",
        "london",
        "usa",
        "united states",
        "new york",
        "canada",
        "france",
        "paris",
        "germany",
        "berlin",
        "italy",
        "milan",
        "portugal",
        "lisbon",
        "netherlands",
        "amsterdam",
    ]

    REMOTE_TERMS = [
        "remoto",
        "remote",
        "teletrabajo",
        "work from home",
        "wfh",
        "100% remoto",
        "en remoto",
    ]

    HYBRID_TERMS = ["hibrido", "híbrido", "mixto", "hybrid"]

    SPANISH_STOPWORDS = {
        "de",
        "la",
        "el",
        "en",
        "con",
        "para",
        "y",
        "del",
        "se",
        "que",
        "por",
        "buscamos",
        "oferta",
        "trabajo",
    }

    def __init__(self, min_role_score: int = 4):
        self.min_role_score = min_role_score

    def classify(
        self, titulo: Optional[str], descripcion: Optional[str]
    ) -> Dict[str, Any]:
        titulo_norm = self._normalize_text(titulo)
        desc_norm = self._normalize_text(descripcion)
        combined = f"{titulo_norm} {desc_norm}".strip()

        role_scores: Dict[str, int] = {}
        role_terms: Dict[str, str] = {}
        for role, terms in self.ROLE_KEYWORDS.items():
            score = 0
            best_term = ""
            best_weight = 0
            for term, weight in terms:
                term_norm = self._normalize_text(term)
                if term_norm and term_norm in titulo_norm:
                    term_score = weight * 3
                elif term_norm and term_norm in desc_norm:
                    term_score = weight
                else:
                    term_score = 0

                score += term_score
                if term_score > best_weight:
                    best_weight = term_score
                    best_term = term

            role_scores[role] = score
            role_terms[role] = best_term

        top_role = (
            max(role_scores.keys(), key=lambda role: role_scores[role])
            if role_scores
            else ""
        )
        top_score = role_scores.get(top_role, 0)

        # Verificar si hay términos de no_audiovisual con score alto
        no_audiovisual_score = 0
        for term, weight in self.ROLE_KEYWORDS["no_audiovisual"]:
            term_norm = self._normalize_text(term)
            if term_norm in titulo_norm:
                no_audiovisual_score += weight * 3
            elif term_norm in desc_norm:
                no_audiovisual_score += weight

        # Si el score de no_audiovisual es alto, clasificar como no relevante
        if no_audiovisual_score >= 8:
            return {
                "rol_canonico": "no_audiovisual",
                "subrol": None,
                "score_confianza": 0.0,
                "es_relevante": False,
            }

        # Aumentar score mínimo para ayudante_produccion a 6 para evitar ofertas no audiovisuales
        if top_role == "ayudante_produccion" and top_score < 6:
            return {
                "rol_canonico": "no_audiovisual",
                "subrol": None,
                "score_confianza": 0.0,
                "es_relevante": False,
            }

        if top_score < self.min_role_score:
            return {
                "rol_canonico": "no_audiovisual",
                "subrol": None,
                "score_confianza": 0.0,
                "es_relevante": False,
            }

        confidence = min(1.0, round(top_score / 12.0, 2))
        return {
            "rol_canonico": top_role,
            "subrol": role_terms.get(top_role),
            "score_confianza": confidence,
            "es_relevante": True,
            "texto_normalizado": combined,
        }

    def evaluate_offer(self, oferta: Dict[str, Any]) -> Dict[str, Any]:
        titulo = oferta.get("titulo_puesto") or ""
        descripcion = oferta.get("descripcion") or ""
        ubicacion = oferta.get("ubicacion") or ""
        enlace = oferta.get("enlace_fuente") or ""
        role_result = self.classify(titulo, descripcion)

        # Verificar si la oferta es muy antigua (antes de 2024)
        fecha_publicacion = oferta.get("fecha_publicacion")
        if fecha_publicacion:
            try:
                from datetime import datetime

                fecha_obj = datetime.fromisoformat(
                    fecha_publicacion.replace("Z", "+00:00")
                )
                if fecha_obj.year < 2024:
                    return {
                        "keep": role_result.get("es_relevante", False),
                        "rol_canonico": "legacy",
                        "subrol": role_result.get("subrol"),
                        "score_confianza": 0.0,
                        "modalidad": "no_especificado",
                        "pais": None,
                        "es_latam": False,
                        "remoto_espana": False,
                        "source_domain": self._extract_domain(enlace),
                        "hash_fingerprint": self.build_fingerprint(
                            titulo, oferta.get("empresa"), enlace
                        ),
                        "legacy": True,
                        "es_relevante_original": role_result.get("es_relevante", False),
                    }
            except Exception:
                pass  # Si no se puede parsear la fecha, continuamos
        texto_geo = self._normalize_text(f"{titulo} {descripcion} {ubicacion}")
        source_domain = self._extract_domain(enlace)

        modalidad = self._detect_modalidad(texto_geo)
        has_latam = self._contains_any(texto_geo, self.LATAM_TERMS)
        has_spain = self._contains_any(texto_geo, self.SPAIN_TERMS)
        spanish_like = self._is_spanish_like(texto_geo)
        is_spanish_domain = source_domain.endswith(".es") if source_domain else False

        remoto_espana = (
            modalidad == "remoto"
            and not has_latam
            and (has_spain or spanish_like or is_spanish_domain)
        )

        if modalidad == "remoto":
            geo_ok = remoto_espana
        else:
            has_other_international = self._contains_any(
                texto_geo, self.INTERNATIONAL_TERMS
            )
            geo_ok = (not has_latam) and (
                has_spain
                or spanish_like
                or is_spanish_domain
                or not has_other_international
            )

        keep = bool(role_result.get("es_relevante")) and geo_ok and not has_latam

        return {
            "keep": keep,
            "rol_canonico": role_result.get("rol_canonico"),
            "subrol": role_result.get("subrol"),
            "score_confianza": role_result.get("score_confianza", 0.0),
            "modalidad": modalidad,
            "pais": "España" if geo_ok else None,
            "es_latam": has_latam,
            "remoto_espana": remoto_espana,
            "source_domain": source_domain,
            "hash_fingerprint": self.build_fingerprint(
                titulo, oferta.get("empresa"), enlace
            ),
        }

    def canonical_url(self, url: str) -> str:
        if not url:
            return ""
        try:
            split = urlsplit(url)
            query = [
                (k, v)
                for k, v in parse_qsl(split.query, keep_blank_values=True)
                if not k.lower().startswith("utm_")
            ]
            cleaned_query = urlencode(query)
            path = split.path.rstrip("/")
            return urlunsplit(
                (split.scheme, split.netloc.lower(), path, cleaned_query, "")
            )
        except Exception:
            return url

    def build_fingerprint(
        self, titulo: Optional[str], empresa: Optional[str], enlace: Optional[str]
    ) -> str:
        canonical = self.canonical_url(enlace or "")
        payload = "|".join(
            [
                self._normalize_text(titulo),
                self._normalize_text(empresa),
                canonical,
            ]
        )
        return hashlib.sha1(payload.encode("utf-8")).hexdigest()

    def _detect_modalidad(self, text_norm: str) -> str:
        if self._contains_any(text_norm, self.HYBRID_TERMS):
            return "hibrido"
        if self._contains_any(text_norm, self.REMOTE_TERMS):
            return "remoto"
        if text_norm:
            return "presencial"
        return "no_especificado"

    def _extract_domain(self, url: str) -> str:
        if not url:
            return ""
        try:
            return urlsplit(url).netloc.lower()
        except Exception:
            return ""

    def _is_spanish_like(self, text_norm: str) -> bool:
        if not text_norm:
            return False
        tokens = re.findall(r"[a-záéíóúñ]+", text_norm)
        if not tokens:
            return False
        hits = sum(1 for t in tokens if t in self.SPANISH_STOPWORDS)
        return hits >= 2

    def _contains_any(self, haystack: str, terms: List[str]) -> bool:
        return any(self._normalize_text(term) in haystack for term in terms)

    def _normalize_text(self, text: Optional[str]) -> str:
        if not text:
            return ""
        text = str(text).lower().strip()
        text = unicodedata.normalize("NFKD", text)
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        text = re.sub(r"\s+", " ", text)
        return text
