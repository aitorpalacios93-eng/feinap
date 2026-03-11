"""
Scraper anti-bot mejorado con técnicas de evasión
"""

import asyncio
import random
from typing import Optional
from playwright.async_api import Page, BrowserContext


class AntiBotManager:
    """Gestiona técnicas anti-detection para Playwright"""

    # User agents rotativos de navegadores reales
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
    ]

    @staticmethod
    def get_random_user_agent() -> str:
        return random.choice(AntiBotManager.USER_AGENTS)

    @staticmethod
    async def apply_stealth(page: Page) -> None:
        """Aplica parches anti-detection a la página"""
        await page.add_init_script("""
            // Ocultar webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Ocultar chrome automation
            if (window.chrome) {
                Object.defineProperty(window.chrome, 'runtime', {
                    get: () => undefined
                });
            }
            
            // Modificar plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Modificar languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['es-ES', 'es', 'en-US', 'en']
            });
        """)

    @staticmethod
    async def human_delay(min_ms: int = 1000, max_ms: int = 3000) -> None:
        """Espera aleatoria tipo humano"""
        delay = random.randint(min_ms, max_ms)
        await asyncio.sleep(delay / 1000)

    @staticmethod
    async def scroll_human(page: Page) -> None:
        """Scroll aleatorio tipo humano"""
        for _ in range(random.randint(2, 5)):
            scroll_amount = random.randint(100, 500)
            await page.mouse.wheel(0, scroll_amount)
            await asyncio.sleep(random.uniform(0.5, 1.5))


# Lista de nuevas fuentes alternativas a InfoJobs
NUEVAS_FUENTES = [
    {
        "url": "https://www.productionparadise.com/jobs/search",
        "nombre": "Production Paradise",
        "categoria": "internacional",
        "extraction_method": "playwright",
        "selector": ".job-item",
        "title": ".job-title",
        "link": ".job-title a",
    },
    {
        "url": "https://www.mandy.com/jobs/",
        "nombre": "Mandy Network",
        "categoria": "internacional",
        "extraction_method": "playwright",
        "selector": ".job-row",
        "title": ".job-title",
        "link": ".job-title a",
    },
    {
        "url": "https://www.crewunited.com/es/jobs/",
        "nombre": "Crew United",
        "categoria": "sectorial",
        "extraction_method": "playwright",
        "selector": ".job-listing",
        "title": ".job-title",
        "link": ".job-title a",
    },
    {
        "url": "https://www.staffmeup.com/jobs",
        "nombre": "Staff Me Up",
        "categoria": "internacional",
        "extraction_method": "playwright",
        "selector": ".job-card",
        "title": ".job-title",
        "link": ".job-title a",
    },
    {
        "url": "https://www.filmingineurope.com/jobs",
        "nombre": "Filming in Europe",
        "categoria": "europa",
        "extraction_method": "playwright",
        "selector": ".job-offer",
        "title": ".offer-title",
        "link": ".offer-title a",
    },
    {
        "url": "https://www.bubble-jobs.com/jobs/",
        "nombre": "Bubble Jobs",
        "categoria": "creativo",
        "extraction_method": "playwright",
        "selector": ".job-listing-item",
        "title": ".job-title",
        "link": ".job-title a",
    },
    {
        "url": "https://www.talentmanager.eu/jobs",
        "nombre": "Talent Manager",
        "categoria": "europa",
        "extraction_method": "playwright",
        "selector": ".vacancy-item",
        "title": ".vacancy-title",
        "link": ".vacancy-title a",
    },
]
