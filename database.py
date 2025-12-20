"""
Velvet Research - Database Models and Setup
"""
import aiosqlite
from datetime import datetime
from pathlib import Path
from config import settings

DATABASE_PATH = Path(settings.database_url.replace("sqlite+aiosqlite:///", ""))


async def init_db():
    """Initialize database tables."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        """)

        # Uploads table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS uploads (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                files TEXT NOT NULL,
                upload_path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Jobs table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                upload_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                progress REAL DEFAULT 0.0,
                error TEXT,
                report_path TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (upload_id) REFERENCES uploads(id)
            )
        """)

        # Feedback table (Phase 2)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                section TEXT NOT NULL,
                approved INTEGER NOT NULL,
                comments TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (job_id) REFERENCES jobs(id)
            )
        """)

        await db.commit()


async def get_db():
    """Get database connection."""
    db = await aiosqlite.connect(DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()


# User operations
async def create_user(db, user_id: str, email: str, password_hash: str):
    await db.execute(
        "INSERT INTO users (id, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
        (user_id, email, password_hash, datetime.utcnow().isoformat())
    )
    await db.commit()


async def get_user_by_email(db, email: str):
    cursor = await db.execute("SELECT * FROM users WHERE email = ?", (email,))
    return await cursor.fetchone()


async def get_user_by_id(db, user_id: str):
    cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return await cursor.fetchone()


# Upload operations
async def create_upload(db, upload_id: str, user_id: str, files: str, upload_path: str):
    await db.execute(
        "INSERT INTO uploads (id, user_id, files, upload_path, created_at) VALUES (?, ?, ?, ?, ?)",
        (upload_id, user_id, files, upload_path, datetime.utcnow().isoformat())
    )
    await db.commit()


async def get_upload(db, upload_id: str):
    cursor = await db.execute("SELECT * FROM uploads WHERE id = ?", (upload_id,))
    return await cursor.fetchone()


# Job operations
async def create_job(db, job_id: str, user_id: str, upload_id: str):
    await db.execute(
        "INSERT INTO jobs (id, user_id, upload_id, status, created_at) VALUES (?, ?, ?, 'pending', ?)",
        (job_id, user_id, upload_id, datetime.utcnow().isoformat())
    )
    await db.commit()


async def update_job_status(db, job_id: str, status: str, progress: float = None,
                            error: str = None, report_path: str = None):
    updates = ["status = ?"]
    params = [status]

    if progress is not None:
        updates.append("progress = ?")
        params.append(progress)
    if error is not None:
        updates.append("error = ?")
        params.append(error)
    if report_path is not None:
        updates.append("report_path = ?")
        params.append(report_path)
    if status == "completed" or status == "failed":
        updates.append("completed_at = ?")
        params.append(datetime.utcnow().isoformat())

    params.append(job_id)
    await db.execute(f"UPDATE jobs SET {', '.join(updates)} WHERE id = ?", params)
    await db.commit()


async def get_job(db, job_id: str):
    cursor = await db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    return await cursor.fetchone()


async def get_user_jobs(db, user_id: str):
    cursor = await db.execute(
        "SELECT * FROM jobs WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    return await cursor.fetchall()
