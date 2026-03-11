from supabase import create_client, Client
from config.settings import settings


def get_supabase_client() -> Client:
    try:
        url = settings.SUPABASE_URL
        key = settings.SUPABASE_KEY
        if not url or not key:
            raise ValueError("SUPABASE_URL o SUPABASE_KEY no configuradas")
        client = create_client(url, key)
        return client
    except Exception as e:
        raise ConnectionError(f"Error al conectar con Supabase: {e}")


def test_connection(client: Client) -> bool:
    try:
        client.table("ofertas_empleo").select("id").limit(1).execute()
        return True
    except Exception as e:
        raise ConnectionError(f"Error de conexión a la base de datos: {e}")
