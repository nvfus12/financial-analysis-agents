import sys
import os

# Ensure project root is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.api.schemas import HealthCheckResponse
from src.api.routes import analysis, history
from src.infrastructure.database.migrations import run_migrations

# Run database migrations on startup
run_migrations()

logger = logging.getLogger("finanalyst.api")

app = FastAPI(
    title="FinAnalyst Multi-Agent System",
    description="Decoupled HTML5/JS Frontend + FastAPI REST API Backend powered by LangGraph Multi-Agent V2",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(analysis.router)
app.include_router(history.router)

# Create static files directory if not exists
static_dir = os.path.join(root_dir, "static")
os.makedirs(static_dir, exist_ok=True)

# Mount static files directory for CSS and JS assets
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", include_in_schema=False)
async def serve_index():
    """
    Serves the main HTML5 frontend web page.
    """
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "FinAnalyst API Backend is running. Add static/index.html to view web UI."}

@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """
    Backend service health check endpoint.
    """
    return HealthCheckResponse(
        status="healthy",
        service="FinAnalyst Multi-Agent API Engine",
        version="2.0.0"
    )
