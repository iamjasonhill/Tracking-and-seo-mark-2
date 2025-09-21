from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "SEO Data Sync Platform"

    # The DATABASE_URL is a default value for local development.
    # In a production environment, this should be set via an environment variable.
    DATABASE_URL: str = "postgresql://user:password@localhost/dbname"

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
