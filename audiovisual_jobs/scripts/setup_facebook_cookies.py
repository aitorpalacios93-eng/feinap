import asyncio
import json
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from playwright.async_api import async_playwright

from config.settings import settings


WAIT_SECONDS = 300


async def _run() -> int:
    cookies_path = Path(settings.FACEBOOK_COOKIES_PATH or "./cookies/facebook.json")
    cookies_path.parent.mkdir(parents=True, exist_ok=True)

    print("Abriendo navegador para login manual de Facebook...")
    print(
        "Cuando termines login, espera. El script detecta la sesion y guarda cookies."
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1366, "height": 900})
        page = await context.new_page()

        try:
            await page.goto("https://www.facebook.com/", wait_until="domcontentloaded")

            for elapsed in range(0, WAIT_SECONDS, 5):
                await asyncio.sleep(5)
                cookies = await context.cookies()
                names = {str(c.get("name", "")) for c in cookies}
                if "c_user" in names and "xs" in names:
                    with cookies_path.open("w", encoding="utf-8") as f:
                        json.dump(cookies, f, ensure_ascii=False, indent=2)
                    print(f"Cookies guardadas en: {cookies_path}")
                    print("Ya puedes ejecutar el pipeline con Facebook habilitado.")
                    return 0

                if elapsed and elapsed % 30 == 0:
                    pending = WAIT_SECONDS - elapsed
                    print(f"Esperando login... quedan aprox {pending} segundos")

            print("No se detecto sesion iniciada a tiempo. Reintenta el script.")
            return 2
        finally:
            await browser.close()


def main() -> int:
    return asyncio.run(_run())


if __name__ == "__main__":
    raise SystemExit(main())
