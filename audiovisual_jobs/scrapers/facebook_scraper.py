import asyncio
import json
import logging
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeout,
)

from scrapers.base import BaseScraper
from config.settings import settings


class FacebookScraper(BaseScraper):
    def __init__(self, grupos: Optional[List[str]] = None):
        super().__init__()
        self.grupos = grupos or settings.FACEBOOK_GROUPS
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    def _normalizar_url_grupo(self, grupo: str) -> str:
        value = (grupo or "").strip()
        if not value:
            return ""
        if value.startswith("http://") or value.startswith("https://"):
            return value

        slug = value.strip("/").replace("@", "")
        if "/groups/" in slug:
            return f"https://www.facebook.com/{slug}"

        slug = re.sub(r"[^a-zA-Z0-9._-]", "", slug)
        if not slug:
            return ""
        return f"https://www.facebook.com/groups/{slug}"

    async def _iniciar_navegador(self):
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=settings.HEADLESS
            )
            await self._cargar_cookies()
            self.logger.info("Navegador Facebook iniciado con cookies")
        except Exception as e:
            self.logger.error(f"Error al iniciar navegador: {e}")
            raise

    async def _cargar_cookies(self):
        cookies_value: str = (
            settings.FACEBOOK_COOKIES_PATH
            if settings.FACEBOOK_COOKIES_PATH
            else "./cookies/facebook.json"
        )
        cookies_path = Path(cookies_value)
        if self.browser is None:
            raise RuntimeError("Browser no inicializado")
        assert self.browser is not None
        if not cookies_path.exists():
            self.logger.warning(f"Archivo de cookies no encontrado: {cookies_path}")
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )
            return

        try:
            with open(cookies_path, "r") as f:
                cookies = json.load(f)
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                viewport={"width": 1280, "height": 720},
            )
            await self.context.add_cookies(cookies)
            self.logger.info("Cookies de Facebook cargadas")
        except Exception as e:
            self.logger.error(f"Error cargando cookies: {e}")
            self.context = await self.browser.new_context()

    async def _cerrar_navegador(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.logger.info("Navegador Facebook cerrado")

    async def _extraer_de_grupo(self, url: str) -> List[Dict[str, Any]]:
        ofertas = []
        page = None

        try:
            if not url.startswith("http"):
                self.logger.warning("URL de grupo inválida: %s", url)
                return []

            if self.context is None:
                self.logger.warning("Contexto de Facebook no inicializado")
                return []
            assert self.context is not None

            page = await self.context.new_page()
            self.logger.info(f"Navegando a {url}")

            await page.goto(
                url, timeout=settings.TIMEOUT, wait_until="domcontentloaded"
            )
            await asyncio.sleep(3)

            current_url = (page.url or "").lower()
            if "facebook.com/login" in current_url or "checkpoint" in current_url:
                self.logger.warning(
                    "Facebook parece no autenticado o bloqueado para %s (url actual: %s)",
                    url,
                    page.url,
                )
                return []

            try:
                body_text = (await page.inner_text("body")).lower()
            except Exception:
                body_text = ""

            join_hints = (
                "unirte al grupo",
                "join group",
                "solo los miembros pueden ver",
                "only members can see",
                "contenido no disponible",
                "this content isn't available",
            )
            if any(hint in body_text for hint in join_hints):
                self.logger.warning(
                    "No hay acceso visible al contenido del grupo %s (puede requerir unirse al grupo).",
                    url,
                )
                return []

            post_selectors = [
                "div[data-ad-comet-preview='message']",
                "div[data-ad-preview='message']",
                "div[role='article']",
                "div[aria-posinset]",
            ]
            posts = []
            selected_selector = ""
            for selector in post_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=7000)
                    posts = await page.query_selector_all(selector)
                    if posts:
                        selected_selector = selector
                        break
                except PlaywrightTimeout:
                    continue

            if not posts:
                self.logger.warning("No se encontraron posts visibles en %s", url)
                return []

            self.logger.info(f"Encontrados {len(posts)} posts en {url}")

            for post in posts[:20]:
                try:
                    texto = (await post.inner_text()).strip()

                    if not texto and selected_selector in {
                        "div[role='article']",
                        "div[aria-posinset]",
                    }:
                        nested = await post.query_selector(
                            "div[data-ad-comet-preview='message'], div[data-ad-preview='message']"
                        )
                        if nested:
                            texto = (await nested.inner_text()).strip()

                    if not texto or len(texto) < 50:
                        continue

                    if not self.filtrar_audiovisual(texto):
                        continue

                    titulo = texto.split("\n")[0][:200]

                    oferta = self.normalizar_oferta(
                        {
                            "titulo_puesto": titulo,
                            "descripcion": texto[:2000],
                            "enlace_fuente": url,
                        }
                    )
                    ofertas.append(oferta)

                except Exception as e:
                    self.logger.warning(f"Error extrayendo post: {e}")
                    continue

        except PlaywrightTimeout:
            self.logger.warning(f"Timeout cargando {url}")
        except Exception as e:
            self.logger.warning(f"Error extrayendo de {url}: {e}")
        finally:
            if page:
                await page.close()

        return ofertas

    async def scrape(self) -> List[Dict[str, Any]]:
        await self._iniciar_navegador()

        try:
            for grupo in self.grupos:
                if not grupo.strip():
                    continue
                try:
                    url_grupo = self._normalizar_url_grupo(grupo)
                    if not url_grupo:
                        self.logger.warning("Grupo Facebook inválido: %s", grupo)
                        continue

                    ofertas_grupo = await self._extraer_de_grupo(url_grupo)
                    self.ofertas_extraidas.extend(ofertas_grupo)
                    self.logger.info(
                        f"Extraídas {len(ofertas_grupo)} ofertas de {url_grupo}"
                    )
                except Exception as e:
                    self.logger.warning(f"Error en grupo {grupo}: {e}")
                    continue

        finally:
            await self._cerrar_navegador()

        self.logger.info(f"Total ofertas Facebook: {len(self.ofertas_extraidas)}")
        return self.ofertas_extraidas


def ejecutar_facebook_scraper(
    grupos: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Función de entrada síncrona"""
    return asyncio.run(FacebookScraper(grupos).scrape())
