import sys
from pathlib import Path

from config.settings import settings
from db.connection import get_supabase_client, test_connection


def print_header(title: str) -> None:
    print("\n" + "=" * 70)
    print(f"{title}")
    print("=" * 70)


def main() -> None:
    print_header("DASHBOARD KPI - PLAN MAESTRO")

    try:
        settings.validate()
        client = get_supabase_client()
        test_connection(client)
    except Exception as e:
        print(f"ERROR de conexión: {e}")
        sys.exit(1)

    try:
        roles = client.table("vw_ofertas_roles_7d").select("*").limit(30).execute().data
        fuentes = (
            client.table("vw_fuentes_rendimiento")
            .select("url,domain,status,priority_score,success_rate_pct,avg_items")
            .order("priority_score", desc=True)
            .limit(15)
            .execute()
            .data
        )
        fuentes_7d = (
            client.table("vw_ofertas_fuente_7d")
            .select("source_domain,total,total_clasificadas,score_medio")
            .order("total", desc=True)
            .limit(15)
            .execute()
            .data
        )
    except Exception as e:
        print(f"ERROR leyendo vistas KPI: {e}")
        sys.exit(1)

    print_header("Roles (7 días)")
    if not roles:
        print("Sin datos aún")
    else:
        for r in roles:
            print(
                f"- {r.get('rol_canonico')}: total={r.get('total')} | "
                f"score={r.get('score_medio')} | remoto={r.get('total_remoto')}"
            )

    print_header("Fuentes Top (rendimiento)")
    if not fuentes:
        print("Sin datos aún")
    else:
        for f in fuentes:
            print(
                f"- {f.get('domain')} | status={f.get('status')} | "
                f"priority={f.get('priority_score')} | success%={f.get('success_rate_pct')} | "
                f"avg_items={f.get('avg_items')}"
            )

    print_header("Fuentes con ofertas (7 días)")
    if not fuentes_7d:
        print("Sin datos aún")
    else:
        for f in fuentes_7d:
            print(
                f"- {f.get('source_domain')}: total={f.get('total')} | "
                f"clasificadas={f.get('total_clasificadas')} | score={f.get('score_medio')}"
            )


if __name__ == "__main__":
    main()
