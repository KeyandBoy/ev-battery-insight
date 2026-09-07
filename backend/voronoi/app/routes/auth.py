from flask import Blueprint, request, jsonify

from ..services.auth_service import AuthService
from ..utils.decorators import token_required
from ..utils.validators import validate_register_data, validate_login_data

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '请提供JSON格式的请求数据'}), 400

    errors = validate_register_data(data)
    if errors:
        return jsonify({'success': False, 'message': '; '.join(errors)}), 400

    user, error = AuthService.register(
        username=str(data['username']).strip(),
        email=str(data['email']).strip(),
        password=data['password'],
    )

    if error:
        return jsonify({'success': False, 'message': error}), 409

    token = AuthService.generate_token(user.id)

    return jsonify({
        'success': True,
        'message': '注册成功',
        'data': {
            'user': user.to_dict(),
            'token': token,
        },
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '请提供JSON格式的请求数据'}), 400

    errors = validate_login_data(data)
    if errors:
        return jsonify({'success': False, 'message': '; '.join(errors)}), 400

    user, token, error = AuthService.login(
        username=str(data['username']).strip(),
        password=data['password'],
    )

    if error:
        return jsonify({'success': False, 'message': error}), 401

    return jsonify({
        'success': True,
        'message': '登录成功',
        'data': {
            'user': user.to_dict(),
            'token': token,
        },
    }), 200


@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """获取当前用户资料"""
    return jsonify({
        'success': True,
        'data': current_user.to_dict(),
    }), 200


@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """更新用户资料"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '请提供JSON格式的请求数据'}), 400

    user, error = AuthService.update_profile(current_user.id, data)
    if error:
        return jsonify({'success': False, 'message': error}), 400

    return jsonify({
        'success': True,
        'message': '资料更新成功',
        'data': user.to_dict(),
    }), 200


@auth_bp.route('/password', methods=['PUT'])
@token_required
def change_password(current_user):
    """修改密码"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '请提供JSON格式的请求数据'}), 400

    old_password = data.get('old_password')
    new_password = data.get('new_password')

    if not old_password or not new_password:
        return jsonify({
            'success': False,
            'message': '请提供原密码和新密码',
        }), 400

    if len(new_password) < 6:
        return jsonify({
            'success': False,
            'message': '新密码长度不能少于6位',
        }), 400

    success, error = AuthService.change_password(
        current_user.id, old_password, new_password
    )

    if not success:
        return jsonify({'success': False, 'message': error}), 400

    return jsonify({
        'success': True,
        'message': '密码修改成功',
    }), 200
