# NUEVAS FUENTES DESCUBIERTAS - INVESTIGACIÓN COMPLEMENTARIA
# Fecha: 2025-02-17
# Método: Web search + Análisis de resultados

## 🎯 PORTALES INTERNACIONALES CON PRESENCIA EN ESPAÑA

PORTALES_INTERNACIONALES = [
    {
        "nombre": "The Mandy Network",
        "url": "https://www.mandy.com/",
        "url_jobs": "https://www.mandy.com/aa/jobs/",
        "tipo": "web",
        "cobertura": "Internacional (España incluida)",
        "descripcion": "Plataforma #1 para casting y crew. 2,551+ audiciones nuevas cada mes",
        "estimacion_ofertas_espana": "50-100 mensuales",
        "keywords": ["actors", "crew", "production", "casting"],
        "prioridad": "ALTA",
        "api_disponible": "Desconocida - Investigar",
        "feed_rss": "Desconocido - Investigar",
        "notas": "Muy popular en Europa. Probablemente tenga API o feed",
    },
    {
        "nombre": "enCAST.pro",
        "url": "https://encast.eu/",
        "url_castings_spain": "https://www.encast.pro/castings?cntry=ES",
        "tipo": "web",
        "cobertura": "Europa (España destacada)",
        "descripcion": "Casting calls en toda Europa. Especializado en Barcelona y Cataluña",
        "estimacion_ofertas_espana": "30-50 mensuales",
        "keywords": ["casting", "actors", "barcelona", "catalonia"],
        "prioridad": "ALTA",
        "api_disponible": "Desconocida",
        "feed_rss": "Desconocido",
        "notas": "Menciona específicamente Barcelona y Cataluña en castings",
    },
    {
        "nombre": "Project Casting",
        "url": "https://projectcasting.com/",
        "url_spain": "https://projectcasting.com/job?country=Spain",
        "tipo": "web",
        "cobertura": "Internacional",
        "descripcion": "Casting calls, audiciones y carreras en entretenimiento",
        "estimacion_ofertas_espana": "10-20 mensuales",
        "keywords": ["casting", "content creator", "modeling"],
        "prioridad": "MEDIA",
        "api_disponible": "Desconocida",
        "feed_rss": "Desconocido",
        "notas": "Filtra por país España",
    },
    {
        "nombre": "StagePool",
        "url": "https://www.stagepool.com/",
        "tipo": "web",
        "cobertura": "Europa",
        "descripcion": "Portal escandinavo con cobertura europea",
        "estimacion_ofertas_espana": "5-10 mensuales",
        "keywords": ["theatre", "musical", "performing arts"],
        "prioridad": "BAJA",
        "api_disponible": "No",
        "feed_rss": "No",
        "notas": "Menos relevante para audiovisual puro",
    },
]

## 🏢 PRODUCTORAS Y CORPORACIONES CON BOLSAS DE TRABAJO

PRODUCTORAS_BOLSAS = [
    {
        "nombre": "Mediapro - Bolsa de Trabajo",
        "url": "https://jobs.mediapro.tv/",
        "tipo": "web",
        "descripcion": "GRUP MEDIAPRO - Líder europeo en contenidos audiovisuales. 7,120 profesionales, 52 sedes",
        "estimacion_ofertas": "Continua (gran productora)",
        "keywords": ["producción", "TV", "derechos deportivos", " Barcelona"],
        "prioridad": "ALTA",
        "api_disponible": "No",
        "feed_rss": "Desconocido",
        "notas": "Portal propio de empleo. Gran volumen de producción en Barcelona",
    },
    {
        "nombre": "RTVE - Aquí hay trabajo",
        "url": "https://www.rtve.es/aqui-hay-trabajo/",
        "tipo": "web",
        "descripcion": "Portal oficial de empleo de RTVE (Radio Televisión Española)",
        "estimacion_ofertas": "5-10 mensuales",
        "keywords": ["televisión", "público", "nacional"],
        "prioridad": "ALTA",
        "api_disponible": "No",
        "feed_rss": "Posible",
        "notas": "Empleo público estable",
    },
    {
        "nombre": "RTVE - Convocatorias",
        "url": "https://convocatorias.rtve.es/",
        "tipo": "web",
        "descripcion": "Convocatorias específicas de RTVE",
        "estimacion_ofertas": "Variable (procesos selectivos)",
        "keywords": ["convocatoria", "proceso selectivo", "fijo"],
        "prioridad": "MEDIA",
        "api_disponible": "No",
        "feed_rss": "No",
        "notas": "Procesos formales de selección",
    },
    {
        "nombre": "Telemadrid - Empleo RTVM",
        "url": "https://bolsartvm.telemadrid.es/",
        "tipo": "web",
        "descripcion": "Bolsa de trabajo de Radio Televisión Madrid",
        "estimacion_ofertas": "2-5 mensuales",
        "keywords": ["madrid", "televisión", "público"],
        "prioridad": "BAJA (geográfico)",
        "api_disponible": "No",
        "feed_rss": "No",
        "notas": "Útil si el usuario busca también en Madrid",
    },
]

## 🔍 AGREGADORES Y BUSCADORES ESPECIALIZADOS

AGREGADORES = [
    {
        "nombre": "Trovit - Producción Audiovisual",
        "url": "https://empleo.trovit.es/empleo-produccion-audiovisual",
        "tipo": "web",
        "descripcion": "Agregador que muestra 781+ ofertas de producción audiovisual",
        "estimacion_ofertas": "Agregado de múltiples fuentes",
        "keywords": ["agregador", "múltiples fuentes"],
        "prioridad": "MEDIA",
        "api_disponible": "No",
        "feed_rss": "No",
        "notas": "Agrega de InfoJobs, Indeed, etc. Útil para descubrir fuentes",
    },
    {
        "nombre": "JobToday - Audiovisuales",
        "url": "https://jobtoday.com/es/trabajos-audiovisuales",
        "tipo": "web",
        "descripcion": "128+ empleos en audiovisuales en España",
        "estimacion_ofertas": "Mixto (hostelería + audiovisual)",
        "keywords": ["hostelería", "eventos", "audiovisual"],
        "prioridad": "BAJA",
        "api_disponible": "No",
        "feed_rss": "No",
        "notas": "Muchos trabajos de hostelería/eventos, menos producción pura",
    },
    {
        "nombre": "InfoJobs - Cine y Televisión",
        "url": "https://www.infojobs.net/ofertas-trabajo/cine-television",
        "tipo": "web",
        "descripcion": "Filtro específico de InfoJobs para cine y TV",
        "estimacion_ofertas": "20-30 mensuales",
        "keywords": ["infojobs", "cine", "televisión"],
        "prioridad": "MEDIA",
        "api_disponible": "No (protegido)",
        "feed_rss": "No",
        "notas": "Muy protegido contra scraping. Requiere técnicas avanzadas",
    },
]

## 📋 DIRECTORIOS Y RECURSOS PROFESIONALES

DIRECTORIOS = [
    {
        "nombre": "Barcelona Film Commission - Directorio Profesionales",
        "url": "https://www.bcncatfilmcommission.com/en/professionals-directory",
        "tipo": "web",
        "descripcion": "Directorio de profesionales catalanes del audiovisual registrados",
        "estimacion_ofertas": "Directorio (no ofertas directas)",
        "keywords": ["directorio", "profesionales", "cataluña"],
        "prioridad": "MEDIA",
        "api_disponible": "No",
        "feed_rss": "No",
        "notas": "Útil para networking y contacto directo con profesionales",
    },
    {
        "nombre": "Screen Global Production - Barcelona",
        "url": "https://www.screenglobalproduction.com/",
        "tipo": "web",
        "descripcion": "Directorio internacional de producción y crew en Barcelona",
        "estimacion_ofertas": "Directorio + posibles ofertas",
        "keywords": ["internacional", "crew", "producción"],
        "prioridad": "MEDIA",
        "api_disponible": "No",
        "feed_rss": "No",
        "notas": "Bueno para producciones internacionales",
    },
]

## 📊 RESUMEN DE NUEVAS FUENTES

ESTADISTICAS_NUEVAS = {
    "portales_internacionales": 4,
    "productoras_bolsas": 4,
    "agregadores": 3,
    "directorios": 2,
    "total_nuevas": 13,
    "prioridad_alta": 6,
    "prioridad_media": 5,
    "prioridad_baja": 2,
}

## 🎯 FUENTES PRIORITARIAS PARA IMPLEMENTAR

FUENTES_PRIORIDAD_IMPLEMENTACION = [
    # ALTA PRIORIDAD
    {
        "nombre": "The Mandy Network",
        "razon": "Mayor volumen de ofertas (2,551+/mes), internacional, España incluida",
        "dificultad_estimada": "Media",
        "url": "https://www.mandy.com/aa/jobs/",
    },
    {
        "nombre": "enCAST.pro",
        "razon": "Especializado en Europa, menciona Barcelona/Cataluña específicamente",
        "dificultad_estimada": "Media",
        "url": "https://www.encast.pro/castings?cntry=ES",
    },
    {
        "nombre": "Mediapro Jobs",
        "razon": "Productora líder en España, portal propio, ofertas reales y frecuentes",
        "dificultad_estimada": "Baja-Media",
        "url": "https://jobs.mediapro.tv/",
    },
    {
        "nombre": "RTVE Aquí hay trabajo",
        "razon": "Empleo público estable, televisión nacional",
        "dificultad_estimada": "Baja",
        "url": "https://www.rtve.es/aqui-hay-trabajo/",
    },
    # MEDIA PRIORIDAD
    {
        "nombre": "Project Casting",
        "razon": "Internacional, filtro por España disponible",
        "dificultad_estimada": "Media",
        "url": "https://projectcasting.com/job?country=Spain",
    },
    {
        "nombre": "Trovit Agregador",
        "razon": "Agrega 781+ ofertas, útil para descubrir fuentes primarias",
        "dificultad_estimada": "Alta (anti-scraping)",
        "url": "https://empleo.trovit.es/empleo-produccion-audiovisual",
    },
]

## 🔧 RECOMENDACIONES TÉCNICAS

RECOMENDACIONES_IMPLEMENTACION = [
    "1. Priorizar portales con FEEDS RSS/APIs antes que scraping HTML",
    "2. The Mandy Network y enCAST probablemente tienen APIs ocultas - Investigar con DevTools",
    "3. Mediapro y RTVE son portales corporativos estándar - Más fáciles de scrapear",
    "4. Trovit e InfoJobs tienen protección fuerte (Cloudflare) - Considerar alternativas",
    "5. Implementar rotación de proxies para portales internacionales",
    "6. Configurar delays aleatorios 2-5 segundos entre peticiones",
    "7. Verificar términos de servicio de cada portal antes de scraping intensivo",
]

## 📁 ARCHIVOS RELACIONADOS

# Este archivo complementa:
# - fuentes_database.py (fuentes originales descubiertas por NotebookLM)
# - scrapers/web_scraper.py (implementación actual)
# - scrapers/selectores_config.py (configuración de selectores)

# Total de fuentes identificadas hasta ahora: 38 (originales) + 13 (nuevas) = 51 fuentes
