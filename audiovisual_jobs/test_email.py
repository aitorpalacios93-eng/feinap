import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

load_dotenv(BASE_DIR / ".env")

import logging
from db.connection import get_supabase_client
from db.queries import get_ofertas_hoy
from notifications.email_sender import enviar_email_ofertas

logging.basicConfig(level=logging.INFO)

def test_enviar_email():
    client = get_supabase_client()
    ofertas_hoy = get_ofertas_hoy(client)
    
    # Podemos limitar a unas pocas para el test
    print(f"Obtenidas {len(ofertas_hoy)} ofertas. Enviando email de prueba...")
    enviar_email_ofertas(ofertas_hoy[:15])

if __name__ == "__main__":
    test_enviar_email()
