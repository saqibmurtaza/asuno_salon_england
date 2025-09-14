from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Supabase Credentials
    NEXT_PUBLIC_SUPABASE_URL: str
    NEXT_PUBLIC_SUPABASE_ANON_KEY: str
    SUPABASE_SECRET_KEY: str # This is crucial for server-side
    DIRECT_URL: str

    # LLM / API credentials
    MODEL_NAME: str
    API_KEY: str

    # Secret for signing / security
    API_SECRET_KEY: str

    # Frontend/backend URLs
    BACKEND_URL: str | None = None

settings = Settings()
