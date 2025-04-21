import logging
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import os

from app.routes.index_routes import router as index_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Stock Index Analyzer",
    description="A backend service that tracks and manages a custom equal-weighted stock index.",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, you should specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware for request logging and timing
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Process the request
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Request error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(e)},
        )
    
    # Calculate and log request duration
    duration = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {duration:.4f}s")
    
    return response

# Include routers
app.include_router(index_router, tags=["Index"])

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Stock Index Analyzer API",
        "docs": "/docs",
        "version": "1.0.0",
    }

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable or use default
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True) 