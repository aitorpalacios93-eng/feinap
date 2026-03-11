# README ANÁLISIS - APIs y Feeds Descubiertos

Este documento resume los endpoints y recursos directos (RSS/APIs) encontrados durante el análisis para evitar el scraping de HTML cuando sea posible.

## 📡 Feeds RSS (Prioridad de uso: ALTA)

| Portal | URL del Feed | Notas |
| :--- | :--- | :--- |
| **Casting en Barcelona** | `https://www.castingenbarcelona.es/feed/` | Muy estable, WordPress estándar. |
| **SoloCastings** | `https://www.solocastings.es/rss/` | Formato XML limpio. |
| **APAC** | N/A | Actualmente desactivados. |

## 🗺️ Sitemaps Estratégicos

| Portal | URL del Sitemap | Utilidad |
| :--- | :--- | :--- |
| **Artfy** | `https://artfy.es/casting-sitemap1.xml` | Contiene TODAS las ofertas individuales. Ideal para evitar la landing. |
| **Spain AV Hub** | `https://spainaudiovisualhub.digital.gob.es/ca/sitemap.xml` | Descubrimiento de nuevas páginas institucionales. |

## 🧩 APIs e Intercepciones Técnicas

### 3Cat (TV3)
- **Tipo:** JSF AJAX
- **Endpoint:** `/seleccio/processos.jsf` (vía POST)
- **Dato clave:** Requiere capturar el `javax.faces.ViewState`.

### Indeed
- **Tipo:** GraphQL / RPC
- **Endpoint:** `https://es.indeed.com/rpc/jobsearch/`
- **Riesgo:** Requiere tokens de sesión dinámicos y cookies de Cloudflare. No recomendado para uso directo sin navegador.

### Artfy / APAC
- **Tipo:** WP-JSON
- **Endpoint:** `/wp-json/wp/v2/posts`
- **Nota:** Pueden estar limitados por el plugin de directorio.

## 🛡️ Protecciones Detectadas

- **Cloudflare:** Indeed, Domestika, Artfy (estándar).
- **reCAPTCHA v3:** APAC (Detección de comportamiento).
- **Didomi (Cookies):** 3Cat, Jobted.
- **Popups:** Actors Barcelona (Suscripción).
