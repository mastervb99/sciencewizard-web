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

        # Token management tables
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_tokens (
                user_id TEXT PRIMARY KEY,
                balance INTEGER DEFAULT 0,
                total_purchased INTEGER DEFAULT 0,
                last_updated TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS token_transactions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL,
                amount INTEGER NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Referral system tables
        await db.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                id TEXT PRIMARY KEY,
                referrer_user_id TEXT NOT NULL,
                referral_code TEXT UNIQUE NOT NULL,
                referee_email TEXT,
                referee_user_id TEXT,
                tokens_awarded INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (referrer_user_id) REFERENCES users(id),
                FOREIGN KEY (referee_user_id) REFERENCES users(id)
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


# Token operations
async def get_user_tokens(db, user_id: str):
    cursor = await db.execute("SELECT * FROM user_tokens WHERE user_id = ?", (user_id,))
    row = await cursor.fetchone()
    if row:
        return dict(row)
    else:
        # Create initial token balance
        await db.execute(
            "INSERT INTO user_tokens (user_id, balance, total_purchased, last_updated) VALUES (?, 0, 0, ?)",
            (user_id, datetime.utcnow().isoformat())
        )
        await db.commit()
        return {"user_id": user_id, "balance": 0, "total_purchased": 0}


async def add_tokens(db, user_id: str, amount: int, transaction_type: str, description: str):
    # Add token transaction
    import uuid
    transaction_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO token_transactions (id, user_id, type, amount, description, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (transaction_id, user_id, transaction_type, amount, description, datetime.utcnow().isoformat())
    )

    # Update user balance
    await db.execute(
        "UPDATE user_tokens SET balance = balance + ?, last_updated = ? WHERE user_id = ?",
        (amount, datetime.utcnow().isoformat(), user_id)
    )

    # Update total purchased if it's a purchase
    if transaction_type == "purchase":
        await db.execute(
            "UPDATE user_tokens SET total_purchased = total_purchased + ? WHERE user_id = ?",
            (amount, user_id)
        )

    await db.commit()


async def consume_tokens(db, user_id: str, amount: int, description: str):
    # Check if user has enough tokens
    user_tokens = await get_user_tokens(db, user_id)
    if user_tokens["balance"] < amount:
        return False

    # Deduct tokens
    await add_tokens(db, user_id, -amount, "consumption", description)
    return True


async def get_token_transactions(db, user_id: str, limit: int = 20):
    cursor = await db.execute(
        "SELECT * FROM token_transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit)
    )
    return await cursor.fetchall()


# Referral operations
async def create_referral(db, referrer_user_id: str, referral_code: str):
    import uuid
    referral_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO referrals (id, referrer_user_id, referral_code, created_at) VALUES (?, ?, ?, ?)",
        (referral_id, referrer_user_id, referral_code, datetime.utcnow().isoformat())
    )
    await db.commit()
    return referral_id


async def get_referral_by_code(db, referral_code: str):
    cursor = await db.execute("SELECT * FROM referrals WHERE referral_code = ?", (referral_code,))
    return await cursor.fetchone()


async def get_user_referral_code(db, user_id: str):
    cursor = await db.execute("SELECT referral_code FROM referrals WHERE referrer_user_id = ? LIMIT 1", (user_id,))
    return await cursor.fetchone()


async def record_referral_signup(db, referral_code: str, referee_user_id: str):
    await db.execute(
        "UPDATE referrals SET referee_user_id = ? WHERE referral_code = ?",
        (referee_user_id, referral_code)
    )
    await db.commit()


async def award_referral_tokens(db, referral_code: str):
    # Get referral info
    referral = await get_referral_by_code(db, referral_code)
    if not referral or referral["referee_user_id"] is None or referral["tokens_awarded"] > 0:
        return False

    # Award 25 tokens to referrer
    await add_tokens(db, referral["referrer_user_id"], 25, "referral_bonus",
                     f"Referral bonus for {referral['referee_user_id']}")

    # Mark as awarded
    await db.execute(
        "UPDATE referrals SET tokens_awarded = 25 WHERE referral_code = ?",
        (referral_code,)
    )
    await db.commit()
    return True


async def send_referral_invitation(db, referrer_user_id: str, referee_email: str):
    # Get or create referral code for user
    referral = await get_user_referral_code(db, referrer_user_id)
    if not referral:
        # Generate new referral code
        import random, string
        referral_code = f"VR-{referrer_user_id[:3].upper()}{random.randint(100, 999)}"
        await create_referral(db, referrer_user_id, referral_code)
    else:
        referral_code = referral["referral_code"]

    # Record the email invitation
    await db.execute(
        "UPDATE referrals SET referee_email = ? WHERE referral_code = ?",
        (referee_email, referral_code)
    )
    await db.commit()

    return referral_code
