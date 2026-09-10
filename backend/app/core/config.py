from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str

    # Security
    secret_key: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60
    access_token_expiration_days: int = 30

    # URLs
    frontend_url: str = "http://localhost:5173"
    backend_url: str = "http://localhost:8000"

    # Resend
    resend_api_key: str = ""
    resend_from_email: str = "noreply@courrierplus.tn"
    resend_from_name: str = "Courrier+"

    # Payment
    payment_provider: str = "mock"
    payment_api_key: str = ""
    payment_secret: str = ""
    letter_price: float = 15.00
    currency: str = "TND"

    # File uploads
    upload_dir: str = "uploads"
    max_upload_size_mb: int = 10

    # Admin bootstrap
    first_admin_email: str = ""
    first_admin_password: str = ""

    # Misc
    environment: str = "development"
    log_level: str = "INFO"

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def is_email_mock_mode(self) -> bool:
        return not self.resend_api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()
