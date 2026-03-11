import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from telethon import TelegramClient
from telethon.tl.types import Message

from scrapers.base import BaseScraper
from config.settings import settings


class TelegramScraper(BaseScraper):
    # Solo extraer mensajes de los últimos 30 días
    DIAS_MAX_ANTIGUEDAD = 30
    
    def __init__(self, canales: Optional[List[str]] = None):
        super().__init__()
        self.canales = [
            c.strip() for c in (canales or settings.TELEGRAM_CHANNELS) if c.strip()
        ]

    def _clean_channel(self, channel: str) -> str:
        return channel.strip().lstrip("@")

    def _es_mensaje_reciente(self, mensaje: Message) -> bool:
        """Verifica si el mensaje es reciente (dentro de los últimos DIAS_MAX_ANTIGUEDAD días)"""
        if not mensaje.date:
            return False
        fecha_mensaje = mensaje.date.date()
        fecha_limite = (datetime.now() - timedelta(days=self.DIAS_MAX_ANTIGUEDAD)).date()
        return fecha_mensaje >= fecha_limite

    def _mapear_mensaje(self, mensaje: Message, canal: str) -> Dict[str, Any]:
        texto = (mensaje.message or "").strip()
        lineas = [line.strip() for line in texto.split("\n") if line.strip()]
        titulo = lineas[0] if lineas else "Sin título"

        username = None
        try:
            username = getattr(mensaje.chat, "username", None)
        except Exception:
            username = None

        enlace = (
            f"https://t.me/{username}/{mensaje.id}"
            if username
            else f"https://t.me/{canal}/{mensaje.id}"
        )

        oferta = self.normalizar_oferta(
            {
                "titulo_puesto": titulo[:200],
                "descripcion": texto[:2500],
                "enlace_fuente": enlace,
                "tipo_fuente": "telegram",
                "fecha_publicacion": mensaje.date.date().isoformat()
                if mensaje.date
                else None,
            }
        )
        return oferta

    async def _extraer_de_canal(
        self, client: TelegramClient, canal_username: str
    ) -> List[Dict[str, Any]]:
        ofertas: List[Dict[str, Any]] = []
        canal = self._clean_channel(canal_username)
        try:
            entity = await client.get_entity(canal)
            self.logger.info("Extrayendo mensajes de @%s", canal)

            mensajes = await client.get_messages(entity, limit=50)
            self.logger.info("Obtenidos %s mensajes de @%s", len(mensajes), canal)

            for mensaje in mensajes:
                try:
                    # FILTRO: Solo procesar mensajes recientes
                    if not self._es_mensaje_reciente(mensaje):
                        continue
                    
                    text = (mensaje.message or "").strip()
                    if not text:
                        continue

                    if not self.filtrar_audiovisual(text):
                        continue

                    ofertas.append(self._mapear_mensaje(mensaje, canal))
                except Exception as e:
                    self.logger.warning("Error procesando mensaje en @%s: %s", canal, e)
                    continue

        except Exception as e:
            self.logger.warning("No se pudo leer @%s: %s", canal, e)

        return ofertas

    async def _scrape_async(self) -> List[Dict[str, Any]]:
        if not settings.TELEGRAM_API_ID or not settings.TELEGRAM_API_HASH:
            self.logger.warning("TELEGRAM_API_ID o TELEGRAM_API_HASH no configurados")
            return []

        if not self.canales:
            self.logger.warning("No hay canales Telegram configurados")
            return []

        session_file = Path("session_telegram.session")
        if not session_file.exists() and not settings.TELEGRAM_INTERACTIVE_LOGIN:
            self.logger.warning(
                "No existe sesión de Telegram (%s). Para evitar prompt interactivo se omite Telegram. "
                "Configura TELEGRAM_INTERACTIVE_LOGIN=true una vez para crear la sesión.",
                session_file,
            )
            return []

        api_id = int(settings.TELEGRAM_API_ID)
        client = TelegramClient("session_telegram", api_id, settings.TELEGRAM_API_HASH)

        try:
            await client.connect()
            autorizado = await client.is_user_authorized()

            if not autorizado:
                if not settings.TELEGRAM_INTERACTIVE_LOGIN:
                    self.logger.warning(
                        "Sesion Telegram no autorizada y TELEGRAM_INTERACTIVE_LOGIN=false. "
                        "Se omite Telegram en este run."
                    )
                    return []
                await client.start()

            self.logger.info("Cliente Telegram conectado")

            for canal in self.canales:
                ofertas_canal = await self._extraer_de_canal(client, canal)
                self.ofertas_extraidas.extend(ofertas_canal)
                self.logger.info(
                    "Extraídas %s ofertas de @%s", len(ofertas_canal), canal
                )

        except EOFError:
            self.logger.warning(
                "No se pudo iniciar Telegram por prompt interactivo (EOF). Se omite Telegram en este run."
            )
        except Exception as e:
            self.logger.warning("Error en scraping Telegram (no fatal): %s", e)
        finally:
            await client.disconnect()
            self.logger.info("Cliente Telegram cerrado")

        self.logger.info("Total ofertas Telegram: %s", len(self.ofertas_extraidas))
        return self.ofertas_extraidas

    def scrape(self) -> List[Dict[str, Any]]:
        return asyncio.run(self._scrape_async())


def ejecutar_telegram_scraper(
    canales: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    scraper = TelegramScraper(canales)
    return scraper.scrape()
