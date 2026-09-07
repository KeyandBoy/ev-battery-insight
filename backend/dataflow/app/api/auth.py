import os
import time
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, request, send_from_directory, url_for
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import User
from app.services.auth_service import (
    AuthValidationError,
    apply_profile_update,
    create_user,
    ensure_user_profile,
    hash_password,
    validate_profile_payload,
    validate_password_change,
    validate_register_payload,
    verify_login,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
ALLOWED_AVATAR_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}


def _avatar_root():
    upload_root = Path(current_app.config.get("UPLOAD_ROOT", "uploads"))
    if not upload_root.is_absolute():
        # 统一以 backend 目录为基准，避免运行目录不同导致读写路径不一致。
        upload_root = Path(current_app.root_path).parent / upload_root
    return upload_root / "avatars"


def _bad_request(message, status_code=400):
    return jsonify({"code": status_code, "message": message}), status_code


def _get_request_json():
    payload = request.get_json(silent=True)
    return payload or {}


def _load_current_user():
    identity = get_jwt_identity()
    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return None
    return db.session.get(User, user_id)


@auth_bp.post("/register")
def register():
    payload = _get_request_json()
    try:
        username, password, email = validate_register_payload(payload)
        user = create_user(username=username, password=password, email=email)
    except AuthValidationError as error:
        return _bad_request(str(error))

    try:
        db.session.add(user)
        db.session.flush()
        ensure_user_profile(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _bad_request("用户名已存在。")

    return jsonify({"code": 0, "message": "注册成功", "data": user.to_dict()})


@auth_bp.post("/login")
def login():
    payload = _get_request_json()
    username = (payload.get("username") or "").strip()
    password = (payload.get("password") or "").strip()
    if not username or not password:
        return _bad_request("请输入用户名和密码。")

    try:
        user = verify_login(username=username, password=password)
    except AuthValidationError as error:
        return _bad_request(str(error), status_code=401)

    token = create_access_token(
        identity=str(user.id),
        additional_claims={"username": user.username},
    )
    return jsonify({"code": 0, "message": "登录成功", "data": {"access_token": token, "user": user.to_dict()}})


@auth_bp.get("/me")
@jwt_required()
def me():
    user = _load_current_user()
    if user is None:
        return _bad_request("登录状态无效，请重新登录。", status_code=401)
    if user.profile is None:
        ensure_user_profile(user)
        db.session.commit()
    return jsonify({"code": 0, "message": "ok", "data": user.to_dict()})


@auth_bp.put("/password")
@jwt_required()
def change_password():
    user = _load_current_user()
    if user is None:
        return _bad_request("登录状态无效，请重新登录。", status_code=401)

    payload = _get_request_json()
    try:
        old_password, new_password = validate_password_change(
            payload.get("old_password"),
            payload.get("new_password"),
        )
    except AuthValidationError as error:
        return _bad_request(str(error))

    try:
        verified_user = verify_login(username=user.username, password=old_password)
    except AuthValidationError:
        return _bad_request("旧密码不正确。")

    verified_user.password_hash = hash_password(new_password)
    db.session.commit()

    return jsonify({"code": 0, "message": "密码修改成功"})


@auth_bp.put("/profile")
@jwt_required()
def update_profile():
    user = _load_current_user()
    if user is None:
        return _bad_request("登录状态无效，请重新登录。", status_code=401)

    payload = _get_request_json()
    try:
        profile_fields = validate_profile_payload(payload)
        apply_profile_update(user, profile_fields)
        db.session.commit()
    except AuthValidationError as error:
        db.session.rollback()
        return _bad_request(str(error))
    except IntegrityError:
        db.session.rollback()
        return _bad_request("用户名已存在。")

    return jsonify({"code": 0, "message": "个人资料已更新", "data": user.to_dict()})


@auth_bp.post("/avatar/upload")
@jwt_required()
def upload_avatar():
    user = _load_current_user()
    if user is None:
        return _bad_request("登录状态无效，请重新登录。", status_code=401)

    upload_file = request.files.get("file")
    if not upload_file or not upload_file.filename:
        return _bad_request("请先选择头像文件。")

    ext = Path(upload_file.filename).suffix.lower().lstrip(".")
    if ext not in ALLOWED_AVATAR_EXTENSIONS:
        return _bad_request("仅支持 png/jpg/jpeg/webp/gif 格式头像。")

    upload_root = _avatar_root()
    upload_root.mkdir(parents=True, exist_ok=True)

    # 统一使用系统生成文件名，确保后缀正确，避免上传名导致的无后缀问题。
    final_name = "u{0}_{1}_{2}_{3}.{4}".format(
        user.id,
        int(time.time() * 1000),
        os.getpid(),
        uuid4().hex[:8],
        ext,
    )
    final_path = upload_root / final_name
    upload_file.save(final_path)

    avatar_url = url_for("auth.get_avatar", filename=final_name, _external=True)
    profile_fields = {
        "username": None,
        "display_name": None,
        "email": None,
        "bio": None,
        "avatar_url": avatar_url,
    }
    apply_profile_update(user, profile_fields)
    db.session.commit()

    return jsonify(
        {
            "code": 0,
            "message": "头像上传成功",
            "data": {
                "avatar_url": avatar_url,
                "user": user.to_dict(),
            },
        }
    )


@auth_bp.get("/avatar/<path:filename>")
def get_avatar(filename):
    avatar_root = _avatar_root()
    if not avatar_root.exists():
        return _bad_request("头像文件不存在。", status_code=404)
    return send_from_directory(str(avatar_root), filename)


@auth_bp.get("/status")
def auth_status():
    return jsonify({"module": "auth", "status": "ready"})
