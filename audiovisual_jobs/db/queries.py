from supabase import Client
from typing import Optional, Dict, Any, Iterable
from datetime import date, datetime, timezone, timedelta

from dateutil import parser as dt_parser


def upsert_oferta(
    client: Client,
    titulo_puesto: str,
    empresa: Optional[str],
    ubicacion: Optional[str],
    descripcion: Optional[str],
    enlace_fuente: str,
    tipo_fuente: str,
    fecha_publicacion: Optional[date] = None,
    rol_canonico: Optional[str] = None,
    subrol: Optional[str] = None,
    score_confianza: Optional[float] = None,
    modalidad: Optional[str] = None,
    pais: Optional[str] = None,
    region: Optional[str] = None,
    ciudad: Optional[str] = None,
    source_domain: Optional[str] = None,
    extraction_method: Optional[str] = None,
    hash_fingerprint: Optional[str] = None,
    remoto_espana: Optional[bool] = None,
    es_latam: Optional[bool] = None,
    first_seen_at: Optional[str] = None,
    last_seen_at: Optional[str] = None,
) -> list:
    data = {
        "titulo_puesto": titulo_puesto,
        "empresa": empresa,
        "ubicacion": ubicacion,
        "descripcion": descripcion,
        "enlace_fuente": enlace_fuente,
        "tipo_fuente": tipo_fuente,
        "rol_canonico": rol_canonico,
        "subrol": subrol,
        "score_confianza": score_confianza,
        "modalidad": modalidad,
        "pais": pais,
        "region": region,
        "ciudad": ciudad,
        "source_domain": source_domain,
        "extraction_method": extraction_method,
        "hash_fingerprint": hash_fingerprint,
        "remoto_espana": remoto_espana,
        "es_latam": es_latam,
        "first_seen_at": first_seen_at,
        "last_seen_at": last_seen_at or datetime.now(timezone.utc).isoformat(),
    }

    if fecha_publicacion:
        if isinstance(fecha_publicacion, date):
            data["fecha_publicacion"] = fecha_publicacion.isoformat()
        elif isinstance(fecha_publicacion, str):
            try:
                parsed = dt_parser.parse(fecha_publicacion)
                data["fecha_publicacion"] = parsed.date().isoformat()
            except Exception:
                pass

    # limpiar nulls innecesarios
    data = {k: v for k, v in data.items() if v is not None}

    try:
        response = (
            client.table("ofertas_empleo")
            .upsert(data, on_conflict="enlace_fuente")
            .execute()
        )
        return response.data
    except Exception as e:
        raise RuntimeError(f"Error al insertar oferta: {e}")


def insert_fuente_por_revisar(
    client: Client,
    url: str,
    titulo: Optional[str] = None,
    tipo_fuente: str = "web",
) -> list:
    data = {
        "url": url,
        "titulo": titulo,
        "tipo_fuente": tipo_fuente,
    }

    try:
        response = (
            client.table("fuentes_por_revisar")
            .upsert(data, on_conflict="url")
            .execute()
        )
        return response.data
    except Exception as e:
        raise RuntimeError(f"Error al insertar fuente: {e}")


def upsert_oferta_desde_dict(client: Client, oferta: Dict[str, Any]) -> list:
    return upsert_oferta(
        client=client,
        titulo_puesto=oferta.get("titulo_puesto", ""),
        empresa=oferta.get("empresa"),
        ubicacion=oferta.get("ubicacion"),
        descripcion=oferta.get("descripcion"),
        enlace_fuente=oferta.get("enlace_fuente", ""),
        tipo_fuente=oferta.get("tipo_fuente", "web"),
        fecha_publicacion=oferta.get("fecha_publicacion"),
        rol_canonico=oferta.get("rol_canonico"),
        subrol=oferta.get("subrol"),
        score_confianza=oferta.get("score_confianza"),
        modalidad=oferta.get("modalidad"),
        pais=oferta.get("pais"),
        region=oferta.get("region"),
        ciudad=oferta.get("ciudad"),
        source_domain=oferta.get("source_domain"),
        extraction_method=oferta.get("extraction_method"),
        hash_fingerprint=oferta.get("hash_fingerprint"),
        remoto_espana=oferta.get("remoto_espana"),
        es_latam=oferta.get("es_latam"),
        first_seen_at=oferta.get("first_seen_at"),
        last_seen_at=oferta.get("last_seen_at"),
    )


def upsert_fuente_catalogo(client: Client, fuente: Dict[str, Any]) -> list:
    data = {
        "url": fuente.get("url"),
        "domain": fuente.get("domain"),
        "nombre": fuente.get("nombre"),
        "categoria": fuente.get("categoria"),
        "extraction_method": fuente.get("extraction_method", "playwright"),
        "priority_score": fuente.get("priority_score", 50),
        "status": fuente.get("status", "candidate"),
        "idioma": fuente.get("idioma", "es"),
        "alcance_geografico": fuente.get("alcance_geografico", "es"),
        "include_remote": fuente.get("include_remote", True),
        "exclude_latam": fuente.get("exclude_latam", True),
        "notes": fuente.get("notes"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    data = {k: v for k, v in data.items() if v is not None}

    try:
        response = (
            client.table("fuentes_catalogo").upsert(data, on_conflict="url").execute()
        )
        return response.data
    except Exception as e:
        raise RuntimeError(f"Error al insertar fuente en catálogo: {e}")


def upsert_fuentes_catalogo_bulk(
    client: Client, fuentes: Iterable[Dict[str, Any]]
) -> int:
    total = 0
    for fuente in fuentes:
        upsert_fuente_catalogo(client, fuente)
        total += 1
    return total


def get_ofertas_recientes(client: Client, limit: int = 100) -> list:
    try:
        response = (
            client.table("ofertas_empleo")
            .select("*")
            .order("extraido_el", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data
    except Exception as e:
        raise RuntimeError(f"Error al obtener ofertas: {e}")

def get_ofertas_hoy(client: Client) -> list:
    hoy_iso = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    try:
        response = (
            client.table("ofertas_empleo")
            .select("*")
            .gte("first_seen_at", hoy_iso)
            .order("score_confianza", desc=True)
            .execute()
        )
        return response.data
    except Exception as e:
        raise RuntimeError(f"Error al obtener ofertas de hoy: {e}")


def get_fuentes_por_revisar(client: Client, limit: int = 50) -> list:
    try:
        response = (
            client.table("fuentes_por_revisar")
            .select("*")
            .eq("revisado", False)
            .limit(limit)
            .execute()
        )
        return response.data
    except Exception as e:
        raise RuntimeError(f"Error al obtener fuentes: {e}")


def get_fuentes_activas_priorizadas(
    client: Client,
    limit: int = 30,
    min_priority: int = 35,
) -> list:
    try:
        response = (
            client.table("fuentes_catalogo")
            .select("url,status,priority_score,extraction_method,next_retry_at")
            .in_("status", ["verified", "partial", "candidate"])
            .gte("priority_score", min_priority)
            .order("priority_score", desc=True)
            .limit(limit * 2)
            .execute()
        )
        rows = response.data or []
        now = datetime.now(timezone.utc)
        filtered = []
        for row in rows:
            next_retry = row.get("next_retry_at")
            if not next_retry:
                filtered.append(row)
                continue
            try:
                retry_dt = dt_parser.parse(next_retry)
                if retry_dt <= now:
                    filtered.append(row)
            except Exception:
                filtered.append(row)
        return filtered[:limit]
    except Exception as e:
        raise RuntimeError(f"Error obteniendo fuentes activas priorizadas: {e}")


def record_fuente_health(
    client: Client,
    source_url: str,
    status: str,
    latency_ms: Optional[int] = None,
    items_detected: int = 0,
    error_message: Optional[str] = None,
) -> None:
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        client.table("fuentes_health").insert(
            {
                "source_url": source_url,
                "checked_at": now_iso,
                "status": status,
                "latency_ms": latency_ms,
                "items_detected": items_detected,
                "error_message": error_message,
            }
        ).execute()

        current = (
            client.table("fuentes_catalogo")
            .select(
                "url,status,success_count,error_count,avg_items,last_success_at,priority_score,consecutive_errors"
            )
            .eq("url", source_url)
            .limit(1)
            .execute()
        )
        row = (current.data or [{}])[0]

        if not row.get("url"):
            domain = source_url.split("//")[-1].split("/")[0].lower()
            upsert_fuente_catalogo(
                client,
                {
                    "url": source_url,
                    "domain": domain,
                    "nombre": domain,
                    "categoria": "runtime",
                    "status": "candidate",
                    "priority_score": 45,
                    "idioma": "es",
                    "alcance_geografico": "es",
                    "include_remote": True,
                    "exclude_latam": True,
                    "notes": "Alta automática en runtime",
                },
            )
            row = {
                "status": "candidate",
                "success_count": 0,
                "error_count": 0,
                "avg_items": 0,
                "priority_score": 45,
                "consecutive_errors": 0,
            }

        success_count = int(row.get("success_count") or 0)
        error_count = int(row.get("error_count") or 0)
        consecutive_errors = int(row.get("consecutive_errors") or 0)
        avg_items = float(row.get("avg_items") or 0)
        current_status = row.get("status") or "candidate"

        updates: Dict[str, Any] = {"last_checked_at": now_iso}

        if status == "success":
            new_success = success_count + 1
            new_avg = round(
                ((avg_items * success_count) + max(0, items_detected)) / new_success, 2
            )
            updates.update(
                {
                    "success_count": new_success,
                    "avg_items": new_avg,
                    "last_success_at": now_iso,
                    "consecutive_errors": 0,
                    "last_items_detected": items_detected,
                    "next_retry_at": None,
                }
            )
            if current_status in ("candidate", "partial", "blocked"):
                updates["status"] = "verified" if new_success >= 3 else "partial"
        elif status in ("empty", "timeout", "error", "blocked"):
            new_error = error_count + 1
            new_consecutive = consecutive_errors + 1
            backoff_minutes = min(24 * 60, 15 * (2 ** max(0, new_consecutive - 1)))
            next_retry = (
                datetime.now(timezone.utc) + timedelta(minutes=backoff_minutes)
            ).isoformat()
            updates["error_count"] = new_error
            updates["consecutive_errors"] = new_consecutive
            updates["last_items_detected"] = items_detected
            updates["next_retry_at"] = next_retry
            if status == "blocked":
                updates["status"] = "blocked"
            elif current_status == "candidate":
                updates["status"] = "partial"

        client.table("fuentes_catalogo").update(updates).eq("url", source_url).execute()
    except Exception as e:
        raise RuntimeError(f"Error registrando health de fuente {source_url}: {e}")


def recalculate_fuentes_prioridad(client: Client) -> int:
    try:
        response = (
            client.table("fuentes_catalogo")
            .select(
                "url,status,priority_score,success_count,error_count,avg_items,last_success_at"
            )
            .execute()
        )
        rows = response.data or []
        updated = 0

        for row in rows:
            url = row.get("url")
            if not url:
                continue

            current_status = row.get("status") or "candidate"
            if current_status in ("disabled", "requires_login"):
                continue

            success_count = int(row.get("success_count") or 0)
            error_count = int(row.get("error_count") or 0)
            avg_items = float(row.get("avg_items") or 0)
            total = success_count + error_count
            success_rate = (success_count / total) if total > 0 else 0.0

            freshness_score = 0
            last_success_raw = row.get("last_success_at")
            if last_success_raw:
                try:
                    last_success_dt = dt_parser.parse(last_success_raw)
                    delta_days = (datetime.now(timezone.utc) - last_success_dt).days
                    if delta_days <= 1:
                        freshness_score = 15
                    elif delta_days <= 3:
                        freshness_score = 10
                    elif delta_days <= 7:
                        freshness_score = 5
                except Exception:
                    freshness_score = 0

            volume_score = min(avg_items, 30.0) / 30.0 * 35.0
            reliability_score = success_rate * 45.0
            penalty = min(error_count, 20) * 1.2
            priority_score = int(
                max(
                    1,
                    min(
                        100,
                        round(
                            20
                            + volume_score
                            + reliability_score
                            + freshness_score
                            - penalty
                        ),
                    ),
                )
            )

            if total >= 8 and success_rate < 0.15:
                new_status = "blocked"
            elif success_rate >= 0.65 and avg_items >= 1:
                new_status = "verified"
            elif success_rate >= 0.25:
                new_status = "partial"
            else:
                new_status = "candidate"

            client.table("fuentes_catalogo").update(
                {
                    "priority_score": priority_score,
                    "status": new_status,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            ).eq("url", url).execute()
            updated += 1

        return updated
    except Exception as e:
        raise RuntimeError(f"Error recalculando prioridad de fuentes: {e}")

def insert_daily_insight(client: Client, content_html: str) -> None:
    """Guarda un resumen diario de inteligencia (Groq/Llama) en Supabase."""
    try:
        # Check if one already exists for today to avoid duplicates (table has unique date constraint)
        # Using upsert requires checking uniqueness, but inserting and catching is fine.
        client.table("daily_insights").upsert(
            {
                "date": datetime.now(timezone.utc).date().isoformat(),
                "content_html": content_html,
            },
            on_conflict="date"
        ).execute()
    except Exception as e:
        raise RuntimeError(f"Error al guardar daily insight: {e}")
