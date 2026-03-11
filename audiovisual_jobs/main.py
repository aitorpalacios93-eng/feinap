import logging
import sys
from pathlib import Path

from config.settings import settings
from db.connection import get_supabase_client, test_connection
from db.queries import (
    upsert_oferta_desde_dict,
    get_fuentes_activas_priorizadas,
    recalculate_fuentes_prioridad,
)
from scrapers.web_scraper import ejecutar_web_scraper
from scrapers.telegram_scraper import ejecutar_telegram_scraper
from scrapers.facebook_scraper import ejecutar_facebook_scraper
from scrapers.infojobs_api import InfoJobsAPIClient
from normalization.normalizer import normalizar_ofertas
from discovery.discoverer import buscar_nuevas_fuentes, Discoverer
import asyncio



def setup_logging():
    settings.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(settings.LOG_FILE),
            logging.StreamHandler(sys.stdout),
        ],
    )


def run_discovery(client, logger):
    logger.info("=" * 50)
    logger.info("FASE 1: Descubrimiento de nuevas fuentes")
    logger.info("=" * 50)

    try:
        discoverer = Discoverer()
        catalogadas = discoverer.sync_catalogo_base(client)
        logger.info("Catálogo base sincronizado: %s fuentes", catalogadas)

        fuentes_encontradas = buscar_nuevas_fuentes(client)
        logger.info(
            f"Descubrimiento completado: {fuentes_encontradas} fuentes guardadas"
        )
    except Exception as e:
        logger.error(f"Error en descubrimiento: {e}")


def run_scrapers(client, logger):
    logger.info("=" * 50)
    logger.info("FASE 2: Extracción de ofertas")
    logger.info("=" * 50)

    todas_ofertas = []

    logger.info("Ejecutando Web Scraper...")
    try:
        fuentes_prio = get_fuentes_activas_priorizadas(
            client,
            limit=settings.SOURCES_LIMIT,
            min_priority=settings.SOURCES_MIN_PRIORITY,
        )
        portales = [f.get("url") for f in fuentes_prio if f.get("url")]
        logger.info("Web Scraper usando %s fuentes priorizadas", len(portales))

        ofertas_web = ejecutar_web_scraper(portales=portales or None, db_client=client)
        logger.info(f"Web Scraper: {len(ofertas_web)} ofertas extraídas")
        todas_ofertas.extend(ofertas_web)
    except Exception as e:
        logger.error(f"Error en Web Scraper: {e}")

    logger.info("Ejecutando Telegram Scraper...")
    try:
        ofertas_telegram = ejecutar_telegram_scraper()
        logger.info(f"Telegram Scraper: {len(ofertas_telegram)} ofertas extraídas")
        todas_ofertas.extend(ofertas_telegram)
    except Exception as e:
        logger.error(f"Error en Telegram Scraper: {e}")

    logger.info("Ejecutando Facebook Scraper...")
    try:
        ofertas_facebook = ejecutar_facebook_scraper()
        logger.info(f"Facebook Scraper: {len(ofertas_facebook)} ofertas extraídas")
        todas_ofertas.extend(ofertas_facebook)
    except Exception as e:
        logger.error(f"Error en Facebook Scraper: {e}")

    # Fase 2d: InfoJobs API (si hay credenciales configuradas)
    logger.info("Ejecutando InfoJobs API (si hay credenciales)...")
    try:
        ij_client = InfoJobsAPIClient()
        if ij_client.client_id and ij_client.client_secret:
            consultas_ij = [
                {"q": "editor video audiovisual"},
                {"q": "operador camara video"},
                {"q": "produccion audiovisual"},
                {"q": "realizador television"},
                {"q": "tecnico sonido"},
            ]
            ofertas_ij = []
            for q in consultas_ij:
                parcial = asyncio.run(ij_client.search_offers(**q))
                ofertas_ij.extend(parcial)
                logger.info(f"  InfoJobs API '{q['q']}': {len(parcial)} ofertas")
            logger.info(f"InfoJobs API total: {len(ofertas_ij)} ofertas")
            todas_ofertas.extend(ofertas_ij)
        else:
            logger.info("InfoJobs API omitida — credenciales no configuradas (INFOJOBS_CLIENT_ID / INFOJOBS_CLIENT_SECRET)")
    except Exception as e:
        logger.error(f"Error en InfoJobs API: {e}")



    logger.info("=" * 50)
    logger.info("FASE 3: Normalización de datos")
    logger.info("=" * 50)

    try:
        ofertas_normalizadas = normalizar_ofertas(todas_ofertas)
        logger.info(f"Ofertas normalizadas: {len(ofertas_normalizadas)}")
    except Exception as e:
        logger.error(f"Error en normalización: {e}")
        return

    logger.info("=" * 50)
    logger.info("FASE 4: Guardado en Supabase")
    logger.info("=" * 50)

    guardadas = 0
    errores = 0

    for oferta in ofertas_normalizadas:
        try:
            upsert_oferta_desde_dict(client, oferta)
            guardadas += 1
        except Exception as e:
            logger.warning(
                f"Error guardando oferta {oferta.get('enlace_fuente', 'sin_url')}: {e}"
            )
            errores += 1

    logger.info("=" * 50)
    logger.info("RESUMEN FINAL")
    logger.info("=" * 50)
    logger.info(f"Ofertas extraídas: {len(todas_ofertas)}")
    logger.info(f"Ofertas normalizadas: {len(ofertas_normalizadas)}")
    logger.info(f"Ofertas guardadas: {guardadas}")
    logger.info(f"Errores al guardar: {errores}")

    try:
        recalculadas = recalculate_fuentes_prioridad(client)
        logger.info("Prioridades de fuentes recalculadas: %s", recalculadas)
    except Exception as e:
        logger.warning("No se pudo recalcular prioridad de fuentes: %s", e)

    logger.info("=" * 50)


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 50)
    logger.info("INICIO: Sistema de extracción de ofertas laborales audiovisuales")
    logger.info("=" * 50)

    try:
        settings.validate()
        logger.info("Configuración validada correctamente")
    except ValueError as e:
        logger.error(f"Error de configuración: {e}")
        sys.exit(1)

    logger.info("Conectando con Supabase...")
    try:
        client = get_supabase_client()
        test_connection(client)
        logger.info("Conexión a Supabase establecida")
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        sys.exit(1)

    run_discovery(client, logger)

    run_scrapers(client, logger)

    logger.info("=" * 50)
    logger.info("FASE 5: Procesando Alertas por Email")
    logger.info("=" * 50)
    try:
        from db.queries import get_ofertas_hoy
        from notifications.email_sender import enviar_email_ofertas
        
        ofertas_hoy = get_ofertas_hoy(client)
        # Filtrar ofertas por confianza y asegurar no saturar el email
        mejores_ofertas = [o for o in ofertas_hoy if o.get("score_confianza", 0) >= 0.3][:40]

        logger.info(f"Se encontraron {len(ofertas_hoy)} ofertas nuevas. Enviando al correo las {len(mejores_ofertas)} mejores del día.")
        enviar_email_ofertas(mejores_ofertas)
    except Exception as e:
        logger.error(f"Error procesando alertas por email: {e}")

    logger.info("Proceso completado exitosamente"
)



if __name__ == "__main__":
    main()
