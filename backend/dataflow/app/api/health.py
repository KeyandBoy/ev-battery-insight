from datetime import datetime, timezone

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.get("/health")
def health_check():
    return jsonify(
        {
            "code": 0,
            "message": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
