import asyncio
import logging
import random
import time
import httpx
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from playwright.async_api import (
    async_playwright,
    Browser,
    Page,
    TimeoutError as PlaywrightTimeout,
)

from scrapers.base import BaseScraper
from scrapers.selectores_config import SELECTORES_CONFIG
from scrapers.antibot_utils import AntiBotManager, NUEVAS_FUENTES
from config.settings import settings
from db.queries import record_fuente_health


class WebScraper(BaseScraper):
    # Fuentes de EMPLEO AUDIOVISUAL - SOLO LAS QUE FUNCIONAN
    # Marzo 2026 - Después de múltiples rondas de testing
    # ÚNICA FUENTE QUE FUNCIONA BIEN: Domestika
    PORTALES_DEFAULT = [
        "https://www.domestika.org/es/jobs/area/75-produccion-audiovisual/forever",
    ]

    def __init__(self, portales: Optional[List[str]] = None, db_client: Any = None):
        super().__init__()
        env_portales = [p.strip() for p in settings.PORTALES_SCRAPER if p.strip()]
        self.portales = portales or env_portales or self.PORTALES_DEFAULT
        self.browser: Optional[Browser] = None
        self.playwright = None
        self.db_client = db_client

    def _xml_text(self, item: ET.Element, tag: str) -> str:
        node = item.find(tag)
        if node is None:
            return ""
        return (node.text or "").strip()

    def _rss_items_from_xml(self, content: bytes) -> List[Dict[str, str]]:
        items_data: List[Dict[str, str]] = []
        try:
            root = ET.fromstring(content)
            items = root.findall(".//item") or root.findall(".//entry")
            for item in items[: settings.OFERTAS_POR_PORTAL]:
                items_data.append(
                    {
                        "title": self._xml_text(item, "title"),
                        "link": self._xml_text(item, "link"),
                        "pub_date": self._xml_text(item, "pubDate"),
                        "description": self._xml_text(item, "description"),
                    }
                )
            return items_data
        except ET.ParseError:
            # Fallback tolerante para feeds mal formados
            soup = BeautifulSoup(content, "xml")
            soup_items = soup.find_all("item") or soup.find_all("entry")

            def soup_text(entry: Any, tag: str) -> str:
                node = entry.find(tag)
                if not node:
                    return ""
                try:
                    return node.get_text(" ", strip=True)
                except Exception:
                    return ""

            for item in soup_items[: settings.OFERTAS_POR_PORTAL]:
                link_tag = item.find("link")
                href = ""
                if link_tag:
                    href_attr = link_tag.get("href")
                    if isinstance(href_attr, (list, tuple)):
                        href = str(href_attr[0]).strip() if href_attr else ""
                    elif href_attr:
                        href = str(href_attr).strip()
                    else:
                        href = soup_text(item, "link")

                items_data.append(
                    {
                        "title": soup_text(item, "title"),
                        "link": href,
                        "pub_date": soup_text(item, "pubDate"),
                        "description": soup_text(item, "description"),
                    }
                )
            return items_data

    async def _iniciar_navegador(self):
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=settings.HEADLESS,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--disable-features=IsolateOrigins,site-per-process",
                ],
            )
            self.logger.info("Navegador Playwright iniciado (modo anti-bot)")
        except Exception as e:
            self.logger.error(f"Error al iniciar navegador: {e}")
            raise

    async def _cerrar_navegador(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.logger.info("Navegador cerrado")

    def _obtener_config(self, url: str) -> Dict[str, Any]:
        domain = urlparse(url).netloc
        # Intentar coincidencia exacta
        if domain in SELECTORES_CONFIG:
            return SELECTORES_CONFIG[domain]
        # Intentar coincidencia parcial (ignorar subdominios como 'es', 'www', etc)
        for cfg_domain, cfg in SELECTORES_CONFIG.items():
            if cfg_domain.replace("www.", "") in domain or domain.replace("www.", "") in cfg_domain:
                return cfg
        return {}

    def _report_health(
        self,
        source_url: str,
        status: str,
        latency_ms: Optional[int],
        items_detected: int,
        error_message: Optional[str] = None,
    ) -> None:
        if not self.db_client:
            return
        try:
            record_fuente_health(
                client=self.db_client,
                source_url=source_url,
                status=status,
                latency_ms=latency_ms,
                items_detected=items_detected,
                error_message=error_message,
            )
        except Exception as e:
            self.logger.warning("No se pudo registrar health %s: %s", source_url, e)

    def _split_selectors(self, raw_value: Any) -> List[str]:
        if not raw_value:
            return []
        if isinstance(raw_value, list):
            return [str(s).strip() for s in raw_value if str(s).strip()]
        return [s.strip() for s in str(raw_value).split(",") if s.strip()]

    def _is_likely_css_selector(self, value: str) -> bool:
        if not value:
            return False
        value = value.strip()
        # Valores literales como "Mediapro" o "RTVE" no deben tratarse como CSS.
        css_hints = (".", "#", "[", "]", ":", ">", " ", "*", "(", ")")
        return any(hint in value for hint in css_hints)

    async def _first_text_from_selectors(self, item: Any, selectors: List[str]) -> str:
        for selector in selectors:
            try:
                node = await item.query_selector(selector)
                if not node:
                    continue
                txt = (await node.inner_text()).strip()
                if txt:
                    return txt
            except Exception:
                continue
        return ""

    async def _first_href_from_selectors(self, item: Any, selectors: List[str]) -> str:
        for selector in selectors:
            try:
                node = await item.query_selector(selector)
                if not node:
                    continue
                href = (await node.get_attribute("href") or "").strip()
                if href:
                    return href
            except Exception:
                continue
        return ""

    async def _fallback_item_data(self, item: Any) -> Dict[str, str]:
        title = ""
        href = ""
        try:
            anchor = await item.query_selector("a[href]")
            if anchor:
                title = (await anchor.inner_text()).strip()
                href = (await anchor.get_attribute("href") or "").strip()
        except Exception:
            pass

        if not title:
            try:
                raw = (await item.inner_text()).strip()
                if raw:
                    title = raw.split("\n", 1)[0].strip()
            except Exception:
                pass

        return {"title": title, "href": href}

    async def _fallback_anchor_offers(
        self, page: Page, source_url: str
    ) -> List[Dict[str, Any]]:
        ofertas: List[Dict[str, Any]] = []
        job_hints = ("job", "empleo", "oferta", "vacan", "trabajo", "careers")
        anchor_selector = "a[href*='job'], a[href*='empleo'], a[href*='oferta'], a[href*='vacan'], a[href*='trabajo'], a[href*='careers']"
        anchors = await page.query_selector_all(anchor_selector)
        for anchor in anchors[: settings.OFERTAS_POR_PORTAL * 5]:
            try:
                href = (await anchor.get_attribute("href") or "").strip()
                title = (await anchor.inner_text()).strip()
                if not href or not title:
                    continue
                if self._is_noise_title(title):
                    continue
                if len(title) < 8:
                    continue
                href_lower = href.lower()
                title_lower = title.lower()
                if not any(
                    h in href_lower for h in job_hints
                ) and not self.filtrar_audiovisual(title_lower):
                    continue
                ofertas.append(
                    self.normalizar_oferta(
                        {
                            "titulo_puesto": title,
                            "enlace_fuente": urljoin(source_url, href),
                            "descripcion": f"Oferta extraída automáticamente de {source_url}",
                        }
                    )
                )
            except Exception:
                continue

            if len(ofertas) >= settings.OFERTAS_POR_PORTAL:
                break
        return ofertas

    def _is_noise_title(self, title: str) -> bool:
        value = (title or "").strip().lower()
        if not value:
            return True

        noise_values = {
            "mostrar mas",
            "mostrar más",
            "leer mas",
            "leer más",
            "ver mas",
            "ver más",
            "mas info",
            "más info",
            "detalles",
            "detalle",
            "apply",
            "aplicar",
            "inscribirme",
            "inscribirse",
            "postular",
            "postularme",
        }
        if value in noise_values:
            return True
        return len(value) < 5

    async def _fallback_title_from_item_text(self, item: Any) -> str:
        try:
            raw = (await item.inner_text()).strip()
        except Exception:
            return ""
        if not raw:
            return ""

        for line in raw.split("\n"):
            candidate = line.strip()
            if self._is_noise_title(candidate):
                continue
            if len(candidate) < 8:
                continue
            return candidate
        return ""

    async def _extraer_con_requests(
        self, url: str, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        ofertas = []
        try:
            self.logger.info(f"Usando Requests para {url}")
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }

                # Prioridad 1: RSS Feed
                if "rss" in config:
                    rss_url = config["rss"]
                    self.logger.info(f"Descargando RSS: {rss_url}")
                    response = await client.get(rss_url, headers=headers)
                    response.raise_for_status()

                    rss_items = self._rss_items_from_xml(response.content)
                    self.logger.info(f"Encontrados {len(rss_items)} items en RSS")

                    if not rss_items:
                        self.logger.warning(
                            "RSS sin items en %s, usando fallback Playwright", rss_url
                        )
                        return await self._extraer_con_playwright(url, config)

                    for item in rss_items:
                        title = item.get("title") or "Sin título"
                        link = item.get("link", "")
                        pub_date = item.get("pub_date", "")
                        description = item.get("description", "")

                        if not self.filtrar_audiovisual(
                            title
                        ) and not self.filtrar_audiovisual(description):
                            continue

                        ofertas.append(
                            self.normalizar_oferta(
                                {
                                    "titulo_puesto": title,
                                    "enlace_fuente": link,
                                    "fecha_publicacion": pub_date,  # TODO: Parsear fecha real
                                    "descripcion": description[:200] + "...",
                                    "tipo_fuente": "rss",
                                }
                            )
                        )
                    return ofertas

                # Fallback a Playwright para HTML si no es RSS
                return await self._extraer_con_playwright(url, config)

        except Exception as e:
            self.logger.warning(f"Error con Requests en {url}: {e}")
            # Intentar fallback si falla requests
            return await self._extraer_con_playwright(url, config)
        return ofertas

    async def _extraer_con_playwright(
        self, url: str, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        ofertas = []
        page = None
        try:
            if self.browser is None:
                raise RuntimeError("Navegador no inicializado")
            assert self.browser is not None
            # Crear contexto con anti-bot
            user_agent = AntiBotManager.get_random_user_agent()
            context = await self.browser.new_context(
                user_agent=user_agent,
                viewport={"width": 1920, "height": 1080},
                locale="es-ES",
                timezone_id="Europe/Madrid",
            )
            page = await context.new_page()

            # Aplicar stealth anti-bot
            await AntiBotManager.apply_stealth(page)

            # Delay inicial humano
            await AntiBotManager.human_delay(2000, 4000)

            self.logger.info(
                f"Navegando con Playwright a {url} (UA: {user_agent[:30]}...)"
            )
            # Usar domcontentloaded para evitar timeouts en webs lentas
            await page.goto(
                url, timeout=settings.TIMEOUT, wait_until="domcontentloaded"
            )

            # Espera humana variable
            await asyncio.sleep(random.uniform(3, 6))

            # Scroll humano para activar lazy loading
            await AntiBotManager.scroll_human(page)

            # Delay adicional después de scroll
            await asyncio.sleep(random.uniform(settings.DELAY_MIN, settings.DELAY_MAX))

            # Si el config tiene wait_for, esperar a que el selector esté presente (ej. Milanuncios JS hydration)
            wait_for_selector = config.get("wait_for")
            if wait_for_selector:
                try:
                    await page.wait_for_selector(wait_for_selector, timeout=10000)
                    self.logger.info(f"wait_for satisfecho: {wait_for_selector}")
                except Exception:
                    self.logger.warning(f"wait_for timeout esperando '{wait_for_selector}' en {url}")

            container_selector = config.get(
                "container", "a.job-link, h2.title, a.titulo-oferta"
            )

            # Si esArtfy o similar que requiere interacción, scroll
            if "artfy" in url or "actorsbarcelona" in url:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)

            items = await page.query_selector_all(container_selector)
            self.logger.info(f"Encontrados {len(items)} elementos en {url}")

            title_selectors = self._split_selectors(config.get("title"))
            link_selectors = self._split_selectors(config.get("link"))
            company_value = str(config.get("company") or "").strip()
            location_selectors = self._split_selectors(config.get("location"))
            seen_links = set()

            for item in items[: settings.OFERTAS_POR_PORTAL]:
                try:
                    titulo = await self._first_text_from_selectors(
                        item, title_selectors
                    )
                    href = await self._first_href_from_selectors(item, link_selectors)

                    if not titulo or not href:
                        fallback_data = await self._fallback_item_data(item)
                        if not titulo:
                            titulo = fallback_data["title"]
                        if not href:
                            href = fallback_data["href"]

                    if not titulo:
                        continue

                    if self._is_noise_title(titulo):
                        better_title = await self._fallback_title_from_item_text(item)
                        if better_title:
                            titulo = better_title
                    if self._is_noise_title(titulo):
                        continue

                    # Filtrado (Relaxar para testing)
                    # if not self.filtrar_audiovisual(titulo):
                    #    continue

                    enlace_completo = urljoin(url, href)
                    if enlace_completo in seen_links:
                        continue
                    seen_links.add(enlace_completo)

                    # Empresa (opcional)
                    empresa = ""
                    if company_value:
                        if self._is_likely_css_selector(company_value):
                            empresa = await self._first_text_from_selectors(
                                item, self._split_selectors(company_value)
                            )
                        else:
                            empresa = company_value

                    # Ubicación (opcional)
                    ubicacion = ""
                    if location_selectors:
                        ubicacion = await self._first_text_from_selectors(
                            item, location_selectors
                        )

                    oferta = self.normalizar_oferta(
                        {
                            "titulo_puesto": titulo.strip(),
                            "enlace_fuente": enlace_completo,
                            "empresa": empresa.strip(),
                            "ubicacion": ubicacion.strip(),
                            "descripcion": f"Oferta extraída automáticamente de {url}",
                        }
                    )
                    ofertas.append(oferta)

                except Exception as e:
                    self.logger.debug(f"Error en elemento de {url}: {e}")
                    continue

            if not ofertas and items:
                self.logger.info(
                    "Sin ofertas válidas tras parseo principal en %s; aplicando fallback de anchors",
                    url,
                )
                ofertas = await self._fallback_anchor_offers(page, url)
                self.logger.info(
                    "Fallback de anchors extrajo %s ofertas en %s", len(ofertas), url
                )

        except Exception as e:
            self.logger.error(f"Error en Playwright para {url}: {e}")
        finally:
            if page:
                await page.close()
        return ofertas

    async def scrape(self) -> List[Dict[str, Any]]:
        self.logger.info(f"Iniciando scrape de {len(self.portales)} portales")
        await self._iniciar_navegador()

        try:
            for portal in self.portales:
                portal_started = time.perf_counter()
                if "platinoempleo.com" in portal:
                    self.logger.info(
                        "Saltando Platino Empleo (Requiere login/matchmaking)"
                    )
                    self._report_health(
                        source_url=portal,
                        status="requires_login",
                        latency_ms=int((time.perf_counter() - portal_started) * 1000),
                        items_detected=0,
                    )
                    continue

                config = self._obtener_config(portal)

                # Saltar portales desactivados
                if config.get("method") == "disabled":
                    self.logger.info(f"Saltando portal desactivado: {portal}")
                    continue

                # Soporte para múltiples URLs de búsqueda por portal (ej: LinkedIn × 6 roles, InfoJobs × 5 categorías)
                urls_busqueda = config.get("urls_busqueda")
                if urls_busqueda and isinstance(urls_busqueda, list):
                    self.logger.info(
                        f"Portal {portal}: {len(urls_busqueda)} URLs de búsqueda específicas"
                    )
                    urls_to_scrape = urls_busqueda
                else:
                    urls_to_scrape = [portal]

                ofertas_portal: List[Dict[str, Any]] = []
                last_error: Optional[str] = None

                for search_url in urls_to_scrape:
                    ofertas_url: List[Dict[str, Any]] = []

                    for intento in range(1, settings.MAX_REINTENTOS + 1):
                        try:
                            if config.get("method") == "requests":
                                ofertas_url = await self._extraer_con_requests(
                                    search_url, config
                                )
                            else:
                                ofertas_url = await self._extraer_con_playwright(
                                    search_url, config
                                )

                            self.logger.info(
                                "Extraídas %s ofertas de %s (intento %s)",
                                len(ofertas_url),
                                search_url,
                                intento,
                            )
                            break
                        except Exception as e:
                            last_error = str(e)
                            self.logger.error(
                                "Fallo en %s intento %s/%s: %s",
                                search_url,
                                intento,
                                settings.MAX_REINTENTOS,
                                e,
                            )
                            if intento < settings.MAX_REINTENTOS:
                                await asyncio.sleep(
                                    random.uniform(settings.DELAY_MIN, settings.DELAY_MAX)
                                )

                    ofertas_portal.extend(ofertas_url)

                    # Pausa humana entre URLs del mismo portal para evitar rate-limiting
                    if len(urls_to_scrape) > 1:
                        await asyncio.sleep(random.uniform(4, 8))

                self.ofertas_extraidas.extend(ofertas_portal)

                elapsed_ms = int((time.perf_counter() - portal_started) * 1000)
                if ofertas_portal:
                    status = "success"
                elif last_error:
                    status = "error"
                else:
                    status = "empty"

                self._report_health(
                    source_url=portal,
                    status=status,
                    latency_ms=elapsed_ms,
                    items_detected=len(ofertas_portal),
                    error_message=last_error,
                )

        finally:
            await self._cerrar_navegador()

        self.logger.info(f"Resultado final: {len(self.ofertas_extraidas)} ofertas")
        return self.ofertas_extraidas


def ejecutar_web_scraper(
    portales: Optional[List[str]] = None,
    db_client: Any = None,
) -> List[Dict[str, Any]]:
    """Función de entrada síncrona para ejecutar el scraper"""
    return asyncio.run(WebScraper(portales, db_client=db_client).scrape())
