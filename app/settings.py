from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    SECRET_KEY: str = "c1591e1c961c5da73be50b329c8390a2ec7d38c3e5615152ec10f4c0202fbaa4"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

settings = Settings()
