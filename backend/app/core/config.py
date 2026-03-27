from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Cardiac Exercise Prescriber"
    DATABASE_URL: str = "sqlite:///./database.db"
    
    SECRET_KEY: str = "replace-this-with-a-secure-random-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    class Config:
        env_file = ".env"

settings = Settings()