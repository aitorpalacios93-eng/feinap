import asyncio
import httpx

async def test_infojobs_rss():
    urls = [
        "https://www.infojobs.net/trabajos.rss/q_audiovisual/",
        "https://www.infojobs.net/trabajos.rss/q_editor-video/",
        "https://www.infojobs.net/trabajos.rss/q_operador-camara/",
        "https://www.infojobs.net/trabajos.rss/q_produccion-audiovisual/",
        "https://www.infojobs.net/trabajos.rss/q_tecnico-sonido/"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        for url in urls:
            try:
                resp = await client.get(url, timeout=10)
                if resp.status_code == 200 and ("<?xml" in resp.text[:200] or "<rss" in resp.text[:200]):
                    print(f"✅ VÁLIDO: {url}")
                else:
                    print(f"❌ FALLO: {url} (Status: {resp.status_code})")
            except Exception as e:
                print(f"❌ ERROR: {url} - {e}")

if __name__ == "__main__":
    asyncio.run(test_infojobs_rss())
