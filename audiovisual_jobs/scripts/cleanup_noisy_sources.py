import argparse
import sys
from pathlib import Path
from typing import Dict, List, Set

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from db.connection import get_supabase_client, test_connection


DEFAULT_PATTERNS = ["w3.org", "duckduckgo.com"]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Limpia URLs ruido del catalogo de fuentes"
    )
    parser.add_argument(
        "--pattern",
        action="append",
        default=[],
        help="Patron a eliminar (se puede repetir). Default: w3.org, duckduckgo.com",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplica borrado real (sin esta flag solo muestra preview)",
    )
    return parser.parse_args()


def _find_urls(client, table: str, patterns: List[str]) -> Set[str]:
    urls: Set[str] = set()
    for pattern in patterns:
        try:
            rows = (
                client.table(table)
                .select("url")
                .ilike("url", f"%{pattern}%")
                .limit(500)
                .execute()
                .data
            ) or []
            for row in rows:
                value = str(row.get("url") or "").strip()
                if value:
                    urls.add(value)
        except Exception as exc:
            print(f"WARN: no se pudo buscar en {table} con pattern={pattern}: {exc}")
    return urls


def _delete_urls(client, table: str, urls: Set[str]) -> int:
    deleted = 0
    for url in sorted(urls):
        try:
            client.table(table).delete().eq("url", url).execute()
            deleted += 1
        except Exception as exc:
            print(f"WARN: no se pudo borrar {url} de {table}: {exc}")
    return deleted


def main() -> int:
    args = _parse_args()
    patterns = [
        p.strip().lower() for p in args.pattern if p.strip()
    ] or DEFAULT_PATTERNS

    try:
        client = get_supabase_client()
        test_connection(client)
    except Exception as exc:
        print(f"ERROR conexion Supabase: {exc}")
        return 1

    catalog_urls = _find_urls(client, "fuentes_catalogo", patterns)
    review_urls = _find_urls(client, "fuentes_por_revisar", patterns)
    all_urls = sorted(catalog_urls | review_urls)

    print(f"Patterns: {', '.join(patterns)}")
    print(f"Coincidencias catalogo: {len(catalog_urls)}")
    print(f"Coincidencias por_revisar: {len(review_urls)}")
    print(f"Total URLs candidatas: {len(all_urls)}")
    for url in all_urls:
        print(f" - {url}")

    if not args.apply:
        print("\nPreview only. Usa --apply para borrar.")
        return 0

    deleted_catalog = _delete_urls(client, "fuentes_catalogo", catalog_urls)
    deleted_review = _delete_urls(client, "fuentes_por_revisar", review_urls)

    print("\nBorrado completado")
    print(f" - fuentes_catalogo: {deleted_catalog}")
    print(f" - fuentes_por_revisar: {deleted_review}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
