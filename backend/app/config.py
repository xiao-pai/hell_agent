import os
import logging
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
dotenv_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=dotenv_path, override=True)

class Settings:
    LLM_MODEL_ID = os.getenv("LLM_MODEL_ID", "deepseek-chat")
    LLM_API_KEY = os.getenv("LLM_API_KEY")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL")

    AMAP_API_KEY = os.getenv("AMAP_API_KEY")
    UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
    MCP_12306_URL = os.getenv("MCP_12306_URL")
    MCP_12306_API_KEY = os.getenv("MCP_12306_API_KEY")

    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))

    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:8000").split(",")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

settings = Settings()

def setup_logging():
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format=log_format,
        handlers=[
            logging.StreamHandler()
        ]
    )
