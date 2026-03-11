import asyncio
import logging
import json
from scrapers.web_scraper import WebScraper


async def test_portals():
    logging.basicConfig(level=logging.INFO)

    # Test with the newly configured major portals
    test_urls = [
        "https://www.infojobs.net/ofertas-trabajo/cine-television-video",
        "https://www.linkedin.com/jobs/search/?keywords=editor%20video%20audiovisual&location=Espa%C3%B1a&f_TPR=r604800",
        "https://www.computrabajo.es/trabajo-de-operador-camara",
        "https://www.tecnoempleo.com/ofertas-trabajo/audiovisual/"
    ]

    scraper = WebScraper(portales=test_urls)
    ofertas = await scraper.scrape()

    print(f"\nTotal ofertas extraídas: {len(ofertas)}")
    for o in ofertas:
        print(f"- {o.get('titulo_puesto', '')} | {o.get('empresa', '')} | {o.get('ubicacion', '')}")

    with open("test_results_targeted.json", "w", encoding="utf-8") as f:
        json.dump(ofertas, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    asyncio.run(test_portals())
