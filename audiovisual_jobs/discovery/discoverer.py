import logging
import requests
from typing import List, Optional
from urllib.parse import parse_qs, urlparse, unquote

from bs4 import BeautifulSoup

from config.settings import settings
from db.queries import insert_fuente_por_revisar, upsert_fuentes_catalogo_bulk
from discovery.source_registry import to_catalog_rows


class Discoverer:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._latam_terms = [
            "mexico",
            "argentina",
            "colombia",
            "chile",
            "peru",
            "ecuador",
            "bolivia",
            "uruguay",
            "paraguay",
            "venezuela",
            "latam",
        ]

    def sync_catalogo_base(self, client) -> int:
        rows = to_catalog_rows(include_blocked=True)
        total = upsert_fuentes_catalogo_bulk(client, rows)
        self.logger.info("Catálogo base sincronizado: %s fuentes", total)
        return total

    def _buscar_serpapi(self, query: str) -> List[str]:
        if not settings.SERPAPI_KEY:
            self.logger.warning("SERPAPI_KEY no configurada")
            return []

        try:
            params = {
                "q": query,
                "api_key": settings.SERPAPI_KEY,
                "num": 20,
                "engine": "google",
            }

            response = requests.get(
                "https://serpapi.com/search", params=params, timeout=30
            )
            response.raise_for_status()
            data = response.json()

            urls = []
            for result in data.get("organic_results", []):
                url = result.get("link")
                if url:
                    urls.append(url)

            self.logger.info(f"SerpAPI: encontrados {len(urls)} resultados")
            return urls

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error en SerpAPI: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error inesperado SerpAPI: {e}")
            return []

    def _buscar_duckduckgo(self, query: str) -> List[str]:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            urls: List[str] = []

            for a in soup.select("a.result__a"):
                href_val = a.get("href")
                if isinstance(href_val, (list, tuple)):
                    href = str(href_val[0]).strip() if href_val else ""
                else:
                    href = str(href_val or "").strip()
                if not href:
                    continue

                parsed = urlparse(href)
                if parsed.netloc.endswith("duckduckgo.com") and parsed.path.startswith(
                    "/l/"
                ):
                    qs = parse_qs(parsed.query)
                    uddg = qs.get("uddg", [""])[0]
                    if uddg:
                        urls.append(unquote(uddg))
                elif href.startswith("http"):
                    urls.append(href)

            urls = list(dict.fromkeys(urls))[:20]

            self.logger.info(f"DuckDuckGo: encontrados {len(urls)} resultados")
            return urls

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error en DuckDuckGo: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error inesperado DuckDuckGo: {e}")
            return []

    def _filtrar_urls(self, urls: List[str]) -> List[str]:
        urls_validas = []
        exclude_patterns = [
            "facebook.com",
            "twitter.com",
            "instagram.com",
            "linkedin.com",
            "youtube.com",
            "tiktok.com",
            ".pdf",
            ".doc",
            ".zip",
            "mailto:",
            "w3.org",
            "duckduckgo.com",
        ]
        include_hints = [
            "empleo",
            "trabajo",
            "oferta",
            "ofertas",
            "jobs",
            "job",
            "casting",
            "career",
            "careers",
            "vacante",
            "vacancy",
            "bolsa",
            "jobsearch",
            "curriculum",
            "seleccion",
            "seleccio",
        ]

        for url in urls:
            url_lower = url.lower()
            if any(term in url_lower for term in self._latam_terms):
                continue
            if any(pattern in url_lower for pattern in exclude_patterns):
                continue
            if not url.startswith("http"):
                continue

            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                continue
            if not parsed.netloc:
                continue

            searchable = f"{parsed.netloc}{parsed.path}{parsed.query}".lower()
            if not any(hint in searchable for hint in include_hints):
                continue

            urls_validas.append(url)

        return urls_validas

    def _build_queries(self, query: Optional[str]) -> List[str]:
        if query:
            return [query]

        env_queries = [
            q.strip().strip('"').strip("'")
            for q in settings.DISCOVERY_QUERIES
            if q.strip()
        ]
        if env_queries:
            return env_queries

        return [
            '("oferta de empleo" OR "trabajo" OR "buscamos") (audiovisual OR video OR cine OR cámara OR producción audiovisual) (España OR Barcelona OR Girona OR Lleida OR Tarragona)',
            '("editor de video" OR "montador" OR "postproducción" OR "davinci" OR "premiere") (España OR Barcelona) empleo',
            '("realizador" OR "operador de cámara" OR "ayudante de producción") (España OR Cataluña) oferta',
        ]

    def buscar(self, client, query: Optional[str] = None) -> int:
        queries = self._build_queries(query)
        self.logger.info("Discovery con %s queries", len(queries))

        all_urls: List[str] = []
        for q in queries:
            self.logger.info("Ejecutando búsqueda: %s...", q[:90])
            if settings.SERPAPI_KEY:
                urls = self._buscar_serpapi(q)
            else:
                self.logger.info("Usando DuckDuckGo como fallback")
                urls = self._buscar_duckduckgo(q)
            all_urls.extend(urls)

        if not all_urls:
            self.logger.warning("No se encontraron URLs")
            return 0

        urls_filtradas = self._filtrar_urls(list(dict.fromkeys(all_urls)))
        self.logger.info(f"URLs válidas tras filtro: {len(urls_filtradas)}")

        guardadas = 0
        for url in urls_filtradas:
            try:
                domain = urlparse(url).netloc.lower()
                insert_fuente_por_revisar(
                    client=client,
                    url=url,
                    titulo="Descubierto automáticamente",
                    tipo_fuente="google",
                )
                upsert_fuentes_catalogo_bulk(
                    client,
                    [
                        {
                            "url": url,
                            "domain": domain,
                            "nombre": domain,
                            "categoria": "discovery",
                            "extraction_method": "pending",
                            "priority_score": 40,
                            "status": "candidate",
                            "idioma": "es",
                            "alcance_geografico": "es",
                            "include_remote": True,
                            "exclude_latam": True,
                            "notes": "Alta automática por discovery",
                        }
                    ],
                )
                guardadas += 1
            except Exception as e:
                self.logger.warning(f"Error guardando {url}: {e}")
                continue

        self.logger.info(f"Fuentes guardadas en DB: {guardadas}")
        return guardadas


def buscar_nuevas_fuentes(client, query: Optional[str] = None) -> int:
    discoverer = Discoverer()
    return discoverer.buscar(client, query)
