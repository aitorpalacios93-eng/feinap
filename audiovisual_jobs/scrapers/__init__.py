from scrapers.base import BaseScraper
from scrapers.web_scraper import WebScraper, ejecutar_web_scraper
from scrapers.telegram_scraper import TelegramScraper, ejecutar_telegram_scraper
from scrapers.facebook_scraper import FacebookScraper, ejecutar_facebook_scraper

__all__ = [
    "BaseScraper",
    "WebScraper",
    "ejecutar_web_scraper",
    "TelegramScraper",
    "ejecutar_telegram_scraper",
    "FacebookScraper",
    "ejecutar_facebook_scraper",
]
