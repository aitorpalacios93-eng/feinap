import asyncio
import logging
import random
import json
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


class LinkedInScraper(BaseScraper):
    """
    Scraper para LinkedIn Jobs con anti-bot avanzado

    IMPORTANTE: LinkedIn tiene protecciones muy fuertes. Este scraper usa:
    1. Persistent context con cookies guardadas
    2. Modo headless=new
    3. Retry con backoff exponencial
    4. Navegación humana

    Para que funcione, primero necesitas:
    1. Iniciar sesión manualmente en LinkedIn
    2. Exportar las cookies del navegador
    3. Guardarlas en ~/.audiovisual_scraper_cookies/linkedin_cookies.json
    """

    BASE_URL = "https://www.linkedin.com"
    COOKIE_DIR = Path.home() / ".audiovisual_scraper_cookies"
    COOKIE_FILE = COOKIE_DIR / "linkedin_cookies.json"

    KEYWORDS = [
        "video editor",
        "video producer",
        "camera operator",
        "film editor",
        "motion graphics",
    ]
    LOCATIONS = ["Spain", "Madrid", "Barcelona", "Remote"]

    def __init__(self):
        super().__init__()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    @classmethod
    def save_linkedin_cookies(cls, cookies: List[Dict]) -> None:
        """Guarda cookies de LinkedIn"""
        cls.COOKIE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(cls.COOKIE_FILE, "w") as f:
                json.dump(cookies, f)
        except Exception as e:
            print(f"Error guardando cookies: {e}")

    @classmethod
    def load_linkedin_cookies(cls) -> List[Dict]:
        """Carga cookies guardadas de LinkedIn"""
        try:
            if cls.COOKIE_FILE.exists():
                with open(cls.COOKIE_FILE, "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    async def _iniciar_navegador(self, use_cookies: bool = True):
        """Inicia navegador con sesión de LinkedIn"""
        try:
            self.playwright = await async_playwright().start()

            # Intentar usar el nuevo headless mode
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=HEADLESS_NEW_ARGS,
            )

            context = await self.browser.new_context(
                user_agent=AntiBotManager.get_random_user_agent(),
                viewport={"width": 1920, "height": 1080},
                locale="es-ES",
                timezone_id="Europe/Madrid",
                color_scheme="light",
            )

            # Aplicar stealth
            page = await context.new_page()
            await AntiBotManager.apply_stealth(page)

            # Bloquear recursos innecesarios
            page.route("**/*", create_block_route())

            # Cargar cookies si existen
            if use_cookies:
                cookies = self.load_linkedin_cookies()
                if cookies:
                    await context.add_cookies(cookies)
                    self.logger.info("Cookies de LinkedIn cargadas")
                else:
                    self.logger.warning("No hay cookies de LinkedIn guardadas")

            self.context = context
            return context, page

        except Exception as e:
            self.logger.error(f"Error al iniciar navegador: {e}")
            raise

    async def _buscar_con_retry(
        self, page, keyword: str, location: str, max_reintentos: int = 3
    ) -> List[Dict]:
        """Busca con retry y backoff"""
        ofertas = []

        # URL de búsqueda de LinkedIn Jobs
        params = {"keywords": keyword, "location": location}
        url = f"{self.BASE_URL}/jobs/search/?{urlencode(params)}"

        for intento in range(max_reintentos):
            try:
                self.logger.info(
                    f"Buscando: {keyword} en {location} (intento {intento + 1})"
                )

                # Navegar con wait largo
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)

                # Espera adicional para Cloudflare
                await asyncio.sleep(random.uniform(3, 6))

                # Scroll para cargar contenido
                await AntiBotManager.scroll_human(page)

                # Esperar que carguen los resultados
                try:
                    await page.wait_for_selector(
                        ".job-card-container, ul.jobs-list, li.job-card-list__item",
                        timeout=15000,
                    )
                except Exception:
                    pass

                # Extraer ofertas
                job_cards = await page.query_selector_all(
                    ".job-card-container, li.job-card-list__item, div[class*='job-card']"
                )

                self.logger.info(f"Encontrados {len(job_cards)} elementos")

                for card in job_cards[:15]:
                    try:
                        title_elem = await card.query_selector(
                            "h3 a, h2 a, .job-card-list__title a"
                        )
                        if not title_elem:
                            continue

                        title = (await title_elem.inner_text()).strip()
                        href = await title_elem.get_attribute("href")
                        if href and not href.startswith("http"):
                            href = urljoin(self.BASE_URL, href)

                        company = "No especificada"
                        company_elem = await card.query_selector(
                            "[class*='company'], .job-card-container__company-name"
                        )
                        if company_elem:
                            company = (await company_elem.inner_text()).strip()

                        location_text = location
                        location_elem = await card.query_selector(
                            "[class*='location'], .job-card-container__metadata-item"
                        )
                        if location_elem:
                            location_text = (await location_elem.inner_text()).strip()

                        if self.filtrar_audiovisual(title):
                            oferta = self.normalizar_oferta(
                                {
                                    "titulo_puesto": title,
                                    "empresa": company,
                                    "ubicacion": location_text,
                                    "descripcion": "",
                                    "enlace_fuente": href or "",
                                    "fecha_publicacion": datetime.now().isoformat(),
                                    "source_domain": "linkedin.com",
                                }
                            )
                            if self.validar_calidad_oferta(oferta):
                                ofertas.append(oferta)

                    except Exception:
                        continue

                # Si encontramos ofertas, salir del retry
                if ofertas:
                    break

            except Exception as e:
                self.logger.warning(f"Intento {intento + 1} falló: {e}")
                # Backoff exponencial
                await asyncio.sleep(2**intento + random.uniform(1, 3))

        return ofertas

    async def scrape(self) -> List[Dict[str, Any]]:
        """Ejecuta el scraping de LinkedIn"""
        self.logger.info("Iniciando LinkedIn scraper")

        page = None
        context = None
        all_ofertas = []

        try:
            context, page = await self._iniciar_navegador(use_cookies=True)

            # Guardar cookies después de navegar
            if context:

                @page.on("requestfinished")
                async def save_cookies(request):
                    pass

            # Buscar con diferentes keywords y locations
            for keyword in self.KEYWORDS:
                for location in self.LOCATIONS[:2]:  # Limitar para no sobrecargar
                    ofertas = await self._buscar_con_retry(page, keyword, location)
                    all_ofertas.extend(ofertas)
                    await AntiBotManager.human_delay(4000, 7000)

            # Guardar cookies de la sesión
            if context:
                cookies = await context.cookies()
                self.save_linkedin_cookies(cookies)
                self.logger.info("Cookies de LinkedIn guardadas")

            self.ofertas_extraidas = all_ofertas
            self.logger.info(f"LinkedIn: {len(all_ofertas)} ofertas extraídas")
            return all_ofertas

        except Exception as e:
            self.logger.error(f"Error en LinkedIn scraper: {e}")
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


def ejecutar_linkedin_scraper() -> List[Dict[str, Any]]:
    """Función de entrada síncrona"""
    return asyncio.run(LinkedInScraper().scrape())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ofertas = ejecutar_linkedin_scraper()
    print(f"\n=== LINKEDIN: {len(ofertas)} ofertas ===")
    for o in ofertas[:5]:
        print(f"- {o.get('titulo_puesto', 'Sin título')} | {o.get('empresa', 'N/A')}")
