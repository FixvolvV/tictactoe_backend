from pathlib import Path

from typing import Sequence
from pydantic import (
    BaseModel,
    PostgresDsn
)
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict
)

BASE_DIR = Path(__file__).resolve().parent.parent

class RunConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000
    mode: str = "development"

class GunicornConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    timeout: int = 900

class DataBaseConfig(BaseModel):
    url: PostgresDsn
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 50
    max_overflow: int = 10


class AuthJWTConfig(BaseModel):
    private_key_path: Path = BASE_DIR / "certs" / "jwt-private.pem"
    public_key_path: Path = BASE_DIR / "certs" / "jwt-public.pem"
    algorithm: str = "RS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 5


class HTTPCORS(BaseModel):
    urls: Sequence[str] | None = None


class ApiV1Prefix(BaseModel):
    prefix: str = "/v1"

class ApiPrefix(BaseModel):
    prefix: str = "/api"
    v1: ApiV1Prefix = ApiV1Prefix()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            BASE_DIR / ".env"
        ),
        case_sensitive=False,
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="_",
        env_prefix="APP_"
    )

    run: RunConfig = RunConfig()
    gunicorn: GunicornConfig = GunicornConfig()
    httpcors: HTTPCORS = HTTPCORS()
    api: ApiPrefix = ApiPrefix()
    jwt: AuthJWTConfig = AuthJWTConfig()
    db: DataBaseConfig

settings = Settings() #pyright:ignore