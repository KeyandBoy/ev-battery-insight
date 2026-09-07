from datetime import datetime, timedelta, timezone

import jwt
from flask import current_app

from ..extensions import db
from ..models.user import User


class AuthService:
    """用户认证相关业务逻辑"""

    @staticmethod
    def register(username, email, password):
        """
        用户注册。
        返回 (user, error_message)，成功时 error_message 为 None。
        """
        if User.query.filter_by(username=username).first():
            return None, '用户名已存在'

        if User.query.filter_by(email=email).first():
            return None, '邮箱已被注册'

        user = User(username=username, email=email)
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return None, '注册失败，请重试'

        return user, None

    @staticmethod
    def login(username, password):
        """
        用户登录。
        返回 (user, token, error_message)。
        """
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            return None, None, '用户名或密码错误'

        token = AuthService.generate_token(user.id)
        return user, token, None

    @staticmethod
    def generate_token(user_id):
        """生成 JWT Token"""
        expiration_hours = current_app.config.get('JWT_EXPIRATION_HOURS', 24)
        now = datetime.now(timezone.utc)
        payload = {
            'user_id': user_id,
            'exp': now + timedelta(hours=expiration_hours),
            'iat': now,
        }
        return jwt.encode(
            payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256',
        )

    @staticmethod
    def verify_token(token):
        """
        验证 JWT Token。
        返回 (user_id, error_message)。
        兼容多种Token格式: user_id, sub, identity
        """
        print("[DEBUG-2026-05-11] verify_token called - NEW CODE VERSION")
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256'],
            )
            print(f"[DEBUG] Payload keys: {list(payload.keys())}")
            # 兼容多种JWT payload格式
            if 'user_id' in payload:
                print("[DEBUG] Using 'user_id' field")
                return payload['user_id'], None
            elif 'sub' in payload:
                # flask_jwt_extended 标准格式 (subject)
                print(f"[DEBUG] Using 'sub' field: {payload['sub']}")
                try:
                    return int(payload['sub']), None
                except (ValueError, TypeError):
                    return payload['sub'], None
            elif 'identity' in payload:
                # 另一种常见格式
                print(f"[DEBUG] Using 'identity' field: {payload['identity']}")
                try:
                    return int(payload['identity']), None
                except (ValueError, TypeError):
                    return payload['identity'], None
            else:
                # 尝试查找任何可能的用户ID字段
                print("[DEBUG] Trying fallback fields...")
                for key in ['id', 'user_id', 'sub', 'identity', 'userId']:
                    if key in payload:
                        print(f"[DEBUG] Found field '{key}': {payload[key]}")
                        try:
                            return int(payload[key]), None
                        except (ValueError, TypeError):
                            return payload[key], None
                return None, 'Token payload中未找到用户标识'
        except jwt.ExpiredSignatureError:
            return None, 'Token已过期，请重新登录'
        except jwt.InvalidTokenError:
            return None, '无效的Token'

    @staticmethod
    def get_user_by_id(user_id):
        """根据ID获取用户"""
        return db.session.get(User, user_id)

    @staticmethod
    def update_profile(user_id, data):
        """
        更新用户资料。
        返回 (user, error_message)。
        """
        user = db.session.get(User, user_id)
        if user is None:
            return None, '用户不存在'

        if 'email' in data and data['email']:
            existing = User.query.filter(
                User.email == data['email'],
                User.id != user_id,
            ).first()
            if existing:
                return None, '邮箱已被其他用户使用'
            user.email = data['email']

        if 'avatar' in data:
            user.avatar = data['avatar']

        db.session.commit()
        return user, None

    @staticmethod
    def change_password(user_id, old_password, new_password):
        """
        修改密码。
        返回 (success, error_message)。
        """
        user = db.session.get(User, user_id)
        if user is None:
            return False, '用户不存在'

        if not user.check_password(old_password):
            return False, '原密码错误'

        user.set_password(new_password)
        db.session.commit()
        return True, None
