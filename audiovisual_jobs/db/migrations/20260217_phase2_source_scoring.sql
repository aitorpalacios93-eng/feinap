-- Fase 2 Plan Maestro
-- Scoring automático de fuentes + vistas de dashboard

BEGIN;

ALTER TABLE public.fuentes_catalogo
    ADD COLUMN IF NOT EXISTS consecutive_errors INT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_items_detected INT,
    ADD COLUMN IF NOT EXISTS next_retry_at TIMESTAMPTZ;

CREATE OR REPLACE VIEW public.vw_fuentes_rendimiento AS
SELECT
    fc.url,
    fc.domain,
    fc.nombre,
    fc.categoria,
    fc.status,
    fc.priority_score,
    fc.extraction_method,
    fc.success_count,
    fc.error_count,
    fc.avg_items,
    CASE
        WHEN (fc.success_count + fc.error_count) = 0 THEN 0
        ELSE ROUND((fc.success_count::numeric / (fc.success_count + fc.error_count)::numeric) * 100, 2)
    END AS success_rate_pct,
    fc.last_success_at,
    fc.last_checked_at,
    fc.include_remote,
    fc.exclude_latam,
    fc.next_retry_at
FROM public.fuentes_catalogo fc
ORDER BY fc.priority_score DESC;

CREATE OR REPLACE VIEW public.vw_ofertas_roles_7d AS
SELECT
    COALESCE(rol_canonico, 'sin_clasificar') AS rol_canonico,
    COUNT(*)::int AS total,
    ROUND(AVG(COALESCE(score_confianza, 0)), 2) AS score_medio,
    COUNT(*) FILTER (WHERE modalidad = 'remoto')::int AS total_remoto,
    COUNT(*) FILTER (WHERE modalidad = 'presencial')::int AS total_presencial,
    COUNT(*) FILTER (WHERE remoto_espana = TRUE)::int AS total_remoto_espana
FROM public.ofertas_empleo
WHERE COALESCE(last_seen_at, extraido_el, NOW()) >= NOW() - INTERVAL '7 days'
GROUP BY COALESCE(rol_canonico, 'sin_clasificar')
ORDER BY total DESC;

CREATE OR REPLACE VIEW public.vw_ofertas_fuente_7d AS
SELECT
    COALESCE(source_domain, 'sin_dominio') AS source_domain,
    COUNT(*)::int AS total,
    COUNT(*) FILTER (WHERE rol_canonico IS NOT NULL)::int AS total_clasificadas,
    ROUND(AVG(COALESCE(score_confianza, 0)), 2) AS score_medio,
    MAX(COALESCE(last_seen_at, extraido_el)) AS ultima_oferta
FROM public.ofertas_empleo
WHERE COALESCE(last_seen_at, extraido_el, NOW()) >= NOW() - INTERVAL '7 days'
GROUP BY COALESCE(source_domain, 'sin_dominio')
ORDER BY total DESC;

COMMIT;
