import os
from datetime import timedelta
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def _parse_csv_env(value, default):
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_positive_int_env(name, default):
    raw = os.getenv(name)
    if raw is None or str(raw).strip() == "":
        return int(default)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return int(default)
    if value <= 0:
        return int(default)
    return value


def _normalize_database_uri(default_uri):
    database_uri = (os.getenv("DATABASE_URL") or default_uri or "").strip()
    if not database_uri.startswith("mysql"):
        return database_uri

    parts = urlsplit(database_uri)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    if not query.get("charset"):
        query["charset"] = "utf8mb4"

    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
    )


def _build_engine_options(database_uri):
    options = {
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
        "pool_recycle": 1800,
    }
    if database_uri.startswith("mysql"):
        options["pool_recycle"] = 1800
    return options


class BaseConfig:
    # Keep MySQL charset explicit so 5.7 and 8.0 behave the same.
    SQLALCHEMY_DATABASE_URI = _normalize_database_uri(
        "mysql+pymysql://root:YOUR_PASSWORD@127.0.0.1:3306/dataflow_canvas?charset=utf8mb4"
    )
    SQLALCHEMY_ENGINE_OPTIONS = _build_engine_options(SQLALCHEMY_DATABASE_URI)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "change-me-in-env",
    )
    JWT_ERROR_MESSAGE_KEY = "message"
    # Default to 7 days to reduce frequent 401s while editing dashboards.
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=_parse_positive_int_env("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", 7 * 24 * 60)
    )
    CORS_ORIGINS = _parse_csv_env(os.getenv("CORS_ORIGINS"), ["http://localhost:5175", "http://localhost:5173", "http://localhost:3001", "http://127.0.0.1:3001", "http://127.0.0.1:5000"])
    JSON_AS_ASCII = False
    UPLOAD_ROOT = os.getenv("UPLOAD_ROOT", "uploads")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 20 * 1024 * 1024))


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(BaseConfig):
    DEBUG = False


_CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(config_name=None):
    runtime_name = config_name or os.getenv("FLASK_ENV", "development")
    return _CONFIG_MAP.get(runtime_name, DevelopmentConfig)
