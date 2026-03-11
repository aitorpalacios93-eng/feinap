import argparse
import csv
import html
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from db.connection import get_supabase_client, test_connection


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera dashboard HTML y CSVs para Google Sheets"
    )
    parser.add_argument(
        "--offers-limit",
        type=int,
        default=1000,
        help="Numero maximo de ofertas recientes a exportar",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Abre el dashboard generado en el navegador",
    )
    parser.add_argument(
        "--output-dir",
        default="reports",
        help="Directorio de salida (default: reports)",
    )
    return parser.parse_args()


def _get_offers(client, limit: int) -> List[Dict[str, Any]]:
    return (
        client.table("ofertas_empleo")
        .select(
            "titulo_puesto,empresa,ubicacion,rol_canonico,score_confianza,modalidad,"
            "pais,region,ciudad,source_domain,tipo_fuente,fecha_publicacion,first_seen_at,last_seen_at,"
            "enlace_fuente,remoto_espana,es_latam,activo"
        )
        .order("last_seen_at", desc=True)
        .limit(limit)
        .execute()
        .data
        or []
    )


def _get_roles_7d(client) -> List[Dict[str, Any]]:
    return (
        client.table("vw_ofertas_roles_7d")
        .select("rol_canonico,total,score_medio,total_remoto")
        .order("total", desc=True)
        .limit(50)
        .execute()
        .data
        or []
    )


def _get_fuentes_rendimiento(client) -> List[Dict[str, Any]]:
    return (
        client.table("vw_fuentes_rendimiento")
        .select("domain,url,status,priority_score,success_rate_pct,avg_items")
        .order("priority_score", desc=True)
        .limit(50)
        .execute()
        .data
        or []
    )


def _get_fuentes_7d(client) -> List[Dict[str, Any]]:
    return (
        client.table("vw_ofertas_fuente_7d")
        .select("source_domain,total,total_clasificadas,score_medio")
        .order("total", desc=True)
        .limit(50)
        .execute()
        .data
        or []
    )


def _safe(value: Any) -> str:
    if value is None:
        return ""
    return html.escape(str(value))


def _table_html(rows: Iterable[Dict[str, Any]], columns: List[str]) -> str:
    rows = list(rows)
    if not rows:
        return "<p class='muted'>Sin datos.</p>"

    thead = "".join(f"<th>{_safe(c)}</th>" for c in columns)
    body_parts = []
    for row in rows:
        tds = []
        for col in columns:
            value = row.get(col)
            if col == "enlace_fuente" and value:
                value = f"<a href='{_safe(value)}' target='_blank'>ver oferta</a>"
            else:
                value = _safe(value)
            tds.append(f"<td>{value}</td>")
        body_parts.append("<tr>" + "".join(tds) + "</tr>")

    return (
        "<table><thead><tr>"
        + thead
        + "</tr></thead><tbody>"
        + "".join(body_parts)
        + "</tbody></table>"
    )


def _write_csv(path: Path, rows: List[Dict[str, Any]], columns: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col) for col in columns})


def _build_html(
    html_path: Path,
    offers: List[Dict[str, Any]],
    roles_7d: List[Dict[str, Any]],
    fuentes_rend: List[Dict[str, Any]],
    fuentes_7d: List[Dict[str, Any]],
) -> None:
    total_recent = len(offers)
    total_remote = sum(1 for o in offers if o.get("remoto_espana"))
    total_with_role = sum(1 for o in offers if o.get("rol_canonico"))
    total_latam = sum(1 for o in offers if o.get("es_latam"))
    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html_content = f"""
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Dashboard Empleo Audiovisual</title>
  <style>
    :root {{
      --bg: #f6f6f0;
      --card: #ffffff;
      --ink: #102027;
      --muted: #56707a;
      --accent: #00796b;
      --line: #d9e2e6;
    }}
    body {{ margin: 0; font-family: "Avenir Next", "Segoe UI", sans-serif; background: var(--bg); color: var(--ink); }}
    .wrap {{ max-width: 1280px; margin: 0 auto; padding: 24px; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; }}
    .muted {{ color: var(--muted); }}
    .kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 18px 0 22px; }}
    .kpi {{ background: linear-gradient(180deg, #ffffff 0%, #f8fbfc 100%); border: 1px solid var(--line); border-radius: 10px; padding: 14px; }}
    .kpi b {{ display: block; font-size: 24px; color: var(--accent); }}
    .section {{ background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 14px; margin-bottom: 14px; }}
    .section h2 {{ margin: 0 0 10px; font-size: 20px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ border-bottom: 1px solid var(--line); padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f2f8f8; position: sticky; top: 0; }}
    a {{ color: #03685d; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .hint {{ font-size: 12px; color: var(--muted); margin-top: 8px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Dashboard Empleo Audiovisual</h1>
    <div class="muted">Generado: {html.escape(generated)}</div>
    <div class="kpis">
      <div class="kpi"><span>Ofertas recientes</span><b>{total_recent}</b></div>
      <div class="kpi"><span>Con rol canonico</span><b>{total_with_role}</b></div>
      <div class="kpi"><span>Remoto Espana</span><b>{total_remote}</b></div>
      <div class="kpi"><span>Marcadas LATAM</span><b>{total_latam}</b></div>
    </div>

    <div class="section">
      <h2>Roles (7 dias)</h2>
      {_table_html(roles_7d, ["rol_canonico", "total", "score_medio", "total_remoto"])}
    </div>

    <div class="section">
      <h2>Fuentes Top (rendimiento)</h2>
      {_table_html(fuentes_rend, ["domain", "status", "priority_score", "success_rate_pct", "avg_items", "url"])}
    </div>

    <div class="section">
      <h2>Fuentes con ofertas (7 dias)</h2>
      {_table_html(fuentes_7d, ["source_domain", "total", "total_clasificadas", "score_medio"])}
    </div>

    <div class="section">
      <h2>Ofertas recientes</h2>
      {_table_html(offers, ["titulo_puesto", "empresa", "rol_canonico", "score_confianza", "modalidad", "ubicacion", "source_domain", "fecha_publicacion", "last_seen_at", "enlace_fuente"])}
      <div class="hint">Tip: importa los CSV en Google Sheets para filtrar y compartir.</div>
    </div>
  </div>
</body>
</html>
"""

    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html_content, encoding="utf-8")


def main() -> int:
    args = _parse_args()
    output_dir = BASE_DIR / args.output_dir
    csv_dir = output_dir / "google_sheets"
    html_path = output_dir / "dashboard_simple.html"

    try:
        client = get_supabase_client()
        test_connection(client)
    except Exception as exc:
        print(f"ERROR conexion Supabase: {exc}")
        return 1

    offers = _get_offers(client, limit=args.offers_limit)
    roles_7d = _get_roles_7d(client)
    fuentes_rend = _get_fuentes_rendimiento(client)
    fuentes_7d = _get_fuentes_7d(client)

    _build_html(html_path, offers, roles_7d, fuentes_rend, fuentes_7d)

    _write_csv(
        csv_dir / "ofertas_recientes.csv",
        offers,
        [
            "titulo_puesto",
            "empresa",
            "ubicacion",
            "rol_canonico",
            "score_confianza",
            "modalidad",
            "pais",
            "region",
            "ciudad",
            "source_domain",
            "tipo_fuente",
            "fecha_publicacion",
            "first_seen_at",
            "last_seen_at",
            "activo",
            "remoto_espana",
            "es_latam",
            "enlace_fuente",
        ],
    )
    _write_csv(
        csv_dir / "roles_7d.csv",
        roles_7d,
        ["rol_canonico", "total", "score_medio", "total_remoto"],
    )
    _write_csv(
        csv_dir / "fuentes_rendimiento.csv",
        fuentes_rend,
        ["domain", "url", "status", "priority_score", "success_rate_pct", "avg_items"],
    )
    _write_csv(
        csv_dir / "fuentes_7d.csv",
        fuentes_7d,
        ["source_domain", "total", "total_clasificadas", "score_medio"],
    )

    print(f"Dashboard HTML: {html_path}")
    print(f"CSV para Google Sheets: {csv_dir}")
    print(
        "CSV generados: ofertas_recientes.csv, roles_7d.csv, fuentes_rendimiento.csv, fuentes_7d.csv"
    )

    if args.open:
        webbrowser.open(html_path.as_uri())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
