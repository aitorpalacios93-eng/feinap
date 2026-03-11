import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def _print_header(title: str) -> None:
    print("\n" + "=" * 64)
    print(title)
    print("=" * 64)


def _fmt_mtime(path: Path) -> str:
    if not path.exists():
        return "missing"
    ts = datetime.fromtimestamp(path.stat().st_mtime)
    return ts.strftime("%Y-%m-%d %H:%M:%S")


def _show_launchd_status() -> None:
    _print_header("AUTO MODE")
    service = f"gui/{os.getuid()}/com.audiovisual.jobs.pipeline"
    try:
        result = subprocess.run(
            ["launchctl", "print", service],
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception as exc:
        print(f"No se pudo consultar launchd: {exc}")
        return

    if result.returncode != 0:
        print("Servicio launchd no encontrado o detenido")
        return

    lines = result.stdout.splitlines()
    keys = ("state =", "runs =", "last exit code =", "pid =")
    for line in lines:
        if any(k in line for k in keys):
            print(line.strip())


def _show_last_run_summary() -> None:
    _print_header("ULTIMO RESUMEN PIPELINE")
    log_path = BASE_DIR / "logs" / "app.log"
    if not log_path.exists():
        print("log app.log no existe")
        return

    lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    markers = [
        "RESUMEN FINAL",
        "Ofertas extraídas:",
        "Ofertas normalizadas:",
        "Ofertas guardadas:",
        "Errores al guardar:",
        "Prioridades de fuentes recalculadas:",
        "Proceso completado exitosamente",
    ]

    idx = -1
    for i, line in enumerate(lines):
        if "RESUMEN FINAL" in line:
            idx = i

    if idx == -1:
        print("No se encontro bloque de resumen en app.log")
        return

    found = []
    for line in lines[idx : idx + 40]:
        if any(m in line for m in markers):
            found.append(line)

    for line in found:
        print(line)


def _show_outputs() -> None:
    _print_header("DASHBOARD Y CSV")
    dashboard = BASE_DIR / "reports" / "dashboard_simple.html"
    csv_dir = BASE_DIR / "reports" / "google_sheets"
    print(f"dashboard: {dashboard}")
    print(f"dashboard actualizado: {_fmt_mtime(dashboard)}")

    csv_names = [
        "ofertas_recientes.csv",
        "roles_7d.csv",
        "fuentes_rendimiento.csv",
        "fuentes_7d.csv",
    ]
    for name in csv_names:
        p = csv_dir / name
        print(f"{name}: {_fmt_mtime(p)}")


def main() -> int:
    _show_launchd_status()
    _show_last_run_summary()
    _show_outputs()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
