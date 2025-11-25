import os
from pathlib import Path

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    # SQLite en carpeta instance
    BASE_DIR = Path(__file__).resolve().parent.parent
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{(BASE_DIR / 'instance' / 'app.db').as_posix()}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de uploads
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(BASE_DIR.parent, "instance", "uploads"))
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB máximo

class DevelopmentConfig(Config):
    """Configuración para desarrollo (SQLite)"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Configuración para producción (PostgreSQL)"""
    DEBUG = False
    TESTING = False
    
    # Usar PostgreSQL en producción
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Render usa postgresql://, pero SQLAlchemy requiere postgresql+psycopg2://
        database_url = database_url.replace("postgresql://", "postgresql+psycopg2://")
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        # Fallback a SQLite si no hay DATABASE_URL
        BASE_DIR = Config.BASE_DIR
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{(BASE_DIR / 'instance' / 'app.db').as_posix()}"

class TestingConfig(Config):
    """Configuración para testing"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
