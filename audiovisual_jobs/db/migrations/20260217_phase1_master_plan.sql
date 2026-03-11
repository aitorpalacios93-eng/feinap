-- Fase 1 Plan Maestro
-- Extiende esquema para clasificación de roles, geofiltro y source registry

BEGIN;

-- 1) Ampliación de ofertas_empleo
ALTER TABLE public.ofertas_empleo
    ADD COLUMN IF NOT EXISTS rol_canonico TEXT,
    ADD COLUMN IF NOT EXISTS subrol TEXT,
    ADD COLUMN IF NOT EXISTS score_confianza NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS modalidad TEXT,
    ADD COLUMN IF NOT EXISTS pais TEXT,
    ADD COLUMN IF NOT EXISTS region TEXT,
    ADD COLUMN IF NOT EXISTS ciudad TEXT,
    ADD COLUMN IF NOT EXISTS source_domain TEXT,
    ADD COLUMN IF NOT EXISTS extraction_method TEXT,
    ADD COLUMN IF NOT EXISTS hash_fingerprint TEXT,
    ADD COLUMN IF NOT EXISTS remoto_espana BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS es_latam BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ DEFAULT NOW();

UPDATE public.ofertas_empleo
SET
    first_seen_at = COALESCE(first_seen_at, extraido_el, NOW()),
    last_seen_at = COALESCE(last_seen_at, extraido_el, NOW())
WHERE first_seen_at IS NULL OR last_seen_at IS NULL;

ALTER TABLE public.ofertas_empleo
    DROP CONSTRAINT IF EXISTS ofertas_empleo_tipo_fuente_check;

ALTER TABLE public.ofertas_empleo
    ADD CONSTRAINT ofertas_empleo_tipo_fuente_check
    CHECK (
        tipo_fuente = ANY(
            ARRAY[
                'web'::TEXT,
                'telegram'::TEXT,
                'facebook'::TEXT,
                'google'::TEXT,
                'rss'::TEXT,
                'api'::TEXT,
                'sitemap'::TEXT,
                'manual'::TEXT
            ]
        )
    );

CREATE INDEX IF NOT EXISTS idx_ofertas_rol_canonico ON public.ofertas_empleo(rol_canonico);
CREATE INDEX IF NOT EXISTS idx_ofertas_modalidad ON public.ofertas_empleo(modalidad);
CREATE INDEX IF NOT EXISTS idx_ofertas_source_domain ON public.ofertas_empleo(source_domain);
CREATE INDEX IF NOT EXISTS idx_ofertas_last_seen_at ON public.ofertas_empleo(last_seen_at DESC);
CREATE INDEX IF NOT EXISTS idx_ofertas_hash_fingerprint ON public.ofertas_empleo(hash_fingerprint);

-- 2) Source registry de alto rendimiento
CREATE TABLE IF NOT EXISTS public.fuentes_catalogo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT UNIQUE NOT NULL,
    domain TEXT NOT NULL,
    nombre TEXT,
    categoria TEXT,
    extraction_method TEXT NOT NULL DEFAULT 'playwright',
    priority_score INT NOT NULL DEFAULT 50,
    status TEXT NOT NULL DEFAULT 'candidate'
        CHECK (status IN ('candidate', 'verified', 'partial', 'blocked', 'requires_login', 'disabled')),
    idioma TEXT NOT NULL DEFAULT 'es',
    alcance_geografico TEXT,
    include_remote BOOLEAN NOT NULL DEFAULT TRUE,
    exclude_latam BOOLEAN NOT NULL DEFAULT TRUE,
    last_checked_at TIMESTAMPTZ,
    last_success_at TIMESTAMPTZ,
    success_count INT NOT NULL DEFAULT 0,
    error_count INT NOT NULL DEFAULT 0,
    avg_items NUMERIC(10,2) NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fuentes_catalogo_status_priority
    ON public.fuentes_catalogo(status, priority_score DESC);

CREATE INDEX IF NOT EXISTS idx_fuentes_catalogo_domain
    ON public.fuentes_catalogo(domain);

-- 3) Histórico de health-check por fuente
CREATE TABLE IF NOT EXISTS public.fuentes_health (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_url TEXT NOT NULL REFERENCES public.fuentes_catalogo(url) ON DELETE CASCADE,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL,
    latency_ms INT,
    items_detected INT,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_fuentes_health_url_checked
    ON public.fuentes_health(source_url, checked_at DESC);

COMMIT;
