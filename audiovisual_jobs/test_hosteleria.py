import asyncio
import logging
import json
from scrapers.web_scraper import WebScraper
from normalization.normalizer import normalizar_ofertas

async def test_hosteleria():
    logging.basicConfig(level=logging.DEBUG)
    
    # Test with some hotelry domains from the user's .env
    test_urls = [
        "https://www.indeed.com/q-cocinero-l-barcelona-empleos.html",
        "https://www.talent.com/jobs?q=cocinero&l=Barcelona",
        "https://www.infojobs.net/ofertas-trabajo/cocina-chef"
    ]
    
    scraper = WebScraper(portales=test_urls)
    ofertas_raw = await scraper.scrape()
    
    print(f"\n✅ Total ofertas extraídas (RAW): {len(ofertas_raw)}")
    
    if ofertas_raw:
        ofertas_norm = normalizar_ofertas(ofertas_raw)
        print(f"\n✅ Total ofertas normalizadas y aceptadas: {len(ofertas_norm)}")
        
        for o in ofertas_norm:
            print(f"- {o.get('titulo_puesto')} | {o.get('empresa')} | Rol: {o.get('rol_canonico')}")
    else:
        print("\n⚠️ No se han extraído ofertas. Los scrapers pueden estar bloqueados por antibots.")

if __name__ == "__main__":
    asyncio.run(test_hosteleria())
