import asyncio
import argparse
import getpass
import inspect
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from telethon import TelegramClient
from telethon.errors import (
    PhoneCodeExpiredError,
    PhoneCodeInvalidError,
    SessionPasswordNeededError,
)

from config.settings import settings


SESSION_NAME = "session_telegram"


async def _maybe_await(result):
    if inspect.isawaitable(result):
        return await result
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Crea o autoriza la sesion de Telegram para el scraper"
    )
    parser.add_argument(
        "--mode",
        choices=["qr", "phone"],
        default="qr",
        help="Metodo de login: qr (default) o phone",
    )
    parser.add_argument(
        "--open-link",
        action="store_true",
        help="Intenta abrir automaticamente el enlace tg:// en tu sistema",
    )
    parser.add_argument(
        "--force-sms",
        action="store_true",
        help="Fuerza envio por SMS en login por telefono",
    )
    return parser.parse_args()


async def _login_with_qr(client: TelegramClient, open_link: bool = False) -> bool:
    print("Intentando login por QR...")
    print("Abre Telegram > Ajustes > Dispositivos > Conectar dispositivo")
    try:
        qr_login = await _maybe_await(client.qr_login())
    except Exception as exc:
        print(f"No fue posible iniciar QR login: {exc}")
        return False

    print("Escanea este enlace QR desde Telegram:")
    print(qr_login.url)
    print("Nota: en terminal no se dibuja imagen QR; este enlace tg:// es el login.")

    qr_image_url = (
        "https://api.qrserver.com/v1/create-qr-code/?size=360x360&data="
        f"{quote(qr_login.url, safe='')}"
    )
    print("Si tu app no abre tg://, abre esta URL en el navegador para ver el QR:")
    print(qr_image_url)

    if sys.platform == "darwin":
        print("Si usas Telegram Desktop, puedes abrirlo con:")
        print(f'open "{qr_login.url}"')
        if open_link:
            try:
                subprocess.run(["open", qr_image_url], check=False)
                print("Se intento abrir el QR en el navegador automaticamente.")
            except Exception as exc:
                print(f"No se pudo abrir el enlace automaticamente: {exc}")

    try:
        await asyncio.wait_for(_maybe_await(qr_login.wait()), timeout=240)
        return True
    except SessionPasswordNeededError:
        password = getpass.getpass("Telegram 2FA password: ")
        await _maybe_await(client.sign_in(password=password))
        return True
    except asyncio.TimeoutError:
        print("Timeout esperando el escaneo QR.")
        return False
    except Exception as exc:
        print(f"QR login fallo: {exc}")
        return False


async def _login_with_phone(client: TelegramClient, force_sms: bool = False) -> None:
    print("Iniciando login por telefono/codigo...")
    phone = input("Telefono (formato +34...): ").strip()
    if not phone:
        print("Telefono vacio. Cancelado.")
        return

    sent_code = await _maybe_await(client.send_code_request(phone, force_sms=force_sms))
    sent_type = type(getattr(sent_code, "type", None)).__name__
    print(f"Codigo enviado via: {sent_type}")
    if "App" in sent_type:
        print("Revisa la app de Telegram (chat oficial llamado 'Telegram').")
        print("Tambien mira chats archivados y otros dispositivos activos.")
    elif "Sms" in sent_type:
        print("Revisa SMS de tu numero.")

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        code = input("Introduce el codigo recibido: ").strip()
        if not code:
            print("Codigo vacio. Intenta de nuevo.")
            continue

        try:
            await _maybe_await(
                client.sign_in(
                    phone=phone,
                    code=code,
                    phone_code_hash=sent_code.phone_code_hash,
                )
            )
            return
        except SessionPasswordNeededError:
            password = getpass.getpass("Telegram 2FA password: ")
            await _maybe_await(client.sign_in(password=password))
            return
        except PhoneCodeInvalidError:
            print(f"Codigo invalido (intento {attempt}/{max_attempts}).")
        except PhoneCodeExpiredError:
            print("Codigo expirado. Solicitando uno nuevo...")
            sent_code = await _maybe_await(
                client.send_code_request(phone, force_sms=force_sms)
            )
        except Exception as exc:
            print(f"Error validando codigo: {exc}")

    print("No se pudo completar login por telefono tras varios intentos.")


async def _run(mode: str, open_link: bool, force_sms: bool) -> int:
    if not settings.TELEGRAM_API_ID or not settings.TELEGRAM_API_HASH:
        print("Falta TELEGRAM_API_ID o TELEGRAM_API_HASH en .env")
        return 1

    client = TelegramClient(
        SESSION_NAME,
        int(settings.TELEGRAM_API_ID),
        settings.TELEGRAM_API_HASH,
    )

    await _maybe_await(client.connect())
    try:
        if await _maybe_await(client.is_user_authorized()):
            print("Sesion Telegram ya autorizada.")
            return 0

        if mode == "phone":
            await _login_with_phone(client, force_sms=force_sms)
        else:
            ok = await _login_with_qr(client, open_link=open_link)
            if not ok:
                print("Fallback a login por telefono/codigo...")
                await _login_with_phone(client, force_sms=force_sms)

        if await _maybe_await(client.is_user_authorized()):
            print("Sesion Telegram creada y autorizada correctamente.")
            print("Archivo esperado: session_telegram.session")
            return 0

        print("No se pudo autorizar la sesion Telegram.")
        return 2
    finally:
        disconnect_result = client.disconnect()
        if inspect.isawaitable(disconnect_result):
            await disconnect_result


def main() -> int:
    args = _parse_args()
    return asyncio.run(
        _run(mode=args.mode, open_link=args.open_link, force_sms=args.force_sms)
    )


if __name__ == "__main__":
    raise SystemExit(main())
