import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print("=" * 50)
print("TEST: Conexión a Supabase")
print("=" * 50)
print(f"URL: {SUPABASE_URL}")
print(f"Key: {SUPABASE_KEY[:20]}..." if SUPABASE_KEY else "Key: NO CONFIGURADA")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("\n❌ ERROR: Faltan credenciales en .env")
    sys.exit(1)

try:
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("\n✅ Cliente creado correctamente")

    print("\nConsultando tabla ofertas_empleo...")
    response = client.table("ofertas_empleo").select("*").limit(1).execute()

    print(f"✅ Conexión exitosa!")
    print(f"Datos recibidos: {response.data}")
    print(
        f"Campos disponibles: {list(response.data[0].keys()) if response.data else 'Tabla vacía'}"
    )

except Exception as e:
    print(f"\n❌ ERROR de conexión: {e}")
    sys.exit(1)
