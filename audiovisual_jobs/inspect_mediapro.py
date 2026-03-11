import asyncio
from playwright.async_api import async_playwright

async def inspect():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Scraping Mediapro Jobs List...")
        await page.goto("https://jobs.mediapro.tv/empleos/go/empleos/8725802/")
        await page.wait_for_timeout(3000)
        html = await page.content()
        with open("html_mediapro_jobs.txt", "w") as f:
            f.write(html)
            
        await browser.close()
        print("Done!")

asyncio.run(inspect())
