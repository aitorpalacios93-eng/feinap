"""
Scraper anti-bot mejorado con técnicas de evasión 2026
Implementa: playwright-stealth patches, cookies persistentes, Cloudflare handling
"""

import asyncio
import json
import os
import random
from pathlib import Path
from typing import Optional, Dict, Any, List
from playwright.async_api import Page, BrowserContext


class AntiBotManager:
    """Gestiona técnicas anti-detection para Playwright (2026)"""

    # ========== USER AGENTS ROTATIVOS ==========
    USER_AGENTS = [
        # Chrome 125 (Windows)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
        # Chrome 125 (macOS)
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
        # Chrome 124 (Windows)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        # Firefox 126 (Windows)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/126.0",
        # Firefox 126 (macOS)
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:126.0) Gecko/20100101 Firefox/126.0",
        # Safari 17 (macOS)
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
        # Chrome 123 (Linux)
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        # Edge 125 (Windows)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
    ]

    # ========== PERFILES DE NAVEGADOR CONSISTENTES ==========
    BROWSER_PROFILES = [
        {
            "viewport": {"width": 1920, "height": 1080},
            "timezone": "America/New_York",
            "locale": "en-US",
            "platform": "Win32",
        },
        {
            "viewport": {"width": 1920, "height": 1080},
            "timezone": "Europe/Madrid",
            "locale": "es-ES",
            "platform": "Win32",
        },
        {
            "viewport": {"width": 1440, "height": 900},
            "timezone": "America/Los_Angeles",
            "locale": "en-US",
            "platform": "MacIntel",
        },
        {
            "viewport": {"width": 1440, "height": 900},
            "timezone": "Europe/London",
            "locale": "en-GB",
            "platform": "MacIntel",
        },
        {
            "viewport": {"width": 1366, "height": 768},
            "timezone": "Europe/Madrid",
            "locale": "es-ES",
            "platform": "Win32",
        },
        {
            "viewport": {"width": 1536, "height": 864},
            "timezone": "Europe/Paris",
            "locale": "fr-FR",
            "platform": "Win32",
        },
        {
            "viewport": {"width": 2560, "height": 1440},
            "timezone": "Europe/Berlin",
            "locale": "de-DE",
            "platform": "Win32",
        },
    ]

    # ========== COOKIES PERSISTENTES ==========
    COOKIE_DIR = Path.home() / ".audiovisual_scraper_cookies"
    COOKIE_FILE = COOKIE_DIR / "session_cookies.json"

    @classmethod
    def get_random_user_agent(cls) -> str:
        return random.choice(cls.USER_AGENTS)

    @classmethod
    def get_random_profile(cls) -> Dict[str, Any]:
        return random.choice(cls.BROWSER_PROFILES)

    @classmethod
    def get_consistent_profile(cls, seed: Optional[str] = None) -> Dict[str, Any]:
        """Genera perfil consistente basado en seed para misma sesión"""
        if seed:
            random.seed(seed)
            profile = random.choice(cls.BROWSER_PROFILES)
            random.seed()  # Reset
            return profile
        return cls.get_random_profile()

    @staticmethod
    async def apply_stealth(page: Page) -> None:
        """Aplica parches anti-detection completos (2026)"""
        await page.add_init_script("""
            // 1. Ocultar webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // 2. Ocultar chrome automation
            if (window.chrome) {
                Object.defineProperty(window.chrome, 'runtime', {
                    get: () => ({})
                });
            }

            // 3. Modificar plugins (lista realista Chrome)
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // 4. Modificar languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['es-ES', 'es', 'en-US', 'en']
            });

            // 5. Modificar permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );

            // 6. WebGL fingerprint normalizado
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Google Inc. (Intel Inc.) Intel Iris OpenGL Engine';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.apply(this, arguments);
            };

            // 7. Screen dimensions fix
            Object.defineProperty(screen, 'width', { get: () => window.screen.width });
            Object.defineProperty(screen, 'height', { get: () => window.screen.height });
            Object.defineProperty(screen, 'availWidth', { get: () => window.screen.availWidth });
            Object.defineProperty(screen, 'availHeight', { get: () => window.screen.availHeight });
        """)

    @staticmethod
    async def apply_stealth_sync(page: Page) -> None:
        """Alias para compatibilidad"""
        await AntiBotManager.apply_stealth(page)

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
            await asyncio.sleep(random.uniform(0.3, 1.0))

    @staticmethod
    async def scroll_to_element(page: Page, selector: str) -> None:
        """Scroll suave hasta elemento"""
        try:
            element = page.locator(selector).first
            await element.scroll_into_view_if_needed()
            await asyncio.sleep(random.uniform(0.2, 0.5))
        except Exception:
            pass

    @classmethod
    def save_cookies(cls, context: BrowserContext, domain: str) -> None:
        """Guarda cookies para dominio específico"""
        try:
            cls.COOKIE_DIR.mkdir(parents=True, exist_ok=True)
            cookies = context.cookies()

            # Cargar cookies existentes
            existing = {}
            if cls.COOKIE_FILE.exists():
                with open(cls.COOKIE_FILE, "r") as f:
                    existing = json.load(f)

            # Actualizar solo cookies del dominio
            domain_cookies = [c for c in cookies if domain in c["domain"]]
            if domain_cookies:
                existing[domain] = domain_cookies
                with open(cls.COOKIE_FILE, "w") as f:
                    json.dump(existing, f)
        except Exception as e:
            pass

    @classmethod
    def load_cookies(cls, domain: str) -> List[Dict[str, Any]]:
        """Carga cookies guardadas para dominio"""
        try:
            if cls.COOKIE_FILE.exists():
                with open(cls.COOKIE_FILE, "r") as f:
                    existing = json.load(f)
                    return existing.get(domain, [])
        except Exception:
            pass
        return []

    @classmethod
    async def apply_saved_cookies(cls, context: BrowserContext, domain: str) -> None:
        """Aplica cookies guardadas al contexto"""
        cookies = cls.load_cookies(domain)
        if cookies:
            await context.add_cookies(cookies)

    @staticmethod
    async def wait_for_cloudflare(page: Page, timeout: int = 30) -> bool:
        """Espera a que Cloudflare resuelva el challenge"""
        import time

        start = time.time()

        while time.time() - start < timeout:
            title = await page.title()

            # Detectar Cloudflare challenge
            if (
                "Just a moment" in title
                or "Attention Required" in title
                or "cf-" in title.lower()
            ):
                await asyncio.sleep(2)
                continue

            # Verificar que hay contenido real
            try:
                await page.wait_for_load_state("networkidle", timeout=5000)
                return True
            except Exception:
                pass

            await asyncio.sleep(1)

        return False

    @staticmethod
    async def handle_cloudflare_page(page: Page, url: str, timeout: int = 30) -> bool:
        """Navega a URL y espera Cloudflare"""
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            return await AntiBotManager.wait_for_cloudflare(page, timeout)
        except Exception:
            return False

    @staticmethod
    def is_blocked_page(page_content: str) -> bool:
        """Detecta si la página indica bloqueo"""
        blocked_patterns = [
            "403 Forbidden",
            "Access Denied",
            "blocked",
            "security check",
            "captcha",
            "unusual traffic",
            "rate limit",
        ]
        content_lower = page_content.lower()
        return any(pattern in content_lower for pattern in blocked_patterns)


class CloudflareSession:
    """Manejo de sesión con Cloudflare"""

    def __init__(self, domain: str):
        self.domain = domain
        self.cookie_file = (
            AntiBotManager.COOKIE_DIR / f"cf_{domain.replace('.', '_')}.json"
        )

    def save_cf_cookie(self, cf_clearance: str) -> None:
        """Guarda cookie cf_clearance"""
        try:
            self.cookie_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cookie_file, "w") as f:
                json.dump(
                    {
                        "cf_clearance": cf_clearance,
                        "timestamp": __import__("time").time(),
                    },
                    f,
                )
        except Exception:
            pass

    def get_cf_cookie(self) -> Optional[str]:
        """Obtiene cookie cf_clearance guardada (validez: 24h)"""
        try:
            import time

            if self.cookie_file.exists():
                with open(self.cookie_file, "r") as f:
                    data = json.load(f)
                    # 24 horas = 86400 segundos
                    if time.time() - data.get("timestamp", 0) < 86400:
                        return data.get("cf_clearance")
        except Exception:
            pass
        return None


# ========== INSTALACIÓN DE PAQUETES RECOMENDADOS ==========
STEALTH_PACKAGES = """
# Para mejor evasión, instala estos paquetes:
pip install playwright-stealth

# Y usa:
from playwright_stealth import stealth_sync
stealth_sync(page)
"""


# ========== CONFIGURACIÓN DE ARGUMENTS PARA CHROMIUM ==========
CHROMIUM_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-web-security",
    "--disable-features=IsolateOrigins,site-per-process",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-accelerated-2d-canvas",
    "--no-first-run",
    "--no-zygote",
    "--disable-gpu",
    "--window-size=1920,1080",
    "--disable-extensions",
    "--disable-background-networking",
    "--disable-default-apps",
    "--disable-sync",
    "--disable-translate",
    "--metrics-recording-only",
    "--mute-audio",
    "--no-default-browser-check",
    "--safebrowsing-disable-auto-update",
]

# Modo headless nuevo (Chrome 112+)
HEADLESS_NEW_ARGS = CHROMIUM_ARGS + ["--headless=new"]


# ========== BLOQUEO DE RECURSOS NO NECESARIOS ==========
BLOCKED_DOMAINS = [
    "google-analytics.com",
    "googletagmanager.com",
    "facebook.net",
    "doubleclick.net",
    "hotjar.com",
    "segment.io",
    "mixpanel.com",
    "sentry.io",
    "newrelic.com",
    "datadome.co",
    "crisp.chat",
]

BLOCKED_RESOURCE_TYPES = ["image", "font", "media", "websocket"]


def create_block_route():
    """Crea función de bloqueo de recursos"""

    def block_resources(route, request):
        url = request.url
        resource_type = request.resource_type

        # Bloquear dominios de tracking
        if any(domain in url for domain in BLOCKED_DOMAINS):
            route.abort()
            return

        # Bloquear recursos pesados
        if resource_type in BLOCKED_RESOURCE_TYPES:
            route.abort()
            return

        route.continue_()

    return block_resources
