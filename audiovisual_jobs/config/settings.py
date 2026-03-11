import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)


class Settings:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
    TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
    TELEGRAM_CHANNELS = os.getenv("TELEGRAM_CHANNELS", "").split(",")
    TELEGRAM_INTERACTIVE_LOGIN = (
        os.getenv("TELEGRAM_INTERACTIVE_LOGIN", "false").lower() == "true"
    )

    FACEBOOK_COOKIES_PATH = os.getenv("FACEBOOK_COOKIES_PATH")
    FACEBOOK_GROUPS = os.getenv("FACEBOOK_GROUPS", "").split(",")

    SERPAPI_KEY = os.getenv("SERPAPI_KEY")

    HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
    TIMEOUT = int(os.getenv("TIMEOUT", "15000"))
    DELAY_MIN = int(os.getenv("DELAY_MIN", "1"))
    DELAY_MAX = int(os.getenv("DELAY_MAX", "2"))
    MAX_REINTENTOS = 1  # Reducir reintentos para ser más rápido
    OFERTAS_POR_PORTAL = int(os.getenv("OFERTAS_POR_PORTAL", "20"))

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = BASE_DIR / "logs" / "app.log"

    # Portales configurados
    PORTALES_SCRAPER = os.getenv("PORTALES_SCRAPER", "").split(",")
    PORTALES_AVANZADOS = os.getenv("PORTALES_AVANZADOS", "").split(",")

    # Discovery
    DISCOVERY_QUERIES = os.getenv("DISCOVERY_QUERIES", "").split("|")
    KEYWORDS_FILTRO = os.getenv("KEYWORDS_FILTRO", "").split(",")
    UBICACIONES_PRIORITARIAS = os.getenv("UBICACIONES_PRIORITARIAS", "").split(",")
    TARGET_ROLES = os.getenv(
        "TARGET_ROLES",
        "edicion_post,realizacion,operador_camara_video,operador_sonido,ayudante_produccion,produccion,relacionados",
    ).split(",")
    INCLUDE_REMOTE_ES_ONLY = (
        os.getenv("INCLUDE_REMOTE_ES_ONLY", "true").lower() == "true"
    )
    EXCLUDE_LATAM = os.getenv("EXCLUDE_LATAM", "true").lower() == "true"
    MIN_ROLE_SCORE = int(os.getenv("MIN_ROLE_SCORE", "3"))
    SOURCES_LIMIT = int(os.getenv("SOURCES_LIMIT", "80"))
    SOURCES_MIN_PRIORITY = int(os.getenv("SOURCES_MIN_PRIORITY", "20"))

    # Email alerts configuration
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    ALERT_EMAIL_FROM = os.getenv("ALERT_EMAIL_FROM", "")
    ALERT_EMAIL_PASSWORD = os.getenv("ALERT_EMAIL_PASSWORD", "")
    ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO", "aitorpalacios93@gmail.com")

    @classmethod
    def validate(cls):
        errors = []
        if not cls.SUPABASE_URL:
            errors.append("SUPABASE_URL no configurada")
        if not cls.SUPABASE_KEY:
            errors.append("SUPABASE_KEY no configurada")
        if errors:
            raise ValueError(f"Configuración incompleta: {', '.join(errors)}")
        return True


settings = Settings()
