"""
Velvet Research - Configuration
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # JWT
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./velvet.db")

    # File storage
    upload_dir: str = os.getenv("UPLOAD_DIR", "/tmp/velvet_uploads")
    report_dir: str = os.getenv("REPORT_DIR", "/tmp/velvet_reports")
    max_file_size_mb: int = 50
    max_upload_size_mb: int = 100
    allowed_extensions: set = {".csv", ".xlsx", ".xls", ".docx", ".pdf", ".txt"}

    # API
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Science Wizard project path
    science_wizard_path: str = os.getenv(
        "SCIENCE_WIZARD_PATH",
        "/Users/vafabayat/Dropbox/Financial/0ScienceWizard/science_wizard_project"
    )

    # Server
    port: int = int(os.getenv("PORT", 8000))
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    class Config:
        env_file = ".env"


settings = Settings()
