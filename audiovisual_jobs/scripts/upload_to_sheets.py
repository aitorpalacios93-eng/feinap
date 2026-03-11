#!/usr/bin/env python3
import argparse
import csv
import sys
from pathlib import Path
from typing import Any, List

import google.auth
from google.auth.exceptions import DefaultCredentialsError
from googleapiclient import discovery
from googleapiclient.errors import HttpError

BASE_DIR = Path(__file__).resolve().parents[1]
CREDENTIALS_PATH = BASE_DIR / "credentials" / "google_sheets.json"
SHEET_ID = "1U3gq9vUia0fr9YFXXw5Evp4zEF-Ikw4M6li2cIfSZXg"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sube CSV a Google Sheets (una hoja por archivo)"
    )
    parser.add_argument(
        "--csv-dir",
        default="reports/google_sheets",
        help="Directorio con CSVs a subir",
    )
    parser.add_argument(
        "--sheet-id",
        default=SHEET_ID,
        help="ID del Google Sheet",
    )
    return parser.parse_args()


def _get_sheets_service():
    try:
        credentials, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        if CREDENTIALS_PATH.exists():
            from google.oauth2 import service_account

            credentials = service_account.Credentials.from_service_account_file(
                str(CREDENTIALS_PATH),
                scopes=["https://www.googleapis.com/auth/spreadsheets"],
            )
        return discovery.build("sheets", "v4", credentials=credentials)
    except DefaultCredentialsError as exc:
        raise RuntimeError(
            f"No se pudieron obtener credenciales: {exc}. "
            f"Asegurate de que {CREDENTIALS_PATH} existe."
        )


def _read_csv(path: Path) -> List[List[Any]]:
    rows: List[List[Any]] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)
    return rows


def _get_or_create_sheet(service, sheet_id: str, sheet_name: str) -> str:
    spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    sheet_id_num = None
    for sheet in spreadsheet.get("sheets", []):
        if sheet.get("properties", {}).get("title") == sheet_name:
            sheet_id_num = sheet.get("properties", {}).get("sheetId")
            break

    if sheet_id_num is None:
        request = {"requests": [{"addSheet": {"properties": {"title": sheet_name}}}]}
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id, body=request
        ).execute()
        spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        for sheet in spreadsheet.get("sheets", []):
            if sheet.get("properties", {}).get("title") == sheet_name:
                sheet_id_num = sheet.get("properties", {}).get("sheetId")
                break

    return sheet_id_num


def _clear_sheet(
    service, sheet_id: str, sheet_id_num: str, row_count: int, col_count: int
) -> None:
    if row_count <= 0 and col_count <= 0:
        return
    clear_request = {
        "requests": [
            {
                "deleteDimension": {
                    "range": {
                        "sheetId": sheet_id_num,
                        "dimension": "ROWS",
                        "startIndex": 0,
                        "endIndex": max(1, row_count),
                    }
                }
            }
        ]
    }
    try:
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id, body=clear_request
        ).execute()
    except Exception:
        pass


def _write_sheet(
    service, sheet_id: str, sheet_name: str, rows: List[List[Any]]
) -> None:
    sheet_id_num = _get_or_create_sheet(service, sheet_id, sheet_name)

    body = {"values": rows}
    range_name = f"{sheet_name}!A1"
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=range_name,
        valueInputOption="USER_ENTERED",
        body=body,
    ).execute()
    print(f"  -> {sheet_name}: {len(rows)} filas escritas")


def main() -> int:
    args = _parse_args()

    csv_dir = BASE_DIR / args.csv_dir
    if not csv_dir.exists():
        print(f"Directorio no encontrado: {csv_dir}")
        return 1

    csv_files = sorted(csv_dir.glob("*.csv"))
    if not csv_files:
        print(f"No hay archivos CSV en {csv_dir}")
        return 1

    try:
        service = _get_sheets_service()
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 1

    print(f"Subiendo {len(csv_files)} archivos a Google Sheet {args.sheet_id}")

    for csv_path in csv_files:
        sheet_name = csv_path.stem.replace("_", " ")[:100]
        rows = _read_csv(csv_path)
        try:
            _write_sheet(service, args.sheet_id, sheet_name, rows)
        except HttpError as exc:
            print(f"Error subiendo {csv_path.name}: {exc}")
            continue

    print("Subida completada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
