import asyncio
import logging
import random
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
from datetime import datetime
from playwright.async_api import async_playwright, Browser

from scrapers.base import BaseScraper
from scrapers.antibot_utils import AntiBotManager, HEADLESS_NEW_ARGS, create_block_route


class ProductionHubScraper(BaseScraper):
    """Scraper para ProductionHUB - bolsa audiovisual USA"""

    BASE_URL = "https://www.productionhub.com"
    KEYWORDS = ["video editor", "camera operator", "film production", "director"]

    def __init__(self):
        super().__init__()
        self.browser: Optional[Browser] = None
        self.playwright = None

    async def _iniciar_navegador(self):
        try:
            self.playwright = await async_playwright().start()
            profile = AntiBotManager.get_consistent_profile("productionhub")

            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=HEADLESS_NEW_ARGS,
            )

            context = await self.browser.new_context(
                user_agent=AntiBotManager.get_random_user_agent(),
                viewport=profile["viewport"],
                locale=profile["locale"],
                timezone_id=profile["timezone"],
            )

            page = await context.new_page()
            await AntiBotManager.apply_stealth(page)
            page.route("**/*", create_block_route())

            self.logger.info("Navegador ProductionHUB iniciado")
            return context, page

        except Exception as e:
            self.logger.error(f"Error navegador: {e}")
            raise

    async def scrape(self) -> List[Dict[str, Any]]:
        self.logger.info("Iniciando ProductionHUB scraper")

        context, page = None, None
        all_ofertas = []

        try:
            context, page = await self._iniciar_navegador()

            # ProductionHUB tiene búsqueda de jobs
            url = f"{self.BASE_URL}/jobs"
            self.logger.info(f"Navegando a: {url}")

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                await AntiBotManager.human_delay(2000, 4000)
                await AntiBotManager.scroll_human(page)

                # Buscar input de búsqueda y realizar búsqueda
                try:
                    search_input = await page.query_selector(
                        "input[name*='search'], input[type='search']"
                    )
                    if search_input:
                        await search_input.fill("video")
                        await search_input.press("Enter")
                        await asyncio.sleep(3)
                except:
                    pass

                # Extraer ofertas
                job_cards = await page.query_selector_all(
                    "div.job-card, article.job, .job-listing, div[class*='job-item']"
                )

                self.logger.info(f"Encontrados {len(job_cards)} elementos")

                for card in job_cards[:20]:
                    try:
                        title_elem = await card.query_selector(
                            "h3 a, h2 a, a[class*='title']"
                        )
                        if not title_elem:
                            continue

                        title = (await title_elem.inner_text()).strip()
                        href = await title_elem.get_attribute("href")
                        if href and not href.startswith("http"):
                            href = urljoin(self.BASE_URL, href)

                        company = "No especificada"
                        company_elem = await card.query_selector(
                            "[class*='company'], .company-name"
                        )
                        if company_elem:
                            company = (await company_elem.inner_text()).strip()

                        location = "USA"
                        location_elem = await card.query_selector(
                            "[class*='location'], .location"
                        )
                        if location_elem:
                            location = (await location_elem.inner_text()).strip()

                        if self.filtrar_audiovisual(title):
                            oferta = self.normalizar_oferta(
                                {
                                    "titulo_puesto": title,
                                    "empresa": company,
                                    "ubicacion": location,
                                    "descripcion": "",
                                    "enlace_fuente": href or "",
                                    "fecha_publicacion": datetime.now().isoformat(),
                                }
                            )
                            if self.validar_calidad_oferta(oferta):
                                all_ofertas.append(oferta)

                    except:
                        continue

            except Exception as e:
                self.logger.error(f"Error extrayendo: {e}")

            self.ofertas_extraidas = all_ofertas
            self.logger.info(f"ProductionHUB: {len(all_ofertas)} ofertas")
            return all_ofertas

        except Exception as e:
            self.logger.error(f"Error en ProductionHUB: {e}")
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


def ejecutar_productionhub_scraper() -> List[Dict[str, Any]]:
    return asyncio.run(ProductionHubScraper().scrape())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ofertas = ejecutar_productionhub_scraper()
    print(f"\n=== PRODUCTIONHUB: {len(ofertas)} ofertas ===")
