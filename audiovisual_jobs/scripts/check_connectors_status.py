import asyncio
import json
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from telethon import TelegramClient

from config.settings import settings


def _status(value: bool) -> str:
    return "OK" if value else "MISSING"


def _check_facebook_cookies() -> tuple[bool, str]:
    path = Path(settings.FACEBOOK_COOKIES_PATH or "./cookies/facebook.json")
    if not path.exists():
        return False, f"{path} no existe"

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, f"cookies invalidas: {exc}"

    if not isinstance(data, list):
        return False, "cookies invalidas: formato esperado lista"

    names = {str(item.get("name", "")) for item in data if isinstance(item, dict)}
    has_session = "c_user" in names and "xs" in names
    if not has_session:
        return False, "faltan cookies c_user/xs"
    return True, f"{path}"


async def _check_telegram_auth() -> tuple[bool, str]:
    if not settings.TELEGRAM_API_ID or not settings.TELEGRAM_API_HASH:
        return False, "faltan TELEGRAM_API_ID/TELEGRAM_API_HASH"

    session_file = Path("session_telegram.session")
    if not session_file.exists():
        return False, "session_telegram.session no existe"

    client = TelegramClient(
        "session_telegram",
        int(settings.TELEGRAM_API_ID),
        settings.TELEGRAM_API_HASH,
    )
    await client.connect()
    try:
        authorized = await client.is_user_authorized()
        if not authorized:
            return False, "session_telegram.session sin autorizar"
        return True, "session_telegram.session autorizada"
    finally:
        await client.disconnect()


async def _run() -> int:
    print("== ENV ==")
    print(f"SUPABASE_URL: {_status(bool(settings.SUPABASE_URL))}")
    print(f"SUPABASE_KEY: {_status(bool(settings.SUPABASE_KEY))}")
    print(f"TELEGRAM_API_ID: {_status(bool(settings.TELEGRAM_API_ID))}")
    print(f"TELEGRAM_API_HASH: {_status(bool(settings.TELEGRAM_API_HASH))}")
    print(
        f"TELEGRAM_CHANNELS: {len([c for c in settings.TELEGRAM_CHANNELS if c.strip()])}"
    )
    print(f"FACEBOOK_GROUPS: {len([g for g in settings.FACEBOOK_GROUPS if g.strip()])}")

    print("\n== TELEGRAM ==")
    tg_ok, tg_detail = await _check_telegram_auth()
    print(f"Authorized: {_status(tg_ok)} ({tg_detail})")

    print("\n== FACEBOOK ==")
    fb_ok, fb_detail = _check_facebook_cookies()
    print(f"Cookies: {_status(fb_ok)} ({fb_detail})")

    print("\n== READY ==")
    ready = tg_ok and fb_ok
    print(f"Social connectors ready: {_status(ready)}")
    return 0 if ready else 2


def main() -> int:
    return asyncio.run(_run())


if __name__ == "__main__":
    raise SystemExit(main())
