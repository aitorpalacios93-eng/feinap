import asyncio
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
from datetime import datetime
from playwright.async_api import async_playwright, Browser

from scrapers.base import BaseScraper
from scrapers.antibot_utils import AntiBotManager, HEADLESS_NEW_ARGS, create_block_route


class OlaCreatorsScraper(BaseScraper):
    """Scraper para Ola Creators - creadores España"""

    BASE_URL = "https://www.olacreators.com"

    def __init__(self):
        super().__init__()
        self.browser: Optional[Browser] = None
        self.playwright = None

    async def _iniciar_navegador(self):
        try:
            self.playwright = await async_playwright().start()
            profile = AntiBotManager.get_consistent_profile("olacreators")

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

            return context, page

        except Exception as e:
            self.logger.error(f"Error navegador: {e}")
            raise

    async def scrape(self) -> List[Dict[str, Any]]:
        self.logger.info("Iniciando Ola Creators scraper")

        context, page = None, None
        all_ofertas = []

        try:
            context, page = await self._iniciar_navegador()

            url = f"{self.BASE_URL}/jobs"
            self.logger.info(f"Navegando a: {url}")

            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await AntiBotManager.human_delay(2000, 4000)
            await AntiBotManager.scroll_human(page)

            job_cards = await page.query_selector_all(
                "div.job-card, article.job, .job-listing, div[class*='job']"
            )

            for card in job_cards[:20]:
                try:
                    title_elem = await card.query_selector("h3 a, h2 a, a")
                    if not title_elem:
                        continue

                    title = (await title_elem.inner_text()).strip()
                    href = await title_elem.get_attribute("href")
                    if href and not href.startswith("http"):
                        href = urljoin(self.BASE_URL, href)

                    if self.filtrar_audiovisual(title):
                        oferta = self.normalizar_oferta(
                            {
                                "titulo_puesto": title,
                                "empresa": "Ola Creators",
                                "ubicacion": "España",
                                "descripcion": "",
                                "enlace_fuente": href or "",
                                "fecha_publicacion": datetime.now().isoformat(),
                            }
                        )
                        all_ofertas.append(oferta)
                except:
                    continue

            self.ofertas_extraidas = all_ofertas
            return all_ofertas

        finally:
            if page:
                await page.close()
            if context:
                await context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()


class NotodoAnimacionScraper(BaseScraper):
    """Scraper para NotodoAnimación"""

    BASE_URL = "https://www.notodoanimacion.es"

    def __init__(self):
        super().__init__()
        self.browser: Optional[Browser] = None
        self.playwright = None

    async def scrape(self) -> List[Dict[str, Any]]:
        self.logger.info("Iniciando NotodoAnimación scraper")

        all_ofertas = []

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=HEADLESS_NEW_ARGS)
                context = await browser.new_context(
                    user_agent=AntiBotManager.get_random_user_agent(),
                )
                page = await context.new_page()
                await AntiBotManager.apply_stealth(page)

                url = f"{self.BASE_URL}/empleo"
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                await AntiBotManager.human_delay(2000, 4000)

                cards = await page.query_selector_all(
                    "article, div.job-item, div.listing-item"
                )

                for card in cards[:15]:
                    try:
                        title_elem = await card.query_selector("h2 a, h3 a, a")
                        if not title_elem:
                            continue

                        title = (await title_elem.inner_text()).strip()
                        href = await title_elem.get_attribute("href")

                        if self.filtrar_audiovisual(title):
                            oferta = self.normalizar_oferta(
                                {
                                    "titulo_puesto": title,
                                    "empresa": "NotodoAnimación",
                                    "ubicacion": "España",
                                    "descripcion": "",
                                    "enlace_fuente": href or "",
                                    "fecha_publicacion": datetime.now().isoformat(),
                                }
                            )
                            all_ofertas.append(oferta)
                    except:
                        continue

                await browser.close()

        except Exception as e:
            self.logger.error(f"Error: {e}")

        return all_ofertas


class IndustriaAnimacionScraper(BaseScraper):
    """Scraper para Industria Animación"""

    BASE_URL = "https://www.industriaanimacion.com"

    def __init__(self):
        super().__init__()
        self.browser = None

    async def scrape(self) -> List[Dict[str, Any]]:
        self.logger.info("Iniciando Industria Animación scraper")

        all_ofertas = []

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=HEADLESS_NEW_ARGS)
                context = await browser.new_context(
                    user_agent=AntiBotManager.get_random_user_agent(),
                )
                page = await context.new_page()
                await AntiBotManager.apply_stealth(page)

                url = f"{self.BASE_URL}/empleo"
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)

                cards = await page.query_selector_all(
                    "article, div.job-item, div.listing-item"
                )

                for card in cards[:15]:
                    try:
                        title_elem = await card.query_selector("h2 a, h3 a, a")
                        if not title_elem:
                            continue

                        title = (await title_elem.inner_text()).strip()
                        href = await title_elem.get_attribute("href")

                        if self.filtrar_audiovisual(title):
                            oferta = self.normalizar_oferta(
                                {
                                    "titulo_puesto": title,
                                    "empresa": "Industria Animación",
                                    "ubicacion": "Iberoamérica",
                                    "descripcion": "",
                                    "enlace_fuente": href or "",
                                    "fecha_publicacion": datetime.now().isoformat(),
                                }
                            )
                            all_ofertas.append(oferta)
                    except:
                        continue

                await browser.close()

        except Exception as e:
            self.logger.error(f"Error: {e}")

        return all_ofertas


class CrewUnitedScraper(BaseScraper):
    """Scraper para Crew United - audiovisual Europa"""

    BASE_URL = "https://www.crew-united.com"

    def __init__(self):
        super().__init__()
        self.browser = None

    async def scrape(self) -> List[Dict[str, Any]]:
        self.logger.info("Iniciando Crew United scraper")

        all_ofertas = []

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=HEADLESS_NEW_ARGS)
                context = await browser.new_context(
                    user_agent=AntiBotManager.get_random_user_agent(),
                )
                page = await context.new_page()
                await AntiBotManager.apply_stealth(page)

                url = f"{self.BASE_URL}/es/jobs/"
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                await AntiBotManager.human_delay(2000, 4000)

                cards = await page.query_selector_all(
                    "div.job-listing, article.job, div.job-item"
                )

                for card in cards[:20]:
                    try:
                        title_elem = await card.query_selector("h3 a, h2 a")
                        if not title_elem:
                            continue

                        title = (await title_elem.inner_text()).strip()
                        href = await title_elem.get_attribute("href")
                        if href and not href.startswith("http"):
                            href = urljoin(self.BASE_URL, href)

                        if self.filtrar_audiovisual(title):
                            oferta = self.normalizar_oferta(
                                {
                                    "titulo_puesto": title,
                                    "empresa": "Crew United",
                                    "ubicacion": "Europa",
                                    "descripcion": "",
                                    "enlace_fuente": href or "",
                                    "fecha_publicacion": datetime.now().isoformat(),
                                }
                            )
                            all_ofertas.append(oferta)
                    except:
                        continue

                await browser.close()

        except Exception as e:
            self.logger.error(f"Error: {e}")

        return all_ofertas


class DeVuegoScraper(BaseScraper):
    """Scraper para DeVuego - videojuegos España"""

    BASE_URL = "https://www.devuego.org"

    def __init__(self):
        super().__init__()
        self.browser = None

    async def scrape(self) -> List[Dict[str, Any]]:
        self.logger.info("Iniciando DeVuego scraper")

        all_ofertas = []

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=HEADLESS_NEW_ARGS)
                context = await browser.new_context(
                    user_agent=AntiBotManager.get_random_user_agent(),
                )
                page = await context.new_page()
                await AntiBotManager.apply_stealth(page)

                # DeVuego puede tener sección de empleo
                urls_to_try = [
                    f"{BASE_URL}/empleo",
                    f"{BASE_URL}/jobs",
                    BASE_URL,
                ]

                for url in urls_to_try:
                    try:
                        await page.goto(
                            url, wait_until="domcontentloaded", timeout=10000
                        )
                        break
                    except:
                        continue

                await AntiBotManager.human_delay(1500, 3000)

                # Buscar cualquier contenido de trabajo
                links = await page.query_selector_all(
                    "a[href*='empleo'], a[href*='job'], a[href*='trabajo']"
                )

                for link in links[:15]:
                    try:
                        title = (await link.inner_text()).strip()
                        href = await link.get_attribute("href")

                        if title and len(title) > 5 and self.filtrar_audiovisual(title):
                            oferta = self.normalizar_oferta(
                                {
                                    "titulo_puesto": title,
                                    "empresa": "DeVuego",
                                    "ubicacion": "España",
                                    "descripcion": "",
                                    "enlace_fuente": href or "",
                                    "fecha_publicacion": datetime.now().isoformat(),
                                }
                            )
                            all_ofertas.append(oferta)
                    except:
                        continue

                await browser.close()

        except Exception as e:
            self.logger.error(f"Error: {e}")

        return all_ofertas


class ScreenSkillsScraper(BaseScraper):
    """Scraper para Screen Skills - cine/TV UK"""

    BASE_URL = "https://www.screenskills.com"

    def __init__(self):
        super().__init__()
        self.browser = None

    async def scrape(self) -> List[Dict[str, Any]]:
        self.logger.info("Iniciando Screen Skills scraper")

        all_ofertas = []

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=HEADLESS_NEW_ARGS)
                context = await browser.new_context(
                    user_agent=AntiBotManager.get_random_user_agent(),
                )
                page = await context.new_page()
                await AntiBotManager.apply_stealth(page)

                url = f"{self.BASE_URL}/jobs"
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                await AntiBotManager.human_delay(2000, 4000)

                cards = await page.query_selector_all(
                    "div.job-card, article.job, .job-item"
                )

                for card in cards[:15]:
                    try:
                        title_elem = await card.query_selector("h3 a, h2 a")
                        if not title_elem:
                            continue

                        title = (await title_elem.inner_text()).strip()
                        href = await title_elem.get_attribute("href")
                        if href and not href.startswith("http"):
                            href = urljoin(self.BASE_URL, href)

                        if self.filtrar_audiovisual(title):
                            oferta = self.normalizar_oferta(
                                {
                                    "titulo_puesto": title,
                                    "empresa": "Screen Skills",
                                    "ubicacion": "UK",
                                    "descripcion": "",
                                    "enlace_fuente": href or "",
                                    "fecha_publicacion": datetime.now().isoformat(),
                                }
                            )
                            all_ofertas.append(oferta)
                    except:
                        continue

                await browser.close()

        except Exception as e:
            self.logger.error(f"Error: {e}")

        return all_ofertas


# Funciones de entrada síncronas
def ejecutar_ola_creators_scraper() -> List[Dict[str, Any]]:
    return asyncio.run(OlaCreatorsScraper().scrape())


def ejecutar_notodo_animacion_scraper() -> List[Dict[str, Any]]:
    return asyncio.run(NotodoAnimacionScraper().scrape())


def ejecutar_industria_animacion_scraper() -> List[Dict[str, Any]]:
    return asyncio.run(IndustriaAnimacionScraper().scrape())


def ejecutar_crew_united_scraper() -> List[Dict[str, Any]]:
    return asyncio.run(CrewUnitedScraper().scrape())


def ejecutar_devuego_scraper() -> List[Dict[str, Any]]:
    return asyncio.run(DeVuegoScraper().scrape())


def ejecutar_screenskills_scraper() -> List[Dict[str, Any]]:
    return asyncio.run(ScreenSkillsScraper().scrape())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test todos
    scrapers = [
        ("Ola Creators", ejecutar_ola_creators_scraper),
        ("Notodo", ejecutar_notodo_animacion_scraper),
        ("Industria", ejecutar_industria_animacion_scraper),
        ("Crew United", ejecutar_crew_united_scraper),
        ("DeVuego", ejecutar_devuego_scraper),
        ("Screen Skills", ejecutar_screenskills_scraper),
    ]

    for name, func in scrapers:
        try:
            ofertas = func()
            print(f"=== {name}: {len(ofertas)} ofertas ===")
        except Exception as e:
            print(f"=== {name}: ERROR - {e} ===")
