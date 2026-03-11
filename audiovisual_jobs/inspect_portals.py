import asyncio
from playwright.async_api import async_playwright

async def inspect():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Scraping Mediapro...")
        await page.goto("https://jobs.mediapro.tv/")
        await page.wait_for_timeout(3000)
        html_mediapro = await page.content()
        with open("html_mediapro.txt", "w") as f:
            f.write(html_mediapro)
            
        print("Scraping convocatorias RTVE...")
        await page.goto("https://convocatorias.rtve.es/")
        await page.wait_for_timeout(3000)
        html_rtve = await page.content()
        with open("html_rtve.txt", "w") as f:
            f.write(html_rtve)
            
        await browser.close()
        print("Done!")

asyncio.run(inspect())
