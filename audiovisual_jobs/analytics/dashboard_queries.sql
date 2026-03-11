-- Dashboard queries Plan Maestro

-- 1) Cobertura de roles (7 días)
SELECT *
FROM public.vw_ofertas_roles_7d
ORDER BY total DESC;

-- 2) Rendimiento de fuentes (global)
SELECT *
FROM public.vw_fuentes_rendimiento
ORDER BY priority_score DESC;

-- 3) Fuentes con más ofertas (7 días)
SELECT *
FROM public.vw_ofertas_fuente_7d
ORDER BY total DESC;

-- 4) Remoto España vs presencial
SELECT
    modalidad,
    COUNT(*)::int AS total
FROM public.ofertas_empleo
WHERE COALESCE(last_seen_at, extraido_el, NOW()) >= NOW() - INTERVAL '7 days'
GROUP BY modalidad
ORDER BY total DESC;

-- 5) Top ofertas por score de confianza
SELECT
    titulo_puesto,
    rol_canonico,
    score_confianza,
    modalidad,
    source_domain,
    enlace_fuente,
    COALESCE(last_seen_at, extraido_el) AS seen_at
FROM public.ofertas_empleo
WHERE COALESCE(last_seen_at, extraido_el, NOW()) >= NOW() - INTERVAL '7 days'
ORDER BY score_confianza DESC NULLS LAST, seen_at DESC
LIMIT 100;
