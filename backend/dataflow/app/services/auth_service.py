from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import User, UserProfile


class AuthValidationError(ValueError):
    pass


def _normalize_username(username):
    return (username or "").strip()


def validate_register_payload(payload):
    username = _normalize_username(payload.get("username"))
    password = (payload.get("password") or "").strip()
    email = (payload.get("email") or "").strip() or None

    if len(username) < 3 or len(username) > 50:
        raise AuthValidationError("用户名长度需在 3 到 50 之间。")
    if len(password) < 6:
        raise AuthValidationError("密码长度不能少于 6 位。")
    if email and len(email) > 100:
        raise AuthValidationError("邮箱长度不能超过 100。")

    return username, password, email


def create_user(username, password, email=None):
    exists = User.query.filter_by(username=username).first()
    if exists:
        raise AuthValidationError("用户名已存在。")

    user = User(
        username=username,
        password_hash=hash_password(password),
        email=email,
        status=1,
    )
    return user


def verify_login(username, password):
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        raise AuthValidationError("用户名或密码错误。")
    if int(user.status or 0) != 1:
        raise AuthValidationError("用户已被禁用。")
    return user


def validate_password_change(old_password, new_password):
    old_password = (old_password or "").strip()
    new_password = (new_password or "").strip()

    if len(old_password) < 6 or len(new_password) < 6:
        raise AuthValidationError("旧密码和新密码长度都不能少于 6 位。")
    if old_password == new_password:
        raise AuthValidationError("新密码不能和旧密码相同。")

    return old_password, new_password


def hash_password(password):
    return generate_password_hash(password)


def ensure_user_profile(user):
    if user.profile is not None:
        return user.profile

    profile = UserProfile(
        user_id=user.id,
        display_name=user.username,
    )
    db.session.add(profile)
    db.session.flush()
    return profile


def validate_profile_payload(payload):
    username = payload.get("username")
    display_name = payload.get("display_name")
    email = payload.get("email")
    bio = payload.get("bio")
    avatar_url = payload.get("avatar_url")

    if username is not None:
        username = (username or "").strip()
        if len(username) < 3 or len(username) > 50:
            raise AuthValidationError("用户名长度需在 3 到 50 之间。")

    if display_name is not None:
        display_name = (display_name or "").strip()
        if len(display_name) > 50:
            raise AuthValidationError("显示名称长度不能超过 50。")

    if email is not None:
        email = (email or "").strip() or None
        if email and len(email) > 100:
            raise AuthValidationError("邮箱长度不能超过 100。")

    if bio is not None:
        bio = (bio or "").strip() or None
        if bio and len(bio) > 255:
            raise AuthValidationError("个人简介长度不能超过 255。")

    if avatar_url is not None:
        avatar_url = (avatar_url or "").strip() or None
        if avatar_url and len(avatar_url) > 255:
            raise AuthValidationError("头像地址长度不能超过 255。")

    return {
        "username": username,
        "display_name": display_name,
        "email": email,
        "bio": bio,
        "avatar_url": avatar_url,
    }


def apply_profile_update(user, profile_fields):
    if profile_fields["username"] is not None and profile_fields["username"] != user.username:
        exists = User.query.filter(User.username == profile_fields["username"], User.id != user.id).first()
        if exists:
            raise AuthValidationError("用户名已存在。")
        user.username = profile_fields["username"]

    if profile_fields["email"] is not None:
        user.email = profile_fields["email"]

    profile = ensure_user_profile(user)
    if profile_fields["display_name"] is not None:
        profile.display_name = profile_fields["display_name"]
    if profile_fields["bio"] is not None:
        profile.bio = profile_fields["bio"]
    if profile_fields["avatar_url"] is not None:
        profile.avatar_url = profile_fields["avatar_url"]

    return user
