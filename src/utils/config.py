from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding="utf-8",
        extra="ignore"
    )

    SECRET_JWT: str
    SECRET_JWT_ALGORITHM: str

    HTTP_CORS: str

    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    def get_db_url(self):
        return (f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}")

    def get_jwt_conf(self):
        return {"token": self.SECRET_JWT, "token_type": self.SECRET_JWT_ALGORITHM}

    def get_cors_conf(self):
        return {"http_cors": self.HTTP_CORS}


settings = Settings() #pyright:ignore
