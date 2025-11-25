import os
from pathlib import Path

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    # SQLite en carpeta instance
    BASE_DIR = Path(__file__).resolve().parent.parent
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{(BASE_DIR / 'instance' / 'app.db').as_posix()}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
