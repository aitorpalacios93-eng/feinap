import asyncio
import logging
import random
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
from datetime import datetime
from playwright.async_api import (
    async_playwright,
    Browser,
    TimeoutError as PlaywrightTimeout,
)

from scrapers.base import BaseScraper
from scrapers.antibot_utils import (
    AntiBotManager,
    CloudflareSession,
    HEADLESS_NEW_ARGS,
    create_block_route,
)
from config.settings import settings


class MandyScraper(BaseScraper):
    """Scraper para Mandy.com con anti-bot avanzado 2026"""

    BASE_URL = "https://www.mandy.com"
    SEARCH_KEYWORDS = [
        "video editor",
        "film",
        "production",
        "camera operator",
        "director",
    ]

    def __init__(self):
        super().__init__()
        self.browser: Optional[Browser] = None
        self.playwright = None
        self.cf_session = CloudflareSession("mandy.com")

    async def _iniciar_navegador(self):
        """Inicia navegador con configuración stealth"""
        try:
            self.playwright = await async_playwright().start()

            # Obtener perfil consistente
            profile = AntiBotManager.get_consistent_profile("mandy")

            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=HEADLESS_NEW_ARGS,
            )

            context = await self.browser.new_context(
                user_agent=AntiBotManager.get_random_user_agent(),
                viewport=profile["viewport"],
                locale=profile["locale"],
                timezone_id=profile["timezone"],
                color_scheme="light",
                device_scale_factor=1,
            )

            page = await context.new_page()

            # Aplicar stealth patches
            await AntiBotManager.apply_stealth(page)

            # Bloquear recursos innecesarios
            page.route("**/*", create_block_route())

            # Intentar cargar cookies guardadas
            await AntiBotManager.apply_saved_cookies(context, "mandy.com")

            self.logger.info("Navegador Playwright iniciado con anti-bot 2026")
            return context, page

        except Exception as e:
            self.logger.error(f"Error al iniciar navegador: {e}")
            raise

    async def _extraer_pagina(self, page, url: str) -> List[Dict[str, Any]]:
        """Extrae ofertas de una página"""
        ofertas = []

        try:
            # Navegar con manejo de Cloudflare
            success = await AntiBotManager.handle_cloudflare_page(page, url, timeout=20)

            if not success:
                self.logger.warning(f"Cloudflare no resolvió para {url}")
                return []

            # Scroll humano para cargar contenido lazy
            await AntiBotManager.scroll_human(page)
            await asyncio.sleep(random.uniform(1, 3))

            # Esperar contenido
            try:
                await page.wait_for_selector(
                    "div.job-card, article.job, .job-listing, .job-item", timeout=10000
                )
            except Exception:
                self.logger.debug("No se encontró selector estándar")

            # Extraer ofertas
            job_cards = await page.query_selector_all(
                "div.job-card, article.job, .job-listing, .job-item, div[class*='job']"
            )

            self.logger.info(f"Encontrados {len(job_cards)} elementos de trabajo")

            for card in job_cards[:25]:
                try:
                    oferta = await self._procesar_card(card)
                    if oferta:
                        ofertas.append(oferta)
                except Exception as e:
                    self.logger.debug(f"Error procesando card: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error extrayendo página {url}: {e}")

        return ofertas

    async def _procesar_card(self, card) -> Optional[Dict[str, Any]]:
        """Procesa un card de oferta individual"""
        try:
            # Título - múltiples selectores
            title_elem = await card.query_selector(
                "h2 a, h3 a, a[class*='title'], .job-title a, [class*='title'] a"
            )
            if not title_elem:
                return None

            title = (await title_elem.inner_text()).strip()
            if not title or len(title) < 5:
                return None

            # URL
            href = await title_elem.get_attribute("href")
            if href and not href.startswith("http"):
                href = urljoin(self.BASE_URL, href)

            # Empresa
            company = "No especificada"
            company_elem = await card.query_selector(
                "[class*='company'], .employer, [class*='employer'], span.company"
            )
            if company_elem:
                company = (await company_elem.inner_text()).strip()

            # Ubicación
            location = "No especificada"
            location_elem = await card.query_selector(
                "[class*='location'], .city, [class*='location']"
            )
            if location_elem:
                location = (await location_elem.inner_text()).strip()

            # Salario
            salary = None
            salary_elem = await card.query_selector("[class*='salary'], .pay")
            if salary_elem:
                salary = (await salary_elem.inner_text()).strip()

            # Descripción
            desc = ""
            desc_elem = await card.query_selector("p, [class*='description'], .excerpt")
            if desc_elem:
                desc = (await desc_elem.inner_text()).strip()[:300]

            # Filtrar audiovisual
            if not self.filtrar_audiovisual(title + " " + desc):
                return None

            # Filtrar calidad
            oferta = self.normalizar_oferta(
                {
                    "titulo_puesto": title,
                    "empresa": company,
                    "ubicacion": location,
                    "descripcion": desc,
                    "enlace_fuente": href or "",
                    "salario": salary,
                    "fecha_publicacion": datetime.now().isoformat(),
                }
            )

            if not self.validar_calidad_oferta(oferta):
                return None

            return oferta

        except Exception as e:
            self.logger.debug(f"Error en procesar_card: {e}")
            return None

    async def scrape(self) -> List[Dict[str, Any]]:
        """Ejecuta el scraping"""
        self.logger.info("Iniciando Mandy scraper con anti-bot 2026")

        context = None
        page = None

        try:
            context, page = await self._iniciar_navegador()

            all_ofertas = []

            # Buscar con diferentes keywords
            for keyword in self.SEARCH_KEYWORDS:
                keyword_url = (
                    f"{self.BASE_URL}/aa/jobs/?keyword={keyword.replace(' ', '+')}"
                )
                self.logger.info(f"Buscando: {keyword}")

                ofertas = await self._extraer_pagina(page, keyword_url)
                all_ofertas.extend(ofertas)

                # Delay entre búsquedas
                await AntiBotManager.human_delay(3000, 6000)

            # También probar URL principal
            ofertas_main = await self._extraer_pagina(page, f"{self.BASE_URL}/aa/jobs/")
            all_ofertas.extend(ofertas_main)

            # Guardar cookies para futuras sesiones
            if context:
                AntiBotManager.save_cookies(context, "mandy.com")

            self.ofertas_extraidas = all_ofertas
            self.logger.info(f"Total ofertas extraídas de Mandy: {len(all_ofertas)}")
            return all_ofertas

        except Exception as e:
            self.logger.error(f"Error en scrape de Mandy: {e}")
            return []

        finally:
            if page:
                await page.close()
            if context:
                await context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()


def ejecutar_mandy_scraper() -> List[Dict[str, Any]]:
    """Función de entrada síncrona"""
    return asyncio.run(MandyScraper().scrape())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ofertas = ejecutar_mandy_scraper()
    print(f"\n=== MANDY: {len(ofertas)} ofertas ===")
    for o in ofertas[:5]:
        print(f"- {o.get('titulo_puesto', 'Sin título')} | {o.get('empresa', 'N/A')}")
