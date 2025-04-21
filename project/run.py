import uvicorn
import os
from app.config.settings import API_HOST, API_PORT, DEBUG

if __name__ == "__main__":
    print(f"Starting Stock Index Analyzer API on http://{API_HOST}:{API_PORT}")
    uvicorn.run("app.main:app", host=API_HOST, port=API_PORT, reload=DEBUG) 