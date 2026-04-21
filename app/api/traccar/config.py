from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    TRACCAR_URL: str
    TRACCAR_USERNAME: str
    TRACCAR_PASSWORD: str

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
