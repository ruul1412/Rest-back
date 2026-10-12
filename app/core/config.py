from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

class Settings(BaseSettings):
    APP_NAME: str = "Restaurant API"
    DEBUG: bool = True

    # 🔥 usa SOLO UNA fuente de verdad
    DATABASE_URL: str = "postgresql://postgres:201411@localhost:5432/restaurant_db"

    SECRET_KEY: str = "supersecretkey"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 240
    
    PRINTER_IP:   str = "192.168.0.53"
    PRINTER_PORT: int = 9100

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
 


settings = Settings()