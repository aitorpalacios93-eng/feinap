# Configuración de selectores para los scrapers de empleo audiovisual

SELECTORES_CONFIG = {
    "spainaudiovisualhub.digital.gob.es": {
        "container": ".card, .content-item",
        "title": ".card__content-subtitle-link span, .content-item__data--subtitle-link span",
        "link": ".card__content-subtitle-link, .content-item__data--subtitle-link",
        "description": ".card__content-description",
        "date": ".content-item__data--date",
        "method": "requests",
    },
    "apac.cat": {
        "container": ".atbd_single_listing",
        "title": ".atbd_listing_title h4 a",
        "link": ".atbd_listing_title h4 a",
        "company": ".atbd_listing_company",
        "location": ".atbd_location",
        "date": ".atbd_listing_meta span.la-calendar",
        "method": "playwright",
    },
    "seleccio.3cat.cat": {
        "container": ".row.bg-light.border-bottom",
        "title": "h3",
        "link": "a[id*=':titol']",
        "company": None,  # Estático "CCMA, SA"
        "date": None,  # Extraer de texto relativo
        "method": "playwright",
    },
    "www.castingenbarcelona.es": {
        "container": "article.post-item",
        "title": ".post-title a",
        "link": ".post-title a",
        "company": "a.url.fn.n",
        "date": "time.entry-date",
        "rss": "https://www.castingenbarcelona.es/feed/",
        "method": "requests",
    },
    "artfy.es": {
        "container": ".elementor-widget-container",
        "title": ".elementor-heading-title a",
        "link": "a[href*='/casting/']",
        "location": ".ts-action-con",
        "date": ".ts-action-con",
        "sitemap": "https://artfy.es/casting-sitemap1.xml",
        "method": "playwright",
    },
    "www.solocastings.es": {
        "container": "table.table-striped tr",
        "title": "td.txtlistados a[title]",
        "link": "td.txtlistados a",
        "company": "span.linea2",
        "date": "span.linea3",
        "rss": "https://www.solocastings.es/rss/",
        "method": "requests",
    },
    "www.actorsbarcelona.com": {
        "container": "div.css-o1zvx0",
        "title": "p.chakra-text:first-of-type",
        "link": "a[href*='bit.ly']",
        "method": "playwright",
    },
    "www.domestika.org": {
        "container": "li.job-item",
        "title": "a.job-title",
        "link": "a.job-title",
        "company": ".job-item__company",
        "location": ".job-item__city",
        "date": ".job-item__date",
        "method": "requests",
    },
    "www.jobted.es": {
        "container": ".res-item-info",
        "title": ".res-data-title",
        "link": "a.res-link-job",
        "company": ".res-data-company",
        "location": ".res-data-location",
        "date": ".res-data-date",
        "method": "requests",
    },
    "es.indeed.com": {
        "container": "div.job_seen_beacon",
        "title": "h2.jobTitle span[title]",
        "link": "h2.jobTitle a",
        "company": "span[data-testid='company-name']",
        "location": "div[data-testid='text-location']",
        "date": "span.date",
        "method": "playwright_stealth",
    },
    # =====================================================
    # NUEVAS FUENTES DESCUBIERTAS - PORTALES INTERNACIONALES
    # =====================================================
    "www.mandy.com": {
        "container": "div.job-card, article.job-listing, .job-item",
        "title": "h3.job-title, h2 a, .title",
        "link": "a[href*='/job/']",
        "company": ".company-name, .employer",
        "location": ".location, .city",
        "date": ".date-posted, .date",
        "method": "playwright_stealth",
        "notas": "ALTA PROTECCIÓN - 403 Forbidden detectado",
    },
    "www.encast.pro": {
        "container": "div.casting-item, article.casting, .offer-card",
        "title": "h3.casting-title, h2 a, .title",
        "link": "a[href*='/casting/']",
        "company": ".producer, .company-name",
        "location": ".location, .city",
        "date": ".date, .published-date",
        "method": "playwright",
        "notas": "Especializado en Europa - Barcelona/Cataluña frecuente",
    },
    "projectcasting.com": {
        "container": "div.casting-card, article.job, .listing-item",
        "title": "h3.casting-title, h2 a",
        "link": "a[href*='/casting/']",
        "company": ".company, .producer",
        "location": ".location",
        "date": ".date",
        "method": "playwright",
        "notas": "Filtrar por país España",
    },
    "www.backstage.com": {
        "container": "div.casting-item, article.offer, .job-listing",
        "title": "h3.casting-title, h2 a",
        "link": "a[href*='/casting/']",
        "company": ".company",
        "location": ".location",
        "date": ".date",
        "method": "playwright",
        "notas": "Internacional - Sección Barcelona",
    },
    "es.yatecasting.com": {
        "container": "div.casting-item, article.offer, .job-card",
        "title": "h3, h2, .casting-title",
        "link": "a",
        "company": ".agency, .company",
        "location": ".location",
        "date": ".date",
        "method": "playwright",
        "notas": "Agencia de castings",
    },
    # =====================================================
    # PRODUCTORAS Y CORPORACIONES
    # =====================================================
    "jobs.mediapro.tv": {
        "container": "tr.data-row",
        "title": "a.jobTitle-link",
        "link": "a.jobTitle-link",
        "company": "span.jobFacility",
        "location": "span.jobLocation",
        "date": "span.jobDate",
        "method": "playwright",
        "notas": "Portal corporativo VERIFICADO - Activo y funcionando",
    },
    "www.rtve.es": {
        "container": "div.oferta, article.job, .employment-item",
        "title": "h3, h2, .title",
        "link": "a",
        "company": "RTVE",
        "location": ".location, .place",
        "date": ".date, time",
        "method": "playwright",
        "notas": "Portal público - Filtrar sector audiovisual",
    },
    "convocatorias.rtve.es": {
        "container": "div.convocatoria, article.call, .selection-process",
        "title": "h3, h2, .title",
        "link": "a",
        "company": "RTVE",
        "location": ".location",
        "date": ".date, .deadline",
        "method": "playwright",
        "notas": "Procesos selectivos formales",
    },
    "bolsartvm.telemadrid.es": {
        "container": "div.job, article.offer, .employment-item",
        "title": "h3, h2, .title",
        "link": "a",
        "company": "Telemadrid",
        "location": "Madrid",
        "date": ".date",
        "method": "playwright",
        "notas": "Radio Televisión Madrid - Geográficamente limitado",
    },
    # =====================================================
    # PORTALES GENERALES ADICIONALES
    # =====================================================
    "empleo.trovit.es": {
        "container": "div.item, article.offer, .job-item",
        "title": "h3, h2, .title",
        "link": "a",
        "company": ".company",
        "location": ".location",
        "date": ".date",
        "method": "playwright",
        "notas": "Agregador - Protección media",
    },
    # INFOJOBS ORIGINAL ELIMINADO: Fuertemente bloqueado por Cloudflare en Playwright.
    # En su lugar, el sistema usa "infojobs_api.py" (si ClientID/Secret están en .env)
    # y los feeds RSS añadidos a FUENTES_RSS a continuación.
    "jobtoday.com": {
        "container": "div.job, article.offer, .job-card",
        "title": "h3, h2, .title",
        "link": "a",
        "company": ".company",
        "location": ".location",
        "date": ".date",
        "method": "playwright",
        "notas": "Mixto hostelería/audiovisual",
    },
    "www.cincactiva.es": {
        "container": "div.oferta, article.job, .listing-item",
        "title": "h3, h2, .title",
        "link": "a",
        "company": ".company",
        "location": ".location",
        "date": ".date",
        "method": "playwright",
    },
    "www.platinoempleo.com": {
        "container": "div.oferta, article.job, .listing-item",
        "title": "h2, h3, .job-title",
        "link": "a",
        "company": ".company, .employer",
        "location": ".location, .city",
        "date": ".date",
        "method": "playwright",
        "notas": "Puede requerir login para detalles",
    },
    # =====================================================
    # DIRECTORIOS PROFESIONALES (Networking)
    # =====================================================
    "www.bcncatfilmcommission.com": {
        "container": "div.professional, article.card, .directory-item",
        "title": "h3, h2, .name",
        "link": "a",
        "company": ".company",
        "location": ".location",
        "date": None,
        "description": ".specialty, .services",
        "method": "playwright",
        "notas": "Directorio - No ofertas directas, útil para networking",
    },
    "www.screenglobalproduction.com": {
        "container": "div.company, article.listing, .directory-item",
        "title": "h3, h2, .company-name",
        "link": "a",
        "company": ".company-name",
        "location": ".location",
        "date": None,
        "description": ".services, .description",
        "method": "playwright",
        "notas": "Directorio internacional",
    },
    # =====================================================
    # PORTALES GENERALISTAS (NUEVA EXPANSION MASIVA)
    # =====================================================
    "www.infoempleo.com": {
        "container": "article.offer-item, .ofertas li, .offer-item",
        "title": "h2 a, h3 a, .offer-title a",
        "link": "a",
        "company": ".empresa, .company",
        "location": ".ubicacion, .location",
        "date": ".fecha, .date",
        "method": "playwright",
    },
    # LinkedIn: Múltiples URL con términos audiovisuales específicos para España
    # La clave es usar las URLs de búsqueda pública (no login) con parámetros correctos
    "es.linkedin.com": {
        "container": "li.jobs-search-results__list-item, .base-card, [data-entity-urn]",
        "title": "h3.base-search-card__title, .job-card-list__title, a.base-card__full-link",
        "link": "a.base-card__full-link, a.job-card-list__title",
        "company": "h4.base-search-card__subtitle, .job-card-container__company-name",
        "location": ".job-search-card__location, .job-card-container__metadata-item",
        "date": "time",
        "method": "playwright_stealth",
        "wait_for": ".jobs-search__results-list, .base-card",
        "urls_busqueda": [
            "https://www.linkedin.com/jobs/search/?keywords=editor%20video%20audiovisual&location=España&f_TPR=r604800",
            "https://www.linkedin.com/jobs/search/?keywords=realizador%20TV%20produccion&location=España&f_TPR=r604800",
            "https://www.linkedin.com/jobs/search/?keywords=operador%20camara%20video&location=Barcelona&f_TPR=r604800",
            "https://www.linkedin.com/jobs/search/?keywords=tecnico%20sonido%20produccion&location=España&f_TPR=r604800",
            "https://www.linkedin.com/jobs/search/?keywords=postproduccion%20montaje%20premiere&location=España&f_TPR=r604800",
            "https://www.linkedin.com/jobs/search/?keywords=production%20coordinator%20media&location=Spain&f_TPR=r604800",
        ],
        "notas": "LinkedIn público sin login. f_TPR=r604800 = última semana. Múltiples búsquedas por rol.",
    },
    "es.jooble.org": {
        "container": "article, .vacancy-serp-item, .vacancy_wrapper",
        "title": "h2 a, .vacancy-title a, a.topCard",
        "link": "a",
        "company": ".vacancy-company-name, .company",
        "location": ".vacancy-location, .location",
        "date": ".vacancy-date, .date",
        "method": "playwright",
    },
    "es.talent.com": {
        "container": "article, .job, .job-card",
        "title": "h2 a, h3 a, .job-title a",
        "link": "a",
        "company": ".company, .company-name",
        "location": ".location, .job-location",
        "date": ".date, .job-date",
        "method": "playwright",
    },
    "www.jobisjob.es": {
        "container": "article, .offer, .job-item",
        "title": "h2 a, h3 a",
        "link": "a",
        "company": ".company, .empresa",
        "location": ".location, .ubicacion",
        "date": ".date, .fecha",
        "method": "playwright",
    },
    "www.glassdoor.es": {
        "container": "article, li[data-test='jobListing'], .react-job-listing",
        "title": "h3 a, a[data-test='job-title']",
        "link": "a",
        "company": ".EmployerProfile_compactEmployerName, .company",
        "location": ".JobCard_location, .location",
        "date": ".JobCard_listingAge, .date",
        "method": "playwright_stealth",
        "notas": "Proteccion alta",
    },
    "www.monster.es": {
        "container": "section.card-content, article, .summary",
        "title": "h2 a, .title a",
        "link": "a",
        "company": ".company, .name",
        "location": ".location",
        "date": ".meta time, .date",
        "method": "playwright",
    },
    "www.adecco.es": {
        "container": "article, .job-tile, .offer-card",
        "title": "h2 a, h3 a, .title a",
        "link": "a",
        "company": ".company, .brand",
        "location": ".location, .city",
        "date": ".date",
        "method": "playwright",
    },
    "www.randstad.es": {
        "container": "article, .vacancy, .job-offer",
        "title": "h2 a, h3 a",
        "link": "a",
        "company": ".company",
        "location": ".location",
        "date": ".date",
        "method": "playwright",
    },
    "www.manpower.es": {
        "container": "article, .job, .result-item",
        "title": "h2 a, h3 a",
        "link": "a",
        "company": ".company",
        "location": ".location",
        "date": ".date",
        "method": "playwright",
    },
    "www.hays.es": {
        "container": "article, .job-result, .listing-item",
        "title": "h2 a, h3 a",
        "link": "a",
        "company": ".company",
        "location": ".location",
        "date": ".date",
        "method": "playwright",
    },
    "www.michaelpage.es": {
        "container": "article, .job-listing, .view-content .views-row",
        "title": "h2 a, h3 a",
        "link": "a",
        "company": ".company",
        "location": ".location",
        "date": ".date",
        "method": "playwright",
    },
    "www.jobijoba.es": {
        "container": "article, .job-item, .offer-item",
        "title": "h2 a, h3 a",
        "link": "a",
        "company": ".company",
        "location": ".location",
        "date": ".date",
        "method": "playwright",
    },
    "www.milanuncios.com": {
        "container": 'article[data-testid="AD_CARD"]',
        "title": ".ma-AdCardListingV2-TitleLink",
        "link": ".ma-AdCardListingV2-TitleLink",
        "location": ".ma-AdLocation",
        "date": ".ma-AdCardV2-date",
        "wait_for": ".ma-AdCardListingV2-TitleLink[href]",
        "url_busqueda": "https://www.milanuncios.com/trabajo-en-barcelona/?q=audiovisual",
        "method": "playwright",
        "notas": "Next.js - hrefs se inyectan via JS. Usar wait_for. URL corregida: /trabajo-en-barcelona/?q=audiovisual",
    },
    "www.monster.es": {
        "notas": "DESACTIVADO - 403 Forbidden detectado en health check 2026-03-10",
        "method": "disabled",
        "container": None,
        "title": None,
        "link": None,
    },
    "es.jooble.org": {
        "notas": "DESACTIVADO - 403 Forbidden detectado en health check 2026-03-10",
        "method": "disabled",
        "container": None,
        "title": None,
        "link": None,
    },
    # =====================================================
    # RSS CONFIRMADOS (200 OK, Content-Type: text/xml)
    # =====================================================
    "InfoJobs RSS - Audiovisual": {
        "rss": "https://www.infojobs.net/trabajos.rss/q_audiovisual/",
        "method": "rss",
        "notas": "Feed directo XML que evade el bloqueo de Cloudflare",
    },
    "InfoJobs RSS - Editor Video": {
        "rss": "https://www.infojobs.net/trabajos.rss/q_editor-video/",
        "method": "rss",
    },
    "InfoJobs RSS - Operador Cámara": {
        "rss": "https://www.infojobs.net/trabajos.rss/q_operador-camara/",
        "method": "rss",
    },
    "www.castingscinetv.com": {
        "rss": "https://www.castingscinetv.com/feeds/posts/default",
        "container": "article, .post",
        "title": "h2 a, h1 a, .post-title a",
        "link": "a[href*='/castings']",
        "date": "time, .date",
        "method": "rss",
        "notas": "Blogger RSS - CONFIRMADO 200 XML. Castings Netflix, Madrid, Barcelona.",
    },
    # =====================================================
    # PORTALES PREMIUM PRODUCTOREAS / PLATAFORMAS
    # =====================================================
    "www.atresmediacorporacion.com": {
        "container": "div.job, article.offer, .oferta-item",
        "title": "h2, h3, .title",
        "link": "a",
        "company": "Atresmedia",
        "location": "Madrid",
        "date": ".date, time",
        "url_busqueda": "https://www.atresmediacorporacion.com/sobre-nosotros/envia-curriculum-empleo-recursos-humanos-atresmedia_201801255a69f0ac0cf2c163afc27a07.html",
        "method": "playwright",
        "notas": "Portal corporativo Atresmedia - Antena3, LaSexta, etc.",
    },
    "www.crew-united.com": {
        "container": "div.job-item, article, .crew-job",
        "title": "h2 a, h3 a, .job-title",
        "link": "a[href*='/jobs/']",
        "company": ".company, .employer",
        "location": ".location, .city",
        "date": ".date, time",
        "url_busqueda": "https://www.crew-united.com/es/jobs/?c=ES",
        "method": "playwright",
        "notas": "Plataforma europea profesionales audiovisual - filtrar por España",
    },
    "www.filmin.es": {
        "container": "div.job, article, .filminjob",
        "title": "h2 a, h3 a, .title",
        "link": "a",
        "company": "Filmin",
        "location": "Barcelona",
        "date": ".date, time",
        "url_busqueda": "https://www.filmin.es/blog/seccion/filminjobs",
        "method": "playwright",
        "notas": "Blog WordPress de Filmin - Ofertas laborales internas",
    },
    "gruposecuoya.es": {
        "container": "div.job, article.oferta, .vacancy",
        "title": "h2, h3, .title a",
        "link": "a",
        "company": "Grupo Secuoya",
        "location": ".location, .city",
        "date": ".date, time",
        "url_busqueda": "https://gruposecuoya.es/es/ofertas-de-empleo/",
        "method": "playwright",
        "notas": "Grupo Secuoya - productora TV nacional con base en Madrid",
    },
    "jobs.netflix.com": {
        "container": "li, div.role-item, .job-result",
        "title": "a, h2, .title",
        "link": "a[href*='/jobs/']",
        "company": "Netflix",
        "location": ".location, span",
        "date": None,
        "url_busqueda": "https://jobs.netflix.com/locations/madrid-spain",
        "method": "playwright",
        "notas": "Portal oficial Netflix España - Madrid. Muy dinámico (React).",
    },
    "the-dots.com": {
        "container": "div.job-card, article, .opportunity",
        "title": "h3 a, h2 a, .title a",
        "link": "a[href*='/jobs/']",
        "company": ".company, .employer",
        "location": ".location",
        "date": ".date, time",
        "url_busqueda": "https://the-dots.com/jobs/search?location=Spain",
        "method": "playwright_stealth",
        "notas": "Intermediaria creativa UK/Europa - requiere cuenta para ver detalles",
    },
    "www.clubdecreativos.com": {
        "container": "article, .job-item, .oferta",
        "title": "h2 a, h3 a",
        "link": "a",
        "company": ".company, .empresa",
        "location": ".location",
        "date": ".date, time",
        "url_busqueda": "https://www.clubdecreativos.com/empleo/",
        "method": "playwright",
        "notas": "Club de Creativos España - publicidad, diseño y audiovisual",
    },
    "www.telefonicaserviciosaudiovisuales.com": {
        "container": "div.job, article, .vacancy",
        "title": "h2, h3, .title",
        "link": "a",
        "company": "Movistar / Telefónica",
        "location": ".location",
        "date": ".date",
        "url_busqueda": "https://www.telefonicaserviciosaudiovisuales.com/trabaja-con-nosotros/",
        "method": "playwright",
        "notas": "Telefónica Servicios Audiovisuales - Movistar+",
    },
    "www.tablondeanuncios.com": {
        "container": "article, .anuncio, .item-list li",
        "title": "h2 a, h3 a",
        "link": "a",
        "company": ".company",
        "location": ".location",
        "date": ".fecha, .date",
        "method": "requests",
    },
    "www.trabajos.com": {
        "container": "article, .oferta, .job-item",
        "title": "h2 a, h3 a",
        "link": "a",
        "company": ".empresa, .company",
        "location": ".ubicacion, .location",
        "date": ".fecha, .date",
        "method": "playwright",
    },
    # =====================================================
    # PORTALES NUEVOS DE ALTO VALOR PROFESIONAL
    # =====================================================
    "www.tecnoempleo.com": {
        "container": "div.oferta, article.job-item, .oferta-empleo",
        "title": "h2.titulo a, h3 a, .oferta-title a",
        "link": "h2.titulo a, h3 a, .oferta-title a",
        "company": ".empresa, .empresa-nombre",
        "location": ".ubicacion, .lugar",
        "date": ".fecha, .date",
        "urls_busqueda": [
            "https://www.tecnoempleo.com/ofertas-trabajo/audiovisual/",
            "https://www.tecnoempleo.com/ofertas-trabajo/produccion-medios-comunicacion/",
            "https://www.tecnoempleo.com/ofertas-trabajo/edicion-video/",
        ],
        "method": "playwright",
        "notas": "Portal técnico España - Tiene sección audiovisual y medios de comunicación",
    },
    "www.computrabajo.es": {
        "container": "article.box_offer, .oferta-empleo, div[id*='offer']",
        "title": "h2.title a, h1 a, a.js-o-link",
        "link": "h2.title a, a.js-o-link",
        "company": "p.emp span.fnt_b, .company-name",
        "location": "ul.details-list li:first-child, .location",
        "date": "ul.details-list li.date, .date",
        "urls_busqueda": [
            "https://www.computrabajo.es/trabajo-de-editor-video",
            "https://www.computrabajo.es/trabajo-de-operador-camara",
            "https://www.computrabajo.es/trabajo-de-produccion-audiovisual",
            "https://www.computrabajo.es/trabajo-de-tecnico-sonido",
        ],
        "method": "playwright",
        "notas": "Portal masivo España. Muchas ofertas sectoriales. Selectores actualizados 2026.",
    },
    "www.infoempleo.com": {
        "container": "article.offer-item, li.listing-item",
        "title": "h2 a, h3 a, .offer-title a",
        "link": "h2 a, h3 a, .offer-title a",
        "company": ".empresa, .company",
        "location": ".ubicacion, .location",
        "date": ".fecha, .date",
        "urls_busqueda": [
            "https://www.infoempleo.com/ofertasdetrabajo/audiovisual/",
            "https://www.infoempleo.com/ofertasdetrabajo/editor-video/",
            "https://www.infoempleo.com/ofertasdetrabajo/produccion-cine-television/",
        ],
        "method": "playwright",
        "notas": "Portal generalista con buena categorización por sector",
    },
    "es.indeed.com": {
        "container": "div.job_seen_beacon, li.css-1ac2h1w",
        "title": "h2.jobTitle span[title], h2.jobTitle a span",
        "link": "h2.jobTitle a, a[data-jk]",
        "company": "span[data-testid='company-name']",
        "location": "div[data-testid='text-location']",
        "date": "span.date",
        "urls_busqueda": [
            "https://es.indeed.com/jobs?q=editor+video+audiovisual&l=Barcelona&fromage=7",
            "https://es.indeed.com/jobs?q=operador+camara+video&l=España&fromage=7",
            "https://es.indeed.com/jobs?q=realizador+TV+produccion&l=España&fromage=7",
            "https://es.indeed.com/jobs?q=tecnico+sonido+produccion&l=España&fromage=7",
            "https://es.indeed.com/jobs?q=montador+postproduccion+premiere&l=España&fromage=7",
            "https://es.indeed.com/jobs?q=production+coordinator+media&l=España&fromage=7",
        ],
        "method": "playwright_stealth",
        "notas": "Indeed España. fromage=7 = últimos 7 días. Multiple queries por rol.",
    },
}

# =====================================================
# CONFIGURACIÓN GLOBAL
# =====================================================

CONFIG_GLOBAL = {
    "delay_min": 2,
    "delay_max": 5,
    "timeout": 30000,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "max_reintentos": 3,
    "ofertas_por_portal": 30,  # Aumentado de 20 a 30
}

# Portales prioritarios (alta probabilidad de éxito, mayor retorno de ofertas)
PORTALES_PRIORITARIOS = [
    # Portales de alto volumen verificados
    "es.indeed.com",         # 162 ofertas/semana - MEJOR fuente
    "www.glassdoor.es",      # 112 ofertas/semana
    "es.linkedin.com",       # Muy potente - mejorar cobertura
    "es.talent.com",         # 12 ofertas/semana
    "www.computrabajo.es",   # NUEVO - alta cobertura España
    "www.tecnoempleo.com",   # NUEVO - perfil técnico audiovisual
    "www.infoempleo.com",    # NUEVO - buena categorización
    # Portales semi-técnicos con oferta audiovisual
    "www.jobted.es",         # 30 ofertas/semana - funciona bien
    "www.milanuncios.com",   # Ofertas locales Barcelona
    "www.tablondeanuncios.com",
    # Especializados audiovisual/digital
    "jobs.mediapro.tv",      # Portal corporativo Mediapro
    "www.crew-united.com",   # Plataforma europea profesionales AV
    "www.clubdecreativos.com",  # Club Creativos España
    "www.domestika.org",     # Comunidad creativa
    # Empresas audiovisuales específicas
    "www.atresmediacorporacion.com",  # Atresmedia (Antena3/LaSexta)
    "gruposecuoya.es",               # Grupo Secuoya TV
    "jobs.netflix.com",              # Netflix España
    "spainaudiovisualhub.digital.gob.es",  # Hub oficial sector audiovisual
    "apac.cat",                      # Asociación Productoras Catalunya
    "InfoJobs RSS - Audiovisual",    # Alta prioridad de descubrimiento RSS antibot
    # EXCLUIDOS (castings para actores - no relevantes):
    # www.castingenbarcelona.es, www.solocastings.es, artfy.es, es.yatecasting.com
    # www.encast.pro, projectcasting.com, www.backstage.com
]
