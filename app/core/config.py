from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Config API
    PROJECT_NAME: str = "Gym Management API"
    VERSEION: str = '1.0.0'

    # Config database
    DATABASE_URL: str

    # Config of Security (JWT)
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Pydantic configuration to read the .env file
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=True
    )

# Global instance to be imported into the rest of the project
settings = Settings()