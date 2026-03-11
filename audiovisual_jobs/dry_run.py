import logging
import sys
import json
from pathlib import Path

TEST_MODE = True

from config.settings import settings
from db.connection import get_supabase_client, test_connection
from scrapers.web_scraper import ejecutar_web_scraper
from scrapers.telegram_scraper import ejecutar_telegram_scraper
from scrapers.facebook_scraper import ejecutar_facebook_scraper
from normalization.normalizer import normalizar_ofertas


OUTPUT_FILE = Path(__file__).parent / "test_output.json"


def setup_logging():
    OUTPUT_DIR = Path(__file__).parent / "logs"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(OUTPUT_DIR / "dry_run.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def run_web_scraper_test(logger):
    logger.info("=" * 50)
    logger.info("TEST: Web Scraper")
    logger.info("=" * 50)
    try:
        ofertas = ejecutar_web_scraper()
        logger.info(f"Web Scraper: {len(ofertas)} ofertas extraídas")
        return ofertas
    except Exception as e:
        logger.error(f"Error en Web Scraper: {e}")
        return []


def run_telegram_scraper_test(logger):
    logger.info("=" * 50)
    logger.info("TEST: Telegram Scraper")
    logger.info("=" * 50)
    try:
        ofertas = ejecutar_telegram_scraper()
        logger.info(f"Telegram Scraper: {len(ofertas)} ofertas extraídas")
        return ofertas
    except Exception as e:
        logger.error(f"Error en Telegram Scraper: {e}")
        return []


def run_facebook_scraper_test(logger):
    logger.info("=" * 50)
    logger.info("TEST: Facebook Scraper")
    logger.info("=" * 50)
    try:
        ofertas = ejecutar_facebook_scraper()
        logger.info(f"Facebook Scraper: {len(ofertas)} ofertas extraídas")
        return ofertas
    except Exception as e:
        logger.error(f"Error en Facebook Scraper: {e}")
        return []


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    print("=" * 50)
    print("DRY RUN - MODO PRUEBA")
    print(f"TEST_MODE: {TEST_MODE}")
    print("=" * 50)

    if not TEST_MODE:
        logger.warning("TEST_MODE es False. Saliendo.")
        print("\n⚠️  TEST_MODE = False. Actívalo para ejecutar.")
        sys.exit(1)

    logger.info("Iniciando Dry Run en modo TEST")

    todas_ofertas = []

    logger.info("\n---Selecciona qué scraper probar---")
    logger.info("Comenta/descomenta en el código para elegir")

    try:
        ofertas_web = run_web_scraper_test(logger)
        todas_ofertas.extend(ofertas_web)
    except Exception as e:
        logger.error(f"Error: {e}")

    try:
        ofertas_telegram = run_telegram_scraper_test(logger)
        todas_ofertas.extend(ofertas_telegram)
    except Exception as e:
        logger.error(f"Error: {e}")

    try:
        ofertas_facebook = run_facebook_scraper_test(logger)
        todas_ofertas.extend(ofertas_facebook)
    except Exception as e:
        logger.error(f"Error: {e}")

    logger.info("=" * 50)
    logger.info("FASE: Normalización")
    logger.info("=" * 50)

    try:
        ofertas_normalizadas = normalizar_ofertas(todas_ofertas)
        logger.info(f"Ofertas normalizadas: {len(ofertas_normalizadas)}")
    except Exception as e:
        logger.error(f"Error en normalización: {e}")
        return

    if TEST_MODE:
        logger.info(f"Guardando en archivo JSON: {OUTPUT_FILE}")
        try:
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(ofertas_normalizadas, f, ensure_ascii=False, indent=4)
            logger.info(
                f"✅ Guardadas {len(ofertas_normalizadas)} ofertas en {OUTPUT_FILE}"
            )
            print(f"\n✅ Output guardado en: {OUTPUT_FILE}")
        except Exception as e:
            logger.error(f"Error guardando JSON: {e}")
    else:
        logger.info("Guardando en Supabase (no implementado en dry_run)")

    logger.info("=" * 50)
    logger.info("RESUMEN")
    logger.info("=" * 50)
    logger.info(f"Total extraídas: {len(todas_ofertas)}")
    logger.info(f"Total normalizadas: {len(ofertas_normalizadas)}")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
