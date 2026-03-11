# ANÁLISIS DE WEBS - PORTALES DE EMPLEO AUDIOVISUAL

Este documento contiene el análisis técnico de cada portal para optimizar el scraping.

---

## 1. Spain Audiovisual Hub

**URL:** https://spainaudiovisualhub.digital.gob.es/ca/empleo

### Análisis General
- Tecnología: Adobe Experience Manager (AEM)
- Protección: Ninguna detectada
- Requiere login: No

### Selectores CSS
```css
/* Contenedor de cada oferta (Directorio de Bolsas) */
.job-container: ".card"

/* Título del puesto / Portal */
.titulo: ".card__content-subtitle-link span"

/* Enlace a la oferta / portal */
.enlace: ".card__content-subtitle-link"

/* Descripción */
.descripcion: ".card__content-description"

/* Contenedor de cada oferta (Actualidad/Noticias) */
.noticia-container: ".content-item"

/* Título Noticia */
.titulo-noticia: ".content-item__data--subtitle-link span"

/* Fecha Noticia */
.fecha: ".content-item__data--date"
```

### Paginación
- Tipo: Estática / Filtros dinámicos en sección Actualidad
- Selector botón siguiente: N/A
- Total páginas aprox: 1

### APIs/Feeds Descubiertos
- API JSON: No detectada
- RSS Feed: No detectada
- Sitemap: `https://spainaudiovisualhub.mineco.gob.es/ca/sitemap.xml`

---

## 2. APAC - Associació de Professionals de l'Audiovisual de Catalunya

**URL:** https://apac.cat/es/bolsa-de-trabajo/

### Análisis General
- Tecnología: WordPress (Plugin Directorist)
- Protección: Google reCAPTCHA v3
- Requiere login: No para ver

### Selectores CSS
```css
.job-container: ".atbd_single_listing"
.titulo: ".atbd_listing_title h4 a"
.empresa: ".atbd_listing_company"
.ubicacion: ".atbd_location"
.enlace: ".atbd_listing_title h4 a"
.fecha: ".atbd_listing_meta span.la-calendar"
```

---

## 3. 3Cat - Espai Selecció (TV3)

**URL:** https://seleccio.3cat.cat/seleccio/index.jsf

### Análisis General
- Tecnología: JSF + PrimeFaces
- Requiere login: No para ver listado

### Selectores CSS
```css
.job-container: ".row.bg-light.border-bottom"
.titulo: "h3"
.enlace: "a[id*=':titol']"
```

---

## 4. Platino Empleo

**URL:** https://www.platinoempleo.com/

### Análisis General
- Tecnología: Asp.Net / Custom
- Requiere login: **Sí (No scrapable públicamente)**

---

## 5. Casting en Barcelona

**URL:** https://www.castingenbarcelona.es/

### Análisis General
- Tecnología: WordPress
- RSS Feed: `https://www.castingenbarcelona.es/feed/` (¡Prioridad!)

### Selectores CSS
```css
.job-container: "article.post-item"
.titulo: ".post-title a"
.empresa: "a.url.fn.n"
.fecha: "time.entry-date"
```

---

## 6. Artfy - Castings Barcelona

**URL:** https://artfy.es/casting-barcelona/

### Análisis General
- Tecnología: WordPress + Elementor
- Sitemap: `https://artfy.es/casting-sitemap1.xml` (¡Mejor fuente!)

### Selectores CSS
```css
.titulo: ".elementor-heading-title a"
.enlace: "a[href*='/casting/']"
.ubicacion: ".ts-action-con"
.fecha: ".ts-action-con"
```

---

## 7. SoloCastings Barcelona

**URL:** https://www.solocastings.es/castings-en/barcelona/

### Análisis General
- Tecnología: Custom PHP
- RSS Feed: `https://www.solocastings.es/rss/` (Muy estable)

### Selectores CSS
```css
.job-container: "table.table-striped tr"
.titulo: "td.txtlistados a[title]"
.empresa: "span.linea2"
.fecha: "span.linea3"
```

---

## 8. Actors Barcelona

**URL:** https://www.actorsbarcelona.com/castings-en-barcelona

### Análisis General
- Tecnología: React (Chakra UI)

### Selectores CSS
```css
.job-container: "div.css-o1zvx0"
.titulo: "p.chakra-text:first-of-type"
.enlace: "a[href*='bit.ly']"
```

---

## 9. Domestika Jobs Barcelona

**URL:** https://www.domestika.org/es/jobs/where/122-barcelona-espana

### Análisis General
- Tecnología: SSR (HTML estático)
- Protección: Cloudflare

### Selectores CSS
```css
.job-container: "li.job-item"
.titulo: "a.job-title"
.empresa: ".job-item__company"
.ubicacion: ".job-item__city"
.fecha: ".job-item__date"
.enlace: "a.job-title"
```

---

## 10. Jobted - Audiovisual Barcelona

**URL:** https://www.jobted.es/trabajo-audiovisual-en-barcelona

### Análisis General
- Tecnología: Agregador (SSR)
- Paginación: Parámetro `?p=2`

### Selectores CSS
```css
.job-container: ".res-item-info"
.titulo: ".res-data-title"
.empresa: ".res-data-company"
.ubicacion: ".res-data-location"
.fecha: ".res-data-date"
.enlace: "a.res-link-job"
```

---

## 11. Indeed Barcelona Audiovisual

**URL:** https://es.indeed.com/q-sector-audiovisual-l-barcelona-provincia-empleos.html

### Análisis General
- Tecnología: GraphQL / SSR (Dinámico)
- Protección: **Altísima (hCaptcha, DataDome, Cloudflare)**

### Selectores CSS
```css
.job-container: "div.job_seen_beacon"
.titulo: "h2.jobTitle span[title]"
.empresa: "span[data-testid='company-name']"
.ubicacion: "div[data-testid='text-location']"
.fecha: "span.date"
.enlace: "h2.jobTitle a"
```

### Estrategia Recomendada
- Método: Usar Playwright con **Stealth** y **Proxies Residenciales**. No intentar scraping vía requests.
