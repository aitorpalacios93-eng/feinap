import asyncio
import logging
import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlencode
from datetime import datetime
from playwright.async_api import async_playwright, Browser, BrowserContext

from scrapers.base import BaseScraper
from scrapers.antibot_utils import (
    AntiBotManager,
    HEADLESS_NEW_ARGS,
    create_block_route,
)


class InfoJobsScraper(BaseScraper):
    """
    Scraper para InfoJobs con anti-bot avanzado

    Usa API oficial si hay credenciales, o scraping con browser
    """

    BASE_URL = "https://www.infojobs.net"
    COOKIE_DIR = Path.home() / ".audiovisual_scraper_cookies"
    COOKIE_FILE = COOKIE_DIR / "infojobs_cookies.json"

    KEYWORDS = [
        "video editor",
        "editor video",
        "produccion audiovisual",
        "operador camara",
    ]
    LOCATION = "espana"

    def __init__(self):
        super().__init__()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    @classmethod
    def save_cookies(cls, cookies: List[Dict]) -> None:
        cls.COOKIE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(cls.COOKIE_FILE, "w") as f:
                json.dump(cookies, f)
        except Exception:
            pass

    @classmethod
    def load_cookies(cls) -> List[Dict]:
        try:
            if cls.COOKIE_FILE.exists():
                with open(cls.COOKIE_FILE, "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    async def _iniciar_navegador(self):
        try:
            self.playwright = await async_playwright().start()

            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=HEADLESS_NEW_ARGS,
            )

            context = await self.browser.new_context(
                user_agent=AntiBotManager.get_random_user_agent(),
                viewport={"width": 1920, "height": 1080},
                locale="es-ES",
                timezone_id="Europe/Madrid",
            )

            page = await context.new_page()
            await AntiBotManager.apply_stealth(page)
            page.route("**/*", create_block_route())

            # Cargar cookies
            cookies = self.load_cookies()
            if cookies:
                await context.add_cookies(cookies)
                self.logger.info("Cookies de InfoJobs cargadas")

            self.context = context
            return context, page

        except Exception as e:
            self.logger.error(f"Error navegador: {e}")
            raise

    async def scrape(self) -> List[Dict[str, Any]]:
        self.logger.info("Iniciando InfoJobs scraper")

        page, context = None, None
        all_ofertas = []

        try:
            context, page = await self._iniciar_navegador()

            for keyword in self.KEYWORDS:
                url = f"{self.BASE_URL}/jobsearch/resultatsRH.do?keyword={keyword.replace(' ', '+')}"
                self.logger.info(f"Buscando: {keyword}")

                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=25000)
                    await AntiBotManager.human_delay(3000, 5000)
                    await AntiBotManager.scroll_human(page)

                    # Selectores InfoJobs
                    job_cards = await page.query_selector_all(
                        "div[class*='job'], article.job-item, li.resultats-obj"
                    )

                    for card in job_cards[:15]:
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

                            if self.filtrar_audiovisual(title):
                                oferta = self.normalizar_oferta(
                                    {
                                        "titulo_puesto": title,
                                        "empresa": company,
                                        "ubicacion": "España",
                                        "descripcion": "",
                                        "enlace_fuente": href or "",
                                        "fecha_publicacion": datetime.now().isoformat(),
                                        "source_domain": "infojobs.net",
                                    }
                                )
                                if self.validar_calidad_oferta(oferta):
                                    all_ofertas.append(oferta)

                        except:
                            continue

                    await AntiBotManager.human_delay(3000, 6000)

                except Exception as e:
                    self.logger.error(f"Error keyword {keyword}: {e}")

            # Guardar cookies
            if context:
                cookies = await context.cookies()
                self.save_cookies(cookies)

            self.ofertas_extraidas = all_ofertas
            self.logger.info(f"InfoJobs: {len(all_ofertas)} ofertas")
            return all_ofertas

        except Exception as e:
            self.logger.error(f"Error en InfoJobs: {e}")
            return []

        finally:
            if page:
                await page.close()
            if context:
                await context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, "playwright") and self.playwright:
                await self.playwright.stop()


class IndeedScraper(BaseScraper):
    """
    Scraper para Indeed con anti-bot avanzado

    Indeed es muy agresivo con anti-bot. Usa técnicas especiales.
    """

    BASE_URL = "https://es.indeed.com"
    COOKIE_DIR = Path.home() / ".audiovisual_scraper_cookies"
    COOKIE_FILE = COOKIE_DIR / "indeed_cookies.json"

    KEYWORDS = ["video editor", "video production", "film editor", "camera operator"]
    LOCATIONS = ["Spain", "Madrid", "Barcelona"]

    def __init__(self):
        super().__init__()
        self.browser = None

    @classmethod
    def save_cookies(cls, cookies: List[Dict]) -> None:
        cls.COOKIE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(cls.COOKIE_FILE, "w") as f:
                json.dump(cookies, f)
        except Exception:
            pass

    @classmethod
    def load_cookies(cls) -> List[Dict]:
        try:
            if cls.COOKIE_FILE.exists():
                with open(cls.COOKIE_FILE, "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    async def scrape(self) -> List[Dict[str, Any]]:
        self.logger.info("Iniciando Indeed scraper")

        all_ofertas = []

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=HEADLESS_NEW_ARGS,
                )

                context = await browser.new_context(
                    user_agent=AntiBotManager.get_random_user_agent(),
                    viewport={"width": 1920, "height": 1080},
                    locale="es-ES",
                    timezone_id="Europe/Madrid",
                )

                # Cargar cookies
                cookies = self.load_cookies()
                if cookies:
                    await context.add_cookies(cookies)

                page = await context.new_page()
                await AntiBotManager.apply_stealth(page)
                page.route("**/*", create_block_route())

                for keyword in self.KEYWORDS[:2]:
                    for location in self.LOCATIONS[:2]:
                        url = f"{self.BASE_URL}/jobs?q={keyword.replace(' ', '+')}&l={location}"
                        self.logger.info(f"Buscando: {keyword} en {location}")

                        try:
                            await page.goto(
                                url, wait_until="domcontentloaded", timeout=20000
                            )
                            await AntiBotManager.human_delay(3000, 6000)
                            await AntiBotManager.scroll_human(page)

                            # Selectores Indeed
                            job_cards = await page.query_selector_all(
                                "div.job_seen_beacon, div.job-card, li.jobsearch-ResultsJobLetter"
                            )

                            for card in job_cards[:10]:
                                try:
                                    title_elem = await card.query_selector(
                                        "h2.jobTitle a, h2 a, a.jobtitle"
                                    )
                                    if not title_elem:
                                        continue

                                    title = (await title_elem.inner_text()).strip()
                                    href = await title_elem.get_attribute("href")
                                    if href and not href.startswith("http"):
                                        href = urljoin(self.BASE_URL, href)

                                    company = "No especificada"
                                    company_elem = await card.query_selector(
                                        "[class*='company'], span.company"
                                    )
                                    if company_elem:
                                        company = (
                                            await company_elem.inner_text()
                                        ).strip()

                                    location_text = location
                                    location_elem = await card.query_selector(
                                        "[class*='location'], .location"
                                    )
                                    if location_elem:
                                        location_text = (
                                            await location_elem.inner_text()
                                        ).strip()

                                    if self.filtrar_audiovisual(title):
                                        oferta = self.normalizar_oferta(
                                            {
                                                "titulo_puesto": title,
                                                "empresa": company,
                                                "ubicacion": location_text,
                                                "descripcion": "",
                                                "enlace_fuente": href or "",
                                                "fecha_publicacion": datetime.now().isoformat(),
                                                "source_domain": "indeed.com",
                                            }
                                        )
                                        if self.validar_calidad_oferta(oferta):
                                            all_ofertas.append(oferta)

                                except:
                                    continue

                            await AntiBotManager.human_delay(4000, 7000)

                        except Exception as e:
                            self.logger.error(f"Error búsqueda: {e}")

                # Guardar cookies
                cookies = await context.cookies()
                self.save_cookies(cookies)

                await browser.close()

        except Exception as e:
            self.logger.error(f"Error en Indeed: {e}")

        self.ofertas_extraidas = all_ofertas
        self.logger.info(f"Indeed: {len(all_ofertas)} ofertas")
        return all_ofertas


def ejecutar_infojobs_scraper() -> List[Dict[str, Any]]:
    return asyncio.run(InfoJobsScraper().scrape())


def ejecutar_indeed_scraper() -> List[Dict[str, Any]]:
    return asyncio.run(IndeedScraper().scrape())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== InfoJobs ===")
    ofertas_ij = ejecutar_infojobs_scraper()
    print(f"InfoJobs: {len(ofertas_ij)} ofertas")

    print("\n=== Indeed ===")
    ofertas_indeed = ejecutar_indeed_scraper()
    print(f"Indeed: {len(ofertas_indeed)} ofertas")
