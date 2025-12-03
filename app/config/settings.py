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

    @property
    def pg_url(self):
        return f"postgresql+psycopg2://{self.pg_user}:{self.pg_password}@{self.pg_host}:{self.pg_port}/{self.pg_db}"

    @property
    def redis_url(self):
        return f"redis://{self.redis_host}:{self.redis_port}"

    model_config = SettingsConfigDict(env_file=".env.local")

settings = Settings()
