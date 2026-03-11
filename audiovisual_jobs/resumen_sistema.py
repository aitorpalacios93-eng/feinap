#!/usr/bin/env python3
"""
Script de resumen del sistema de scraping de empleo audiovisual.
Muestra todas las fuentes configuradas y verifica la conectividad.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from scrapers.selectores_config import (
    SELECTORES_CONFIG,
    PORTALES_PRIORITARIOS,
    PORTALES_RSS,
    PORTALES_AVANZADOS,
)
from config.settings import settings


def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_section(title, items, emoji="📌"):
    print(f"\n{emoji} {title}:")
    for i, item in enumerate(items, 1):
        print(f"   {i}. {item}")


def main():
    print_header("SISTEMA DE SCRAPING DE EMPLEO AUDIOVISUAL - CATALUÑA")

    # Contar fuentes
    total_web = len(SELECTORES_CONFIG)
    total_rss = len(PORTALES_RSS)
    total_avanzados = len(PORTALES_AVANZADOS)
    total_prioritarios = len(PORTALES_PRIORITARIOS)

    print("\n📊 ESTADÍSTICAS:")
    print(f"   • Total portales web configurados: {total_web}")
    print(f"   • Portales con RSS/Feeds: {total_rss}")
    print(f"   • Portales prioritarios: {total_prioritarios}")
    print(f"   • Portales avanzados (requieren técnicas especiales): {total_avanzados}")
    print(
        f"   • TOTAL DE FUENTES: {total_web + len(settings.TELEGRAM_CHANNELS) + len(settings.FACEBOOK_GROUPS)}"
    )

    # Mostrar portales prioritarios
    print_section("PORTALES WEB PRIORITARIOS", PORTALES_PRIORITARIOS, "🌟")

    # Mostrar portales con RSS
    print_section("PORTALES CON RSS (Más rápidos)", PORTALES_RSS, "⚡")

    # Mostrar portales avanzados
    print_section(
        "PORTALES AVANZADOS (Requieren técnicas especiales)", PORTALES_AVANZADOS, "🔒"
    )

    # Mostrar canales de Telegram
    print_section("CANALES DE TELEGRAM", settings.TELEGRAM_CHANNELS, "📱")

    # Mostrar grupos de Facebook
    print_section("GRUPOS DE FACEBOOK", settings.FACEBOOK_GROUPS, "👥")

    # Mostrar configuración
    print_header("CONFIGURACIÓN ACTUAL")
    print(f"\n🔧 Parámetros:")
    print(f"   • Modo headless: {settings.HEADLESS}")
    print(f"   • Timeout: {settings.TIMEOUT}ms")
    print(f"   • Delay entre peticiones: {settings.DELAY_MIN}-{settings.DELAY_MAX}s")
    print(f"   • Máximo reintentos: {settings.MAX_REINTENTOS}")
    print(f"   • Ofertas por portal: {settings.OFERTAS_POR_PORTAL}")
    print(f"   • Roles objetivo: {', '.join([r for r in settings.TARGET_ROLES if r])}")
    print(f"   • Score mínimo de rol: {settings.MIN_ROLE_SCORE}")
    print(f"   • Remoto solo ES: {settings.INCLUDE_REMOTE_ES_ONLY}")
    print(f"   • Excluir LATAM: {settings.EXCLUDE_LATAM}")
    print(f"   • Límite de fuentes por ejecución: {settings.SOURCES_LIMIT}")
    print(f"   • Prioridad mínima de fuente: {settings.SOURCES_MIN_PRIORITY}")

    # Verificar conexión Supabase
    print_header("VERIFICACIÓN DE CONEXIONES")
    try:
        from db.connection import get_supabase_client, test_connection

        client = get_supabase_client()
        if test_connection(client):
            print("\n✅ Supabase: Conectado correctamente")
        else:
            print("\n❌ Supabase: Error de conexión")
    except Exception as e:
        print(f"\n❌ Supabase: {e}")

    # Verificar Telegram
    if settings.TELEGRAM_API_ID and settings.TELEGRAM_API_HASH:
        print("✅ Telegram API: Configurada")
    else:
        print("⚠️  Telegram API: No configurada completamente")

    print_header("COMANDOS DISPONIBLES")
    print("""
   Para ejecutar el sistema:
   
   1. Dry Run (modo prueba, no guarda en BD):
      python dry_run.py
   
   2. Ejecución completa (guarda en Supabase):
      python main.py
   
   3. Test de conexión:
      python tests/test_connection.py
   
   4. Test de normalizador:
      python tests/test_normalizer.py
   
   5. Ver este resumen:
      python resumen_sistema.py

   6. Dashboard de KPIs (Plan Maestro):
      python dashboard_kpis.py
    """)

    print_header("LISTO PARA USAR 🚀")
    print("\nEl sistema está configurado con 30+ fuentes de empleo audiovisual.")
    print("Ejecuta 'python dry_run.py' para probar sin guardar en la base de datos.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
