"""
Velvet Research - Main FastAPI Server

Phase 1-3 Implementation for Render Professional
"""
import os
import sys
import uuid
import json
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings
from database import (
    init_db, get_db,
    create_user, get_user_by_email, get_user_by_id,
    create_upload, get_upload,
    create_job, update_job_status, get_job, get_user_jobs
)
from services.auth import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    hash_password, verify_password, create_access_token,
    get_current_user, generate_user_id
)
from services.upload import save_uploaded_files, get_upload_files
from services.report_generator import run_generation_job, get_job_progress


# Lifespan for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.report_dir).mkdir(parents=True, exist_ok=True)
    yield
    # Shutdown


app = FastAPI(
    title="Velvet Research",
    description="AI-Powered Research Manuscript Generation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

app.mount("/css", StaticFiles(directory=STATIC_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=STATIC_DIR / "js"), name="js")


# ============================================================================
# Static Pages
# ============================================================================

@app.get("/")
async def root():
    """Serve the main landing page."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/about.html")
async def about():
    """Serve the about page."""
    return FileResponse(STATIC_DIR / "about.html")


@app.get("/review.html")
async def review():
    """Serve the review page."""
    return FileResponse(STATIC_DIR / "review.html")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0", "plan": "professional"}


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/api/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    """Register a new user."""
    async for db in get_db():
        # Check if email exists
        existing = await get_user_by_email(db, user_data.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create user
        user_id = generate_user_id()
        password_hash = hash_password(user_data.password)
        await create_user(db, user_id, user_data.email, password_hash)

        # Generate token
        token = create_access_token(user_id, user_data.email)

        # Get user for response
        user = await get_user_by_id(db, user_id)

        return TokenResponse(
            access_token=token,
            user=UserResponse(
                id=user["id"],
                email=user["email"],
                created_at=user["created_at"]
            )
        )


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Login and get access token."""
    async for db in get_db():
        user = await get_user_by_email(db, credentials.email)

        if not user or not verify_password(credentials.password, user["password_hash"]):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        token = create_access_token(user["id"], user["email"])

        return TokenResponse(
            access_token=token,
            user=UserResponse(
                id=user["id"],
                email=user["email"],
                created_at=user["created_at"]
            )
        )


@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info."""
    async for db in get_db():
        user = await get_user_by_id(db, current_user["id"])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return UserResponse(
            id=user["id"],
            email=user["email"],
            created_at=user["created_at"]
        )


# ============================================================================
# File Upload Endpoints
# ============================================================================

class UploadResponse(BaseModel):
    upload_id: str
    files: List[dict]


@app.post("/api/upload", response_model=UploadResponse)
async def upload_files(
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload research files."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    upload_id, upload_path, file_list = await save_uploaded_files(
        current_user["id"],
        files
    )

    # Save to database
    async for db in get_db():
        await create_upload(db, upload_id, current_user["id"], json.dumps(file_list), upload_path)

    return UploadResponse(upload_id=upload_id, files=file_list)


@app.get("/api/upload/{upload_id}")
async def get_upload_info(
    upload_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get upload info."""
    async for db in get_db():
        upload = await get_upload(db, upload_id)

        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")

        if upload["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        return {
            "upload_id": upload["id"],
            "files": json.loads(upload["files"]),
            "created_at": upload["created_at"]
        }


# ============================================================================
# Report Generation Endpoints
# ============================================================================

class GenerateRequest(BaseModel):
    upload_id: str
    project_type: Optional[str] = "manuscript"


class JobResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    error: Optional[str] = None
    report_path: Optional[str] = None


@app.post("/api/generate", response_model=JobResponse)
async def generate_report(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Start report generation job."""
    async for db in get_db():
        # Verify upload exists and belongs to user
        upload = await get_upload(db, request.upload_id)

        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")

        if upload["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Create job
        job_id = str(uuid.uuid4())
        await create_job(db, job_id, current_user["id"], request.upload_id)

        # Output directory
        output_dir = Path(settings.report_dir) / current_user["id"] / job_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Define callback for progress updates
        async def update_callback(jid, status, progress, error=None, report_path=None):
            async for db in get_db():
                await update_job_status(db, jid, status, progress, error, report_path)

        # Start background task
        background_tasks.add_task(
            run_generation_job,
            job_id,
            upload["upload_path"],
            str(output_dir),
            update_callback
        )

        return JobResponse(
            job_id=job_id,
            status="processing",
            progress=0.0
        )


@app.get("/api/status/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get job status."""
    async for db in get_db():
        job = await get_job(db, job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Get live progress if job is running
        live_progress = get_job_progress(job_id)
        progress = live_progress if live_progress is not None else job["progress"]

        return JobResponse(
            job_id=job["id"],
            status=job["status"],
            progress=progress,
            error=job["error"],
            report_path=job["report_path"]
        )


@app.get("/api/jobs")
async def list_jobs(current_user: dict = Depends(get_current_user)):
    """List user's jobs."""
    async for db in get_db():
        jobs = await get_user_jobs(db, current_user["id"])

        return [
            {
                "job_id": job["id"],
                "status": job["status"],
                "progress": job["progress"],
                "created_at": job["created_at"],
                "completed_at": job["completed_at"]
            }
            for job in jobs
        ]


# ============================================================================
# Download Endpoint
# ============================================================================

@app.get("/api/download/{job_id}")
async def download_report(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Download generated report."""
    async for db in get_db():
        job = await get_job(db, job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        if job["status"] != "completed":
            raise HTTPException(status_code=400, detail="Report not ready")

        if not job["report_path"] or not Path(job["report_path"]).exists():
            raise HTTPException(status_code=404, detail="Report file not found")

        return FileResponse(
            job["report_path"],
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="velvet_research_manuscript.docx"
        )


# ============================================================================
# Feedback Endpoints (Phase 2)
# ============================================================================

class FeedbackRequest(BaseModel):
    section: str
    approved: bool
    comments: Optional[List[str]] = None


@app.post("/api/feedback/{job_id}")
async def submit_feedback(
    job_id: str,
    feedback: FeedbackRequest,
    current_user: dict = Depends(get_current_user)
):
    """Submit section feedback (Phase 2)."""
    async for db in get_db():
        job = await get_job(db, job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Store feedback
        feedback_id = str(uuid.uuid4())
        await db.execute(
            """INSERT INTO feedback (id, job_id, section, approved, comments, created_at)
               VALUES (?, ?, ?, ?, ?, datetime('now'))""",
            (feedback_id, job_id, feedback.section, 1 if feedback.approved else 0,
             json.dumps(feedback.comments) if feedback.comments else None)
        )
        await db.commit()

        return {"status": "ok", "feedback_id": feedback_id}


@app.post("/api/regenerate/{job_id}")
async def regenerate_report(
    job_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Regenerate report with feedback (Phase 2)."""
    async for db in get_db():
        job = await get_job(db, job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Create new job
        new_job_id = str(uuid.uuid4())
        await create_job(db, new_job_id, current_user["id"], job["upload_id"])

        # Get upload for path
        upload = await get_upload(db, job["upload_id"])

        output_dir = Path(settings.report_dir) / current_user["id"] / new_job_id
        output_dir.mkdir(parents=True, exist_ok=True)

        async def update_callback(jid, status, progress, error=None, report_path=None):
            async for db in get_db():
                await update_job_status(db, jid, status, progress, error, report_path)

        background_tasks.add_task(
            run_generation_job,
            new_job_id,
            upload["upload_path"],
            str(output_dir),
            update_callback
        )

        return {"job_id": new_job_id, "status": "processing"}


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
