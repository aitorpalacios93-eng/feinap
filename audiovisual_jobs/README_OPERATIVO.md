# Como Funciona El Pipeline (Plan Maestro)

## 1) Flujo de extremo a extremo

Cada ejecucion de `main.py` hace esto, en orden:

1. **Conexion y validacion**
   - Carga `.env`
   - Conecta a Supabase

2. **Discovery + Source Registry**
   - Sincroniza fuentes base en `fuentes_catalogo`
   - Ejecuta busqueda de nuevas URLs (SerpAPI o DuckDuckGo)
   - Guarda nuevas fuentes en `fuentes_por_revisar` y `fuentes_catalogo`

3. **Seleccion de fuentes prioritarias**
   - Lee `fuentes_catalogo`
   - Ordena por `priority_score`
   - Descarta temporalmente fuentes en backoff (`next_retry_at`)

4. **Scraping**
   - Web scraper por fuente (RSS/API/Playwright)
   - Reintentos por portal (`MAX_REINTENTOS`)
   - Registro de salud en `fuentes_health` (latencia, items, estado)
   - Telegram/Facebook (si credenciales/cookies disponibles)

5. **Normalizacion e inteligencia**
   - Limpieza de texto
   - Dedupe por URL y titulo+empresa
   - Clasificacion de rol (`rol_canonico`, `subrol`, `score_confianza`)
   - Geofiltro:
     - **Si** remoto en espanol/espanol-like/es dominio `.es` -> se permite
     - **Si** LATAM detectado -> se excluye

6. **Carga en DB (ETL)**
   - Upsert en `ofertas_empleo` con campos enriquecidos
   - Recalculo de prioridad de fuentes al final


## 2) Tablas principales

- `ofertas_empleo`: ofertas finales (ya filtradas y clasificadas)
- `fuentes_catalogo`: inventario de fuentes con score y estado
- `fuentes_health`: historico de ejecucion por fuente
- `fuentes_por_revisar`: URLs descubiertas para analisis


## 3) Que campos nuevos te importan

En `ofertas_empleo`:
- `rol_canonico`
- `subrol`
- `score_confianza`
- `modalidad` (`presencial`, `remoto`, `hibrido`)
- `pais`
- `source_domain`
- `hash_fingerprint`
- `remoto_espana`
- `es_latam`


## 4) Comandos operativos

```bash
cd "/Users/aitor/Documents/2. PROJECTES/AUTOMATIZACIONES/FEINA AUDIOVISUAL/audiovisual_jobs"
. venv/bin/activate

# Ver configuracion actual
python resumen_sistema.py

# Ejecutar pipeline completo (guarda en Supabase)
python main.py

# Dashboard de KPIs
python dashboard_kpis.py

# Estado rapido (auto mode + ultimo resumen + rutas de dashboard/csv)
python scripts/review_status.py

# Modo prueba sin escribir en DB
python dry_run.py
```

### Activacion de conectores (Telegram/Facebook)

```bash
cd "/Users/aitor/Documents/2. PROJECTES/AUTOMATIZACIONES/FEINA AUDIOVISUAL/audiovisual_jobs"
. venv/bin/activate

# Estado rapido de conectores
python scripts/check_connectors_status.py

# 1) Crear/autorizar sesion de Telegram (QR + fallback telefono)
python scripts/setup_telegram_session.py

# 2) Crear cookies de Facebook abriendo navegador manual
python scripts/setup_facebook_cookies.py
```

### Ejecucion programada (macOS launchd)

```bash
cd "/Users/aitor/Documents/2. PROJECTES/AUTOMATIZACIONES/FEINA AUDIOVISUAL/audiovisual_jobs"

# Ejecucion manual con log timestamp
./scripts/run_pipeline.sh

# Instalar scheduler cada 6 horas (00:00, 06:00, 12:00, 18:00)
./scripts/install_launchd.sh

# Comandos simplificados de auto mode
./scripts/auto_mode.sh start
./scripts/auto_mode.sh status
./scripts/auto_mode.sh logs
./scripts/auto_mode.sh stop
```

El script `run_pipeline.sh` ya ejecuta automaticamente:
- `python main.py`
- `python scripts/cleanup_noisy_sources.py --apply`
- `python scripts/build_review_dashboard.py --offers-limit 1000`

Variables opcionales:
- `DASHBOARD_OFFERS_LIMIT=1500` para ampliar ofertas exportadas en dashboard/CSV.

### Limpieza de fuentes ruido (w3/duckduckgo)

```bash
cd "/Users/aitor/Documents/2. PROJECTES/AUTOMATIZACIONES/FEINA AUDIOVISUAL/audiovisual_jobs"
. venv/bin/activate

# Preview
python scripts/cleanup_noisy_sources.py

# Borrado real
python scripts/cleanup_noisy_sources.py --apply
```

### Dashboard sencillo + export para Google Sheets

```bash
cd "/Users/aitor/Documents/2. PROJECTES/AUTOMATIZACIONES/FEINA AUDIOVISUAL/audiovisual_jobs"
. venv/bin/activate

# Genera HTML + CSVs
python scripts/build_review_dashboard.py --offers-limit 1000

# Genera y abre en navegador
python scripts/build_review_dashboard.py --offers-limit 1000 --open
```

Archivos generados:
- `reports/dashboard_simple.html`
- `reports/google_sheets/ofertas_recientes.csv`
- `reports/google_sheets/roles_7d.csv`
- `reports/google_sheets/fuentes_rendimiento.csv`
- `reports/google_sheets/fuentes_7d.csv`

Importar a Google Sheets (manual y rapido):
1. Crear un Google Sheet nuevo.
2. `Archivo` -> `Importar` -> `Subir`.
3. Seleccionar cada CSV de `reports/google_sheets/`.
4. Elegir `Insertar hoja nueva` para cada archivo.


## 5) Como leer el dashboard

- **vw_fuentes_rendimiento**:
  - `priority_score` alto: fuente buena
  - `success_rate_pct` bajo + `error_count` alto: revisar selector o bloqueo

- **vw_ofertas_roles_7d**:
  - Volumen por rol canonicamente clasificado
  - Distribucion remoto/presencial

- **vw_ofertas_fuente_7d**:
  - Dominios que mas estan aportando ofertas reales


## 6) Configuracion clave en .env

- `TARGET_ROLES`
- `MIN_ROLE_SCORE` (3 recomendado para no perder demasiadas)
- `INCLUDE_REMOTE_ES_ONLY=true`
- `EXCLUDE_LATAM=true`


## 7) Estado actual

En este momento ya hay datos iniciales, pero el sistema todavia esta en fase de calibracion de fuentes:
- primero estabilizar fuentes top (RSS + institucionales)
- luego ajustar selectores en fuentes con `status=candidate/partial`
- luego aumentar cobertura (Telegram/Facebook y discovery continuo)

### Cobertura actual de fuentes

El catalogo ya incluye:
- Portales sectoriales (casting, audiovisual)
- Portales institucionales
- Portales generalistas de empleo (InfoJobs, Infoempleo, Jooble, Talent, JobisJob, etc.)
- ETT/consultoras (Adecco, Randstad, Manpower, Hays, Michael Page)

Consulta en SQL:

```sql
select categoria, count(*) as total
from public.fuentes_catalogo
group by categoria
order by total desc;
```
