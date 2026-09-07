from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
GENERATED_DIR = DATA_DIR / "generated"


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dbscan-region-visual-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:YOUR_PASSWORD@127.0.0.1:3306/highdim_region_vis?charset=utf8mb4",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_AS_ASCII = False
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    DATA_DIR = DATA_DIR
    UPLOAD_DIR = UPLOAD_DIR
    GENERATED_DIR = GENERATED_DIR
