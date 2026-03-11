# SOP: Análisis de Scraping y Optimización de Selectores

Este procedimiento operativo estándar define los pasos para analizar una web y extraer la información necesaria para construir un scraper robusto.

## 1. Fase de Análisis Visual

1. **Navegación**: Abrir la URL con el navegador (o mediante la herramienta de navegación del agente).
2. **Inspección de Estructura**:
   - Identificar el elemento "Contenedor de Oferta" (el que se repite por cada trabajo).
   - Identificar selectores para: Título, Empresa, Ubicación, Enlace, Fecha.
3. **Paginación**:
   - Observar si se usa paginación por parámetros (`?page=2`), botones de "Siguiente" o Scroll Infinito.
   - Guardar el patrón de URL de paginación o el selector del botón.

## 2. Fase de Análisis Técnico (Network)

1. **APIs Ocultas**: Monitorizar las peticiones de red (XHR/Fetch) al cargar la página o al navegar entre páginas. Buscar respuestas JSON que contengan la lista de trabajos.
2. **Feeds y Sitemaps**: Buscar en el código fuente o rutas comunes (`/feed/`, `/rss`, `/sitemap.xml`).
3. **Protecciones**: Detectar si aparece Cloudflare, peticiones bloqueadas (403), o CAPTCHAs.

## 3. Documentación del Hallazgo

Por cada portal, se debe rellenar la ficha detallada en `ANALISIS_WEBS.md` siguiendo el formato especificado en `GUIA_PARA_ANTIGRAVITY.md`.

## 4. Implementación en Código

1. **Selectores**: No hardcodear selectores en la lógica del scraper. Usar un archivo de configuración (`selectores_config.py`).
2. **Fallback**: Si el portal tiene API, priorizarla sobre el scraping de HTML.
3. **Manejo de Errores**: Implementar try-except por cada elemento extraído para evitar que un error en una oferta rompa todo el ciclo.

## 5. Restricciones y Aprendizajes (Memoria Viva)

- **Cloudflare**: Si se detecta Cloudflare, usar Playwright con sigilo o tiempos de espera aleatorios.
- **Indeed**: Extremadamente sensible. Requiere User-Agent real y rotación. *Nota*: Sus descripciones suelen contener el texto "descripción extraída automáticamente", nunca descartar ofertas basadas en esa frase explícita porque bloquearía todas las de Indeed válidas.
- **3Cat**: Al ser JSF, puede requerir esperar a que el DOM esté completamente cargado y manejar estados de sesión.
- **Filtros de Calidad y Roles**: No hacer validaciones hardcodeadas en Python. *Nota*: Nunca bloquear familias de palabras de forma estática en el código (ej. excluir "cocinero") porque rompe la configuración flexible que el usuario ingresa en `.env` (como `KEYWORDS_FILTRO`). Siempre leer dinámicamente de las variables de entorno.
- **Puntuaciones de Confianza Prematuras**: No descartar en la fase de validación en crudo si el "score_confianza" es 0. *Nota*: El score se calcula habitualmente *después*, por lo que evaluar eso al inicio provocaba el descarte del 100% de ofertas sin fecha explícita.
- **Títulos Cortos**: No establecer límites mínimos abusivos a los títulos (ej. rechazar si `< 10` caracteres). Roles reales y válidos como `Chef`, `Gaffer`, o `Cocinero` son muy cortos. Usar un mínimo de 4 letras.

## 6. Expansión de Fuentes - 2026-03-10

### InfoJobs API
- **Estado**: CERRADA. La página developer.infojobs.net dice "The registration of new apps is currently unavailable." No se puede conseguir cliente API. Ignorar completamente esta vía.
- **Alternativa**: playwright_stealth sobre `infojobs.net` (ya configurado). El HTML responde 200 OK.

### RSS/Feeds Confirmados (200 OK + Content-Type: text/xml)
- `castingenbarcelona.es` → `https://www.castingenbarcelona.es/feed/` ✅
- `solocastings.es` → `https://www.solocastings.es/rss/` ✅
- `artfy.es` (Sitemap) → `https://artfy.es/casting-sitemap1.xml` ✅
- `castingscinetv.com` → `https://www.castingscinetv.com/feeds/posts/default` ✅ **NUEVO**

### Portales Desactivados (Health Check 2026-03-10)
- `monster.es` → 403 Forbidden → `method: disabled`
- `jooble.org` → 403 Forbidden → `method: disabled`
- `milanuncios.com` → URL corregida a `/trabajo-en-barcelona/?q=audiovisual`

### Nuevos Portales Premium Añadidos
Fuente: `produccionaudiovisual.com` (authoritative del sector español):
- **Atresmedia** (`atresmediacorporacion.com`) - Antena3, LaSexta, Neox
- **Crew United** (`crew-united.com`) - Plataforma europea de profesionales
- **Filmin** (`filmin.es/blog/seccion/filminjobs`) - Ofertas internas
- **Grupo Secuoya** (`gruposecuoya.es`) - Productora TV nacional
- **Netflix España** (`jobs.netflix.com/locations/madrid-spain`)
- **The Dots** (`the-dots.com`) - Intermediaria creativa UK/Europa
- **Club de Creativos** (`clubdecreativos.com`) - Publicidad y audiovisual
- **Movistar/Telefónica AV** (`telefonicaserviciosaudiovisuales.com`)

## 7. Rediseño de Arquitectura de Fuentes - 2026-03-11

### Decisión: Castings de actores ELIMINADOS
- Los portales de casting (castingenbarcelona.es, solocastings.es, artfy.es, bcncasting.es) son relevantes para actores, no para técnicos audiovisuales.
- Estos portales han sido desactivados en `fuentes_catalogo` con `status='disabled'`.
- **Nota**: No añadir este tipo de fuentes en futuras expansiones.

### Nueva arquitectura: Múltiples URLs por portal (urls_busqueda)
- La configuración en `selectores_config.py` ahora soporta el campo `urls_busqueda: list[str]`.
- `web_scraper.py` (método `scrape()`) itera sobre cada URL de `urls_busqueda` en lugar de una sola URL por portal.
- Esto permite que LinkedIn con 6 queries específicas por rol genere 6x más ofertas relevantes.
- **Pausa de 4-8s entre URLs del mismo portal** para evitar rate-limiting.

### Portales añadidos con urls_busqueda (2026-03-11)
- **LinkedIn**: 6 URLs por rol (editor video, realizador TV, operador cámara, técnico sonido, postproducción, production coordinator). Parámetro `f_TPR=r604800` = última semana.
- **InfoJobs**: 5 categorías (cine-tv-video, editor-video, produccion-audiovisual, tecnico-sonido, operador-camara).
- **Computrabajo**: 3 URLs (editor-video, operador-camara, produccion-audiovisual).
- **Tecnoempleo**: Sección audiovisual específica.

### Limpieza de fuentes de BD (Supabase)
- 14 fuentes de hostelería/cocina marcadas como `disabled`. Entre ellas: `trovit/empleo-cocinero`, `glassdoor/ayudante-cocina`, `indeed/cocinero`, etc.
- Estas URLs contaminaban los resultados del email y el normalizer tenía que descartarlas.

### Workflow GitHub Actions actualizado
- **Antes**: `cron: '0 7 * * 1-5'` (solo L-V, 1x/día)
- **Ahora**: 4 crons diarios (5h, 10h, 15h, 19h UTC = 7h, 12h, 17h, 21h España), todos los días
- Eliminado el step de `Deploy to Cloudflare Pages` (el directorio `public/` ya no existe)
- Añadida variable de entorno `SUPABASE_SERVICE_KEY`
