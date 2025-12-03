from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    pg_host: str
    pg_user: str
    pg_password: str
    pg_db: str
    pg_port: int

    redis_host: str
    redis_port: int
    redis_password: str

    model_config = SettingsConfigDict(env_file=".env.local")

settings = Settings()
