from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    supabase_url: str
    supabase_service_role_key: str
    database_url: str | None = None

    mail_username: str | None = None
    mail_password: str | None = None
    mail_from: str | None = None
    mail_server: str = "smtp.gmail.com"
    mail_port: int = 587
    mail_from_name: str = "COM/VERGE"
    mail_starttls: bool = True
    mail_ssl_tls: bool = False

    admin_email: str = "comverge@rived.community"
    allowed_origins: str = "http://localhost:3000,https://comverge.rived.community,https://*.vercel.app"
    rate_limit_per_minute: int = 5

    class Config:
        env_file = str(Path(__file__).resolve().parent.parent / ".env")
        case_sensitive = False

    @property
    def allowed_origins_list(self) -> List[str]:
        return [item.strip() for item in self.allowed_origins.split(",") if item.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
