# GUÍA PARA ANTIGRAVITY - Optimización de Scrapers Audiovisual

## 📋 CONTEXTO DEL PROYECTO

Este es un sistema automatizado en Python para extraer ofertas de empleo del sector audiovisual en Cataluña (Barcelona, Girona, Lleida, Tarragona).

**Arquitectura actual:**
- Base de datos: Supabase (PostgreSQL)
- Scrapers: Playwright (Web, Facebook), Telethon (Telegram)
- Normalización: Limpieza de datos con detección de ubicaciones
- Discovery: Búsqueda en Google (SerpAPI/DuckDuckGo)

**Estado actual:**
- ✅ Conexión a Supabase funcionando
- ✅ Telegram API configurada
- ✅ Estructura de scrapers creada
- ❌ Selectores CSS no optimizados (usando selectores genéricos)
- ❌ No se ha analizado la estructura real de las webs

## 🎯 OBJETIVO PARA ANTIGRAVITY

**Navegar manualmente a cada una de las URLs listadas abajo, analizar su estructura HTML, y proporcionar:**

1. **Selectores CSS específicos** para extraer ofertas de cada portal
2. **Patrones de URLs** (pagination, detalle de ofertas)
3. **Mecanismos anti-bot** detectados (Cloudflare, CAPTCHA, rate limiting)
4. **APIs ocultas** o endpoints JSON que devuelvan datos directamente
5. **Feeds RSS o Atom** si existen
6. **Recomendaciones de delays y estrategias** para cada portal

## 🔗 URLs A ANALIZAR (Prioridad ALTA)

### Fuentes Institucionales (Más estables)
1. **Spain Audiovisual Hub**
   - URL: https://spainaudiovisualhub.digital.gob.es/ca/empleo
   - Notas: Portal gubernamental, probablemente estructura HTML tradicional

2. **APAC - Associació de Professionals de l'Audiovisual de Catalunya**
   - URL: https://apac.cat/es/bolsa-de-trabajo/
   - Notas: Asociación profesional, posiblemente WordPress

3. **3Cat - Espai Selecció (TV3)**
   - URL: https://seleccio.3cat.cat/seleccio/index.jsf
   - Notas: Usa JSF (Java Server Faces), probablemente muy dinámico

### Portales Especializados (Alta prioridad)
4. **Platino Empleo**
   - URL: https://www.platinoempleo.com/
   - Notas: Portal líder de cine/TV en España

5. **Casting en Barcelona**
   - URL: https://www.castingenbarcelona.es/
   - Notas: WordPress con castings diarios

6. **Artfy - Castings Barcelona**
   - URL: https://artfy.es/casting-barcelona/
   - Notas: Plataforma de castings, probablemente React/Vue

7. **SoloCastings Barcelona**
   - URL: https://www.solocastings.es/castings-en/barcelona/
   - Notas: Portal especializado en castings

8. **Actors Barcelona**
   - URL: https://www.actorsbarcelona.com/castings-en-barcelona
   - Notas: Castings filtrados para actores

### Portales Generales (Media prioridad)
9. **Domestika Jobs Barcelona**
   - URL: https://www.domestika.org/es/jobs/where/122-barcelona-espana
   - Notas: Comunidad creativa, ofertas de diseño/audiovisual

10. **Jobted - Audiovisual Barcelona**
    - URL: https://www.jobted.es/trabajo-audiovisual-en-barcelona
    - Notas: Agregador de ofertas

11. **Indeed Barcelona Audiovisual**
    - URL: https://es.indeed.com/q-sector-audiovisual-l-barcelona-provincia-empleos.html
    - Notas: Indeed con filtro, probablemente muy protegido

## 🔍 INSTRUCCIONES DE ANÁLISIS

Para CADA URL, por favor proporciona:

### 1. Información General
```yaml
Portal: "Nombre del portal"
URL: "https://..."
Tipo: "WordPress/React/Angular/HTML tradicional/SPA"
Protección anti-bot: "Ninguna/Cloudflare/CAPTCHA/Rate limiting"
Requiere login: "Sí/No"
```

### 2. Selectores CSS (inspeccionar elementos)
```yaml
Contenedor_oferta: "div.job-card / article.listing / etc"
Titulo: "h2.title / h3.job-title / etc"
Empresa: ".company-name / .employer / etc"
Ubicación: ".location / .city / etc"
Descripción: ".description / .summary / etc"
Enlace: "a.job-link / h2 a / etc"
Fecha_publicación: ".date / time / etc"
```

### 3. Estructura de URLs
```yaml
Patrón_listado: "/jobs/page/2 / ?page=2 / etc"
Patrón_detalle: "/job/12345 / /oferta/nombre-oferta / etc"
Total_paginas: "Número aproximado o 'infinito scroll'"
```

### 4. APIs o Endpoints (DevTools → Network)
```yaml
API_JSON: "https://.../api/jobs / graphql endpoint"
Feed_RSS: "https://.../feed/ / rss.xml"
Sitemap: "https://.../sitemap.xml"
```

### 5. Estrategia de Scraping Recomendada
```yaml
Método: "HTTP requests / Playwright / Selenium / API directa"
Delay_entre_peticiones: "2 segundos / 5 segundos"
User-Agent: "Recomendado"
Headers_adicionales: "Referer, Accept-Language, etc"
Manejo_paginación: "Clic en 'Siguiente' / Scroll infinito / Parámetro URL"
```

## 🛠️ ENTREGA ESPERADA

Por favor, crea un archivo `ANALISIS_WEBS.md` con el formato anterior para cada una de las 11 URLs, y luego actualiza los archivos del proyecto:

1. **`scrapers/web_scraper.py`**: Actualizar selectores CSS según tu análisis
2. **`scrapers/selectores_config.py`** (nuevo): Crear archivo con todos los selectores
3. **`README_ANALISIS.md`**: Documentar APIs descubiertas y endpoints útiles

## 🔐 CREDENCIALES Y ACCESO

### Supabase (Base de datos)
- URL: https://ciivmkypsodwaldorkaa.supabase.co
- Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNpaXZta3lwc29kd2FsZG9ya2FhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMyNDA5NDgsImV4cCI6MjA3ODgxNjk0OH0.JIhHM98CogZH2r1Js6f_ZUY4mnCtyX9YKcHUHxI86Yc

### Telegram API
- API ID: 38122893
- API Hash: bcad0530a079c2e1c22d7d5ff0001ac2

### Estructura de carpetas
```
audiovisual_jobs/
├── config/settings.py
├── db/connection.py
├── db/queries.py
├── scrapers/
│   ├── base.py
│   ├── web_scraper.py
│   ├── telegram_scraper.py
│   └── facebook_scraper.py
├── normalization/normalizer.py
├── discovery/discoverer.py
├── tests/
├── fuentes_database.py
└── main.py
```

## ⚠️ NOTAS IMPORTANTES

1. **No realices scraping masivo** durante el análisis, solo inspección visual
2. **Respeta los robots.txt** de cada sitio
3. **Identifica rate limits** para no ser bloqueado
4. **Busca alternativas legales**: RSS, APIs públicas, newsletters
5. **Algunos portales pueden tener términos de servicio** que prohíban scraping

## 📝 FORMATO DE SALIDA

Por favor, para cada portal analizado, proporciona la información en este formato exacto:

```markdown
## [Nombre del Portal]

**URL:** https://...

### Análisis General
- Tecnología: WordPress/React/Vanilla JS/etc
- Protección: Ninguna/Cloudflare/etc
- Requiere login: Sí/No

### Selectores CSS
```css
/* Contenedor de cada oferta */
.job-container: "selector aquí"

/* Título del puesto */
.titulo: "selector aquí"

/* Empresa */
.empresa: "selector aquí"

/* Ubicación */
.ubicacion: "selector aquí"

/* Descripción */
.descripcion: "selector aquí"

/* Enlace a la oferta */
.enlace: "selector aquí"

/* Fecha de publicación */
.fecha: "selector aquí"
```

### Paginación
- Tipo: Botón "Siguiente" / Scroll infinito / Numeración
- Selector botón siguiente: "..."
- Total páginas aprox: X

### APIs/Feeds Descubiertos
- API JSON: `URL si existe`
- RSS Feed: `URL si existe`
- Sitemap: `URL si existe`

### Estrategia Recomendada
- Método: Playwright / Requests / Selenium
- Delay: X segundos
- User-Agent: Recomendado
- Consideraciones especiales: ...

---
```

## ✅ CHECKLIST DE COMPLETADO

- [ ] Analizadas las 3 fuentes institucionales
- [ ] Analizadas las 5 fuentes especializadas de alta prioridad
- [ ] Analizadas las 3 fuentes generales
- [ ] Creado archivo `ANALISIS_WEBS.md` con toda la información
- [ ] Actualizado `scrapers/web_scraper.py` con selectores reales
- [ ] Creado `scrapers/selectores_config.py` con configuración
- [ ] Documentadas APIs/Feeds descubiertos en `README_ANALISIS.md`
- [ ] Probado al menos un scraper con los nuevos selectores

---

**Nota para Antigravity:** Este proyecto está en la carpeta:
`/Users/aitor/Documents/2. PROJECTES/AUTOMATIZACIONES/FEINA AUDIOVISUAL/audiovisual_jobs/`

El entorno virtual Python está en `venv/` y ya tiene todas las dependencias instaladas.

¡Gracias por tu ayuda!
