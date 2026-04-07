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


class WorkanaScraper(BaseScraper):
    """Scraper para Workana con anti-bot 2026"""

    BASE_URL = "https://www.workana.com"
    KEYWORDS = [
        "video editor",
        "editor de video",
        "motion graphics",
        "postproduccion",
        "video production",
    ]

    def __init__(self):
        super().__init__()
        self.browser: Optional[Browser] = None
        self.playwright = None

    async def _iniciar_navegador(self):
        try:
            self.playwright = await async_playwright().start()
            profile = AntiBotManager.get_consistent_profile("workana")

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
            await AntiBotManager.apply_saved_cookies(context, "workana.com")

            self.logger.info("Navegador Workana iniciado")
            return context, page

        except Exception as e:
            self.logger.error(f"Error navegador Workana: {e}")
            raise

    async def scrape(self) -> List[Dict[str, Any]]:
        self.logger.info("Iniciando Workana scraper")

        context, page = None, None
        all_ofertas = []

        try:
            context, page = await self._iniciar_navegador()

            for keyword in self.KEYWORDS:
                url = f"{self.BASE_URL}/jobs?keyword={keyword.replace(' ', '+')}"
                self.logger.info(f"Buscando: {keyword}")

                try:
                    await AntiBotManager.handle_cloudflare_page(page, url, timeout=25)
                    await AntiBotManager.scroll_human(page)
                    await asyncio.sleep(2)

                    # Selectores para Workana
                    job_cards = await page.query_selector_all(
                        "div.job-box, article.job-item, div[class*='job']"
                    )

                    for card in job_cards[:20]:
                        try:
                            title_elem = await card.query_selector(
                                "h3 a, h2 a, a.job-title"
                            )
                            if not title_elem:
                                continue

                            title = (await title_elem.inner_text()).strip()
                            href = await title_elem.get_attribute("href")
                            if href and not href.startswith("http"):
                                href = urljoin(self.BASE_URL, href)

                            # Empresa
                            company = "No especificada"
                            company_elem = await card.query_selector(
                                "[class*='company'], .client"
                            )
                            if company_elem:
                                company = (await company_elem.inner_text()).strip()

                            # Descripción
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
                                        "ubicacion": "Freelance",
                                        "descripcion": desc,
                                        "enlace_fuente": href or "",
                                        "fecha_publicacion": datetime.now().isoformat(),
                                    }
                                )
                                if self.validar_calidad_oferta(oferta):
                                    all_ofertas.append(oferta)

                        except Exception:
                            continue

                    await AntiBotManager.human_delay(3000, 5000)

                except Exception as e:
                    self.logger.error(f"Error keyword {keyword}: {e}")

            if context:
                AntiBotManager.save_cookies(context, "workana.com")

            self.ofertas_extraidas = all_ofertas
            self.logger.info(f"Workana: {len(all_ofertas)} ofertas")
            return all_ofertas

        except Exception as e:
            self.logger.error(f"Error en Workana: {e}")
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


def ejecutar_workana_scraper() -> List[Dict[str, Any]]:
    return asyncio.run(WorkanaScraper().scrape())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ofertas = ejecutar_workana_scraper()
    print(f"\n=== WORKANA: {len(ofertas)} ofertas ===")
