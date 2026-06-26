import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Ensure the root project path is in the sys.path for importing shared package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.routes import tasks, health

app = FastAPI(
    title="Multi-Agent Anomaly Detection API",
    description="REST API to coordinate task assignments and track execution telemetry.",
    version="1.0"
)

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(tasks.router)
app.include_router(health.router)

# Resolve absolute path to static directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_dir = os.path.join(project_root, "static")

# Serve index.html at root
@app.get("/")
def read_root():
    return FileResponse(os.path.join(static_dir, "index.html"))

# Serve other static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

