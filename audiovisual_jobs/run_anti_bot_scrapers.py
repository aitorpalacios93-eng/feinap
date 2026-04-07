"""
Ejecutor de scrapers para portales anti-bot
Ejecuta todos los scrapers y guarda resultados en Supabase
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import List, Dict, Any

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

from db.connection import get_supabase_client
from db.queries import upsert_oferta_desde_dict


# Importar scrapers
from scrapers.mandy_scraper import ejecutar_mandy_scraper
from scrapers.workana_scraper import ejecutar_workana_scraper
from scrapers.productionhub_scraper import ejecutar_productionhub_scraper
from scrapers.malt_scraper import ejecutar_malt_scraper
from scrapers.weremoto_scraper import ejecutar_weremoto_scraper
from scrapers.new_portals_scraper import (
    ejecutar_ola_creators_scraper,
    ejecutar_notodo_animacion_scraper,
    ejecutar_industria_animacion_scraper,
    ejecutar_crew_united_scraper,
    ejecutar_devuego_scraper,
    ejecutar_screenskills_scraper,
)
from scrapers.linkedin_scraper import ejecutar_linkedin_scraper
from scrapers.hard_portals_scraper import (
    ejecutar_infojobs_scraper,
    ejecutar_indeed_scraper,
)


def guardar_ofertas(client, ofertas: List[Dict[str, Any]], fuente: str) -> int:
    """Guarda ofertas en Supabase"""
    guardadas = 0
    for oferta in ofertas:
        try:
            oferta["tipo_fuente"] = fuente
            oferta["fecha_scraping"] = datetime.now().isoformat()
            upsert_oferta_desde_dict(client, oferta)
            guardadas += 1
        except Exception as e:
            logging.warning(f"Error guardando oferta de {fuente}: {e}")
    return guardadas


async def ejecutar_scraper_async(nombre: str, func, client, max_errors: int = 3) -> int:
    """Ejecuta un scraper con manejo de errores"""
    errores = 0
    ofertas = []

    while errores < max_errors:
        try:
            logging.info(f"🚀 Ejecutando {nombre}...")
            ofertas = func()
            logging.info(f"✅ {nombre}: {len(ofertas)} ofertas extraídas")
            break
        except Exception as e:
            logging.error(f"❌ {nombre} error (intento {errores + 1}): {e}")
            errores += 1
            asyncio.sleep(2**errores)

    if ofertas:
        return guardar_ofertas(client, ofertas, nombre)
    return 0


def ejecutar_todos_los_scrapers():
    """Ejecuta todos los scrapers y guarda en Supabase"""
    logging.info("=" * 60)
    logging.info("🚀 INICIANDO SCRAPER SUITE ANTI-BOT 2026")
    logging.info("=" * 60)

    # Conectar a Supabase
    client = get_supabase_client()
    if not client:
        logging.error("No se pudo conectar a Supabase")
        return

    total_guardadas = 0
    scrapers_ejecutados = []

    # Lista de scrapers a ejecutar
    scrapers = [
        ("Mandy", ejecutar_mandy_scraper),
        ("Workana", ejecutar_workana_scraper),
        ("ProductionHUB", ejecutar_productionhub_scraper),
        ("Malt", ejecutar_malt_scraper),
        ("WeRemoto", ejecutar_weremoto_scraper),
        ("OlaCreators", ejecutar_ola_creators_scraper),
        ("NotodoAnimacion", ejecutar_notodo_animacion_scraper),
        ("IndustriaAnimacion", ejecutar_industria_animacion_scraper),
        ("CrewUnited", ejecutar_crew_united_scraper),
        ("DeVuego", ejecutar_devuego_scraper),
        ("ScreenSkills", ejecutar_screenskills_scraper),
        # Estos pueden necesitar sesión manual
        # ("LinkedIn", ejecutar_linkedin_scraper),
        # ("InfoJobs", ejecutar_infojobs_scraper),
        # ("Indeed", ejecutar_indeed_scraper),
    ]

    for nombre, func in scrapers:
        try:
            logging.info(f"\n--- {nombre} ---")
            ofertas = func()
            if ofertas:
                guardadas = guardar_ofertas(client, ofertas, nombre)
                total_guardadas += guardadas
                scrapers_ejecutados.append((nombre, len(ofertas), guardadas))
            else:
                scrapers_ejecutados.append((nombre, 0, 0))
        except Exception as e:
            logging.error(f"Error en {nombre}: {e}")
            scrapers_ejecutados.append((nombre, 0, 0))

    # Resumen
    logging.info("\n" + "=" * 60)
    logging.info("📊 RESUMEN DE EJECUCIÓN")
    logging.info("=" * 60)
    for nombre, extraidas, guardadas in scrapers_ejecutados:
        logging.info(f"  {nombre}: {extraidas} extraídas, {guardadas} guardadas")
    logging.info(f"\n🎯 TOTAL GUARDADAS: {total_guardadas}")

    return total_guardadas


if __name__ == "__main__":
    ejecutar_todos_los_scrapers()
