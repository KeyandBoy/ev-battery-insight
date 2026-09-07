from __future__ import annotations

from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from config import Config
from database import db
from routes.analysis import analysis_bp
from routes.datasets import datasets_bp
from routes.health import health_bp
from services.dataset_service import ensure_data_directories


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)
    db.init_app(app)
    ensure_data_directories()

    app.register_blueprint(health_bp)
    app.register_blueprint(datasets_bp)
    app.register_blueprint(analysis_bp)

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"message": "资源不存在。"}), 404

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        return jsonify({"message": error.description}), error.code

    @app.errorhandler(Exception)
    def handle_error(error):
        app.logger.exception(error)
        return jsonify({"message": "服务器内部处理失败，请检查参数或稍后重试。"}), 500

    return app


app = create_app()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5002, debug=False)
