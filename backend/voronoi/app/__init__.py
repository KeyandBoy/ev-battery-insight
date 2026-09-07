import os

from flask import Flask, jsonify

from .config import config
from .extensions import db, cors


def create_app(config_name=None):
    """Flask 应用工厂函数"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))

    _init_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _create_database(app)

    return app


def _init_extensions(app):
    """初始化 Flask 扩展"""
    db.init_app(app)
    cors.init_app(app, resources={r'/api/*': {'origins': '*'}})

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def _register_blueprints(app):
    """注册所有蓝图"""
    from .routes import register_blueprints
    register_blueprints(app)


def _register_error_handlers(app):
    """注册全局错误处理器"""

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({
            'success': False,
            'message': '请求参数错误',
        }), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({
            'success': False,
            'message': '请求的资源不存在',
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({
            'success': False,
            'message': '请求方法不被允许',
        }), 405

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return jsonify({
            'success': False,
            'message': '上传文件大小超过限制（最大16MB）',
        }), 413

    @app.errorhandler(500)
    def internal_server_error(e):
        response = {'success': False, 'message': '服务器内部错误'}
        if app.debug:
            response['error'] = str(e)
        return jsonify(response), 500


def _create_database(app):
    """创建数据库表"""
    with app.app_context():
        from .models import User, Dataset  # noqa: F401
        db.create_all()
