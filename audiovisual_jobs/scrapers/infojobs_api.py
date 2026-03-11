import os
import httpx
import logging

logger = logging.getLogger(__name__)

class InfoJobsAPIClient:
    """
    Cliente para la API oficial de InfoJobs.
    Requiere registrarse en https://developer.infojobs.net/ y obtener Credenciales (Client ID y Client Secret).
    """
    def __init__(self):
        self.client_id = os.getenv("INFOJOBS_CLIENT_ID")
        self.client_secret = os.getenv("INFOJOBS_CLIENT_SECRET")
        self.base_url = "https://api.infojobs.net/api/9/offer"
        
        if not self.client_id or not self.client_secret:
            logger.warning("Faltan INFOJOBS_CLIENT_ID o INFOJOBS_CLIENT_SECRET en .env")

    async def search_offers(self, query: str = "audiovisual", category: str = "", province: str = ""):
        """Busca ofertas usando Basic Auth con Client ID/Client Secret."""
        if not self.client_id or not self.client_secret:
            return []
            
        auth = (self.client_id, self.client_secret)
        params = {"q": query, "maxResults": 50}
        
        if category:
            params["category"] = category
        if province:
            params["province"] = province
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, auth=auth, params=params, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                ofertas = []
                for item in data.get("items", []):
                    ofertas.append({
                        "id_oferta": item.get("id"),
                        "titulo_puesto": item.get("title"),
                        "empresa": item.get("author", {}).get("name", "Desconocida"),
                        "ubicacion": item.get("province", {}).get("value", "España"),
                        "enlace_fuente": item.get("link"),
                        "fuente": "InfoJobs API",
                        "dominio_fuente": "infojobs.net",
                        "descripcion_original": item.get("requirementMin", "") + " " + item.get("study", {}).get("value", ""),
                        "es_casting": False,
                    })
                return ofertas
        except Exception as e:
            logger.error(f"Error en API InfoJobs: {e}")
            return []
