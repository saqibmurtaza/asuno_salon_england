import httpx, os

async def get_config_from_backend():
     """Fetches configuration data from the FastAPI backend."""
     async with httpx.AsyncClient as cleint:
          backend_url= os.getenv("BACKEND_URL", "http://localhost:8001")
          response= await cleint.get(f"{backend_url}/agent/config")
          response.raise_for_status()
          return response.json()