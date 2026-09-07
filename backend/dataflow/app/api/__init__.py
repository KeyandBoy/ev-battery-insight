from app.api.analysis import analysis_bp
from app.api.auth import auth_bp
from app.api.dashboard import dashboard_bp
from app.api.dataset import dataset_bp
from app.api.health import health_bp


def register_api_blueprints(app):
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dataset_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(dashboard_bp)
