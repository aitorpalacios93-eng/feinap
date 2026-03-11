import asyncio
from playwright.async_api import async_playwright
from scrapers.antibot_utils import AntiBotManager

async def dump_milanuncios_js():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=AntiBotManager.get_random_user_agent(),
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        await AntiBotManager.apply_stealth(page)
        
        url = "https://www.milanuncios.com/ofertas-de-empleo-en-barcelona/audiovisual.htm"
        print(f"Navegando a {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        
        # Wait for JS hydration - wait for links to have href
        try:
            await page.wait_for_selector('.ma-AdCardListingV2-TitleLink[href]', timeout=12000)
            print("Title links have href! Extracting...")
        except Exception as e:
            print(f"Timeout waiting for title links with href: {e}")
            
        # Wait a bit more
        await asyncio.sleep(3)
        
        # Extract links by evaluating JS directly
        links = await page.evaluate("""
            () => {
                const cards = document.querySelectorAll('.ma-AdCardV2, article[data-testid="AD_CARD"]');
                return Array.from(cards).slice(0, 20).map(card => {
                    const titleLink = card.querySelector('.ma-AdCardListingV2-TitleLink, a[href]');
                    const title = card.querySelector('h2, .ma-AdCardV2-title');
                    return {
                        href: titleLink ? titleLink.getAttribute('href') : '',
                        title: title ? title.innerText : '',
                        card_html_prefix: card.innerHTML.slice(0, 500)
                    };
                });
            }
        """)
        
        print(f"\nResults ({len(links)} cards):")
        for l in links[:10]:
            print(f"  title: {l['title'][:60]} | href: {l['href']}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(dump_milanuncios_js())
