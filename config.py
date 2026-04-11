import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "nurse-inventory-secret-key")
    # Use DATABASE_URL env var (PostgreSQL on Render/Neon), fallback to SQLite for local dev
    database_url = os.environ.get("DATABASE_URL", "")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = database_url or "sqlite:///" + os.path.join(BASE_DIR, "instance", "inventory.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "images")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB
