import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Calculate the absolute path to the root directory where '.env' resides
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
dotenv_path = os.path.join(base_dir, ".env")

# Force-load the environment variables from the calculated path
load_dotenv(dotenv_path)

class Settings(BaseSettings):
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
    GEMINI_MODEL: str = "gemini-2.5-flash"

    class Config:
        extra = "ignore"

settings = Settings()