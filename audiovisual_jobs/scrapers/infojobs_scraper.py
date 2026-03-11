"""
Módulo específico para InfoJobs con estrategias anti-bot avanzadas
"""

import asyncio
import json
import random
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode
import httpx
from bs4 import BeautifulSoup


class InfoJobsScraper:
    """Scraper especializado para InfoJobs con técnicas anti-detection"""

    BASE_URL = "https://www.infojobs.net"

    # Headers avanzados que imitan un navegador real
    HEADERS = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "max-age=0",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    }

    # URLs de búsqueda específicas
    SEARCH_URLS = [
        "https://www.infojobs.net/ofertas-trabajo/produccion-audiovisuales",
        "https://www.infojobs.net/ofertas-trabajo/audiovisual",
        "https://www.infojobs.net/ofertas-trabajo/edicion-video",
        "https://www.infojobs.net/ofertas-trabajo/realizador",
        "https://www.infojobs.net/ofertas-trabajo/camarografo",
        "https://www.infojobs.net/ofertas-trabajo/operador-camara",
        "https://www.infojobs.net/ofertas-trabajo/editor-video",
        "https://www.infojobs.net/ofertas-trabajo/postproduccion",
    ]

    async def scrape(self, db_client=None) -> List[Dict[str, Any]]:
        """Scrapea InfoJobs usando múltiples estrategias"""
        all_offers = []
        seen_urls = set()

        for url in self.SEARCH_URLS:
            try:
                offers = await self._scrape_with_requests(url)
                for offer in offers:
                    if offer["enlace_fuente"] not in seen_urls:
                        all_offers.append(offer)
                        seen_urls.add(offer["enlace_fuente"])

                # Delay humano entre búsquedas
                await asyncio.sleep(random.uniform(2, 4))
            except Exception as e:
                print(f"❌ Error en {url}: {e}")
                continue

        return all_offers

    async def _scrape_with_requests(self, url: str) -> List[Dict[str, Any]]:
        """Intenta scrapear usando requests con headers avanzados"""
        headers = self.HEADERS.copy()
        headers["User-Agent"] = self._get_random_ua()

        async with httpx.AsyncClient(
            headers=headers, follow_redirects=True, timeout=30.0
        ) as client:
            response = await client.get(url)

            if response.status_code == 200:
                return self._parse_html(response.text, url)
            else:
                print(f"⚠️  Status {response.status_code} en {url}")
                return []

    def _get_random_ua(self) -> str:
        """Retorna un User-Agent aleatorio"""
        uas = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        ]
        return random.choice(uas)

    def _parse_html(self, html: str, source_url: str) -> List[Dict[str, Any]]:
        """Parsea el HTML de InfoJobs"""
        soup = BeautifulSoup(html, "html.parser")
        offers = []

        # Selectores específicos para InfoJobs
        job_cards = soup.select(
            '.ij-OfferCard, .job-item, [data-testid="offer-card"], .offer-card'
        )

        for card in job_cards[:10]:  # Máximo 10 por página
            try:
                # Título
                title_elem = card.select_one(
                    ".ij-OfferCardTitle, .job-title, h2 a, .title"
                )
                title = title_elem.get_text(strip=True) if title_elem else ""

                # Link
                link_elem = card.select_one('a[href*="oferta"], a[href*="job"]')
                link = (
                    link_elem["href"]
                    if link_elem and link_elem.has_attr("href")
                    else ""
                )
                if link and not link.startswith("http"):
                    link = f"https://www.infojobs.net{link}"

                # Empresa
                company_elem = card.select_one(
                    ".ij-OfferCardCompany, .company-name, .employer"
                )
                company = company_elem.get_text(strip=True) if company_elem else ""

                # Ubicación
                location_elem = card.select_one(
                    ".ij-OfferCardLocation, .location, .city"
                )
                location = location_elem.get_text(strip=True) if location_elem else ""

                # Descripción
                desc_elem = card.select_one(
                    ".ij-OfferCardDescription, .description, .summary"
                )
                description = desc_elem.get_text(strip=True) if desc_elem else ""

                if title and link:
                    offers.append(
                        {
                            "titulo_puesto": title,
                            "empresa": company,
                            "ubicacion": location,
                            "descripcion": description or f"Oferta de {company}",
                            "enlace_fuente": link,
                            "tipo_fuente": "infojobs",
                            "source_domain": "infojobs.net",
                        }
                    )
            except Exception as e:
                continue

        return offers


# Función de conveniencia para integrar con el pipeline principal
async def scrape_infojobs(db_client=None) -> List[Dict[str, Any]]:
    """Función principal para scrapear InfoJobs"""
    scraper = InfoJobsScraper()
    return await scraper.scrape(db_client)
