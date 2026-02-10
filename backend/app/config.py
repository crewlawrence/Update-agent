from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "Client Update Agent"
    debug: bool = False
    secret_key: str = "change-me-in-production-use-env"

    # Database (multi-tenant: one DB, tenant_id on tables)
    database_url: str = "sqlite:///./app.db"

    # Auth: short-lived access token, refresh in HttpOnly cookie with DB rotation
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 15  # short-lived access token
    refresh_cookie_name: str = "refresh_token"
    refresh_cookie_max_age_days: int = 7
    cookie_secure: bool = False  # set True in production (HTTPS)
    cookie_same_site: str = "lax"

    # QuickBooks OAuth (from developer.intuit.com)
    qb_client_id: str = ""
    qb_client_secret: str = ""
    qb_redirect_uri: str = "http://localhost:8000/api/qb/callback"
    qb_environment: str = "sandbox"  # sandbox | production

    # OpenAI (for Agno agent)
    openai_api_key: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
