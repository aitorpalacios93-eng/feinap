import asyncio
from playwright.async_api import async_playwright
import os

async def check_linkedin():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        print("Navigating to LinkedIn...")
        await page.goto("https://www.linkedin.com/jobs/search/?keywords=editor%20video%20audiovisual&location=Espa%C3%B1a&f_TPR=r604800")
        await page.wait_for_timeout(5000)
        
        await page.screenshot(path="/Users/aitor/.gemini/antigravity/brain/2280c410-92be-4496-bf22-9a5a82690549/li_debug.png", full_page=True)
        print("Screenshot guardado en li_debug.png")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_linkedin())
