import asyncio
import logging
import random
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
from datetime import datetime
from playwright.async_api import async_playwright, Browser

from scrapers.base import BaseScraper
from scrapers.antibot_utils import AntiBotManager, HEADLESS_NEW_ARGS, create_block_route


class WeRemotoScraper(BaseScraper):
    """Scraper para WeRemoto - remote LatAm"""

    BASE_URL = "https://weremoto.com"
    KEYWORDS = ["video", "editor", "motion graphics", "production", "audiovisual"]

    def __init__(self):
        super().__init__()
        self.browser: Optional[Browser] = None
        self.playwright = None

    async def _iniciar_navegador(self):
        try:
            self.playwright = await async_playwright().start()
            profile = AntiBotManager.get_consistent_profile("weremoto")

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

            self.logger.info("Navegador WeRemoto iniciado")
            return context, page

        except Exception as e:
            self.logger.error(f"Error navegador: {e}")
            raise

    async def scrape(self) -> List[Dict[str, Any]]:
        self.logger.info("Iniciando WeRemoto scraper")

        context, page = None, None
        all_ofertas = []

        try:
            context, page = await self._iniciar_navegador()

            # WeRemoto tiene búsqueda
            url = f"{self.BASE_URL}/jobs?q=video"
            self.logger.info(f"Navegando a: {url}")

            try:
                # Intentar HTTP primero si HTTPS falla
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                except Exception:
                    # Fallback a HTTP
                    http_url = url.replace("https://", "http://")
                    await page.goto(
                        http_url, wait_until="domcontentloaded", timeout=15000
                    )

                await AntiBotManager.human_delay(2000, 4000)
                await AntiBotManager.scroll_human(page)

                # Selectores WeRemoto
                job_cards = await page.query_selector_all(
                    "div.job-card, article.job, .job-listing, div[class*='job'], a.job-link"
                )

                self.logger.info(f"Encontrados {len(job_cards)} elementos")

                for card in job_cards[:20]:
                    try:
                        title_elem = await card.query_selector(
                            "h3 a, h2 a, a[class*='title'], .job-title"
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

                        location = "LatAm Remote"
                        location_elem = await card.query_selector(
                            "[class*='location'], .location"
                        )
                        if location_elem:
                            location = (await location_elem.inner_text()).strip()

                        desc = ""
                        desc_elem = await card.query_selector(
                            "p, [class*='description']"
                        )
                        if desc_elem:
                            desc = (await desc_elem.inner_text()).strip()[:300]

                        if self.filtrar_audiovisual(title + " " + desc):
                            oferta = self.normalizar_oferta(
                                {
                                    "titulo_puesto": title,
                                    "empresa": company,
                                    "ubicacion": location,
                                    "descripcion": desc,
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
            self.logger.info(f"WeRemoto: {len(all_ofertas)} ofertas")
            return all_ofertas

        except Exception as e:
            self.logger.error(f"Error en WeRemoto: {e}")
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


def ejecutar_weremoto_scraper() -> List[Dict[str, Any]]:
    return asyncio.run(WeRemotoScraper().scrape())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ofertas = ejecutar_weremoto_scraper()
    print(f"\n=== WEREMOTO: {len(ofertas)} ofertas ===")
