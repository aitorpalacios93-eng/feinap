import asyncio
import logging
from scrapers.web_scraper import WebScraper

async def test_milanuncios():
    logging.basicConfig(level=logging.INFO)
    
    # URL de prueba específica de Milanuncios
    test_urls = [
        "https://www.milanuncios.com/ofertas-de-empleo-en-barcelona/audiovisual.htm",
        "https://www.milanuncios.com/ofertas-de-empleo-en-madrid/camara.htm"
    ]

    scraper = WebScraper(portales=test_urls)
    ofertas = await scraper.scrape()

    print(f"\nTotal ofertas extraídas de milanuncios: {len(ofertas)}")
    for o in ofertas:
        print(f"✔️ {o['titulo_puesto']} | {o['enlace_fuente']}")

if __name__ == "__main__":
    asyncio.run(test_milanuncios())
