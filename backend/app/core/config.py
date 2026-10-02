from decimal import Decimal
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    DATABASE_URL: str = "sqlite:///./erp.db"
    SECRET_KEY: str = "dev-secret-change-me"
    ACCESS_TOKEN_MINUTES: int = 60
    S3_BUCKET: str = ""
    AWS_REGION: str = "us-east-1"
    IGV_RATE: Decimal = Decimal("0.18")

settings = Settings()
