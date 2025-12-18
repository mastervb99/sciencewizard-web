"""
ScienceWizard - Phase I Static Frontend Server

Minimal server that serves static files.
Will be extended with API endpoints in Phase II.
"""
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(
    title="ScienceWizard",
    description="From Data to Publication in Hours",
    version="0.1.0"
)

# Get the directory where this script is located
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

# Mount static files (CSS, JS)
app.mount("/css", StaticFiles(directory=STATIC_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=STATIC_DIR / "js"), name="js")


@app.get("/")
async def root():
    """Serve the main landing page."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/about.html")
async def about():
    """Serve the about page."""
    return FileResponse(STATIC_DIR / "about.html")


@app.get("/health")
async def health():
    """Health check endpoint for Render."""
    return {"status": "healthy", "phase": "I", "version": "0.1.0"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
