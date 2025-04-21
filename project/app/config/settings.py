import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Database settings
DB_PATH = os.getenv("DB_PATH", "stock_index.ddb")

# Redis settings
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_EXPIRY = int(os.getenv("REDIS_EXPIRY", 3600))  # 1 hour default cache expiry

# Data acquisition settings
DATA_ACQUISITION_DAYS = int(os.getenv("DATA_ACQUISITION_DAYS", 30))

# API settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("PORT", 8000))

# Application settings
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO") 