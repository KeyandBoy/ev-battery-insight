from functools import wraps

from flask import request, jsonify

from ..services.auth_service import AuthService


def token_required(f):
    """JWT Token 认证装饰器，注入 current_user 到视图函数"""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        auth_header = request.headers.get('Authorization')
        if auth_header:
            parts = auth_header.split(' ')
            if len(parts) == 2 and parts[0] == 'Bearer':
                token = parts[1]

        if not token:
            return jsonify({
                'success': False,
                'message': '缺少认证Token，请先登录',
            }), 401

        user_id, error = AuthService.verify_token(token)
        if error:
            return jsonify({'success': False, 'message': error}), 401

        current_user = AuthService.get_user_by_id(user_id)
        if not current_user:
            return jsonify({'success': False, 'message': '用户不存在'}), 401

        return f(current_user, *args, **kwargs)

    return decorated
