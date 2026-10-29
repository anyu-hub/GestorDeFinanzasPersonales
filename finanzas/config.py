import os
from pathlib import Path
import secrets


BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
    DATABASE = BASE_DIR / "finanzas.db"
    TEMPLATES_AUTO_RELOAD = True
