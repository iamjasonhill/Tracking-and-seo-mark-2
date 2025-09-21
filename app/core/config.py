from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "SEO Data Sync Platform"

    # The DATABASE_URL is a default value for local development.
    # In a production environment, this should be set via an environment variable.
    DATABASE_URL: str = "postgresql://user:password@localhost/dbname"

    # Celery configuration defaults for local development. Override these values
    # via environment variables in production deployments.
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TIMEZONE: str = "UTC"
    DAILY_SYNC_HOUR: int = 2
    DAILY_SYNC_MINUTE: int = 0

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")


settings = Settings()
