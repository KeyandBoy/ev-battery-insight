import re
import time
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, g, request
from flask_cors import CORS
from sqlalchemy import inspect, text
from flask_jwt_extended import JWTManager

from app.api import register_api_blueprints
from app.config import get_config
from app.errors import register_error_handlers
from app.extensions import db, migrate
from app.logging_config import configure_logging


def _ensure_runtime_schema(app):
    with app.app_context():
        inspector = inspect(db.engine)
        if not inspector.has_table("users"):
            app.logger.info("Tables not found, creating schema...")
            db.create_all()


def _register_request_logging(app):
    @app.before_request
    def start_timer():
        g._start_time = time.perf_counter()

    @app.after_request
    def log_request(response):
        if re.match(r"^/api/", request.path):
            elapsed_ms = (time.perf_counter() - g._start_time) * 1000
            app.logger.info(f"{request.method} {request.path} -> {response.status_code} ({elapsed_ms:.2f} ms)")
        return response


def create_app(config_name=None):
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    # Import models before schema inspection so metadata is complete.
    from app import models  # noqa: F401

    configure_logging(app)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize JWT with error handlers
    jwt = JWTManager(app)
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        app.logger.error(f"[JWT ERROR] Invalid token: {error_string}")
        return {"code": 422, "message": f"Invalid token: {error_string}"}, 422
    
    @jwt.unauthorized_loader
    def unauthorized_callback(error_string):
        app.logger.error(f"[JWT ERROR] Unauthorized: {error_string}")
        return {"code": 401, "message": f"Unauthorized: {error_string}"}, 401
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        app.logger.error(f"[JWT ERROR] Token expired")
        return {"code": 401, "message": "Token has expired"}, 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        app.logger.error(f"[JWT ERROR] Token revoked")
        return {"code": 401, "message": "Token has been revoked"}, 401
    
    _ensure_runtime_schema(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    _register_request_logging(app)
    register_error_handlers(app)
    register_api_blueprints(app)

    return app