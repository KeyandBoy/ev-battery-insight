from .auth import auth_bp
from .dataset import dataset_bp
from .analysis import analysis_bp


def register_blueprints(app):
    """注册所有蓝图到 Flask 应用"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(dataset_bp)
    app.register_blueprint(analysis_bp)
