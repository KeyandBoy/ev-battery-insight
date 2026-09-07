from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Dashboard
from app.services.dashboard_service import (
    DashboardValidationError,
    create_dashboard,
    delete_dashboard,
    get_dashboard_for_user,
    list_dashboards,
    save_dashboard_layout,
    set_publish_status,
    update_dashboard_meta,
)

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboards")


def _bad_request(message, status_code=400):
    return jsonify({"code": status_code, "message": message}), status_code


def _current_user_id():
    identity = get_jwt_identity()
    try:
        return int(identity)
    except (TypeError, ValueError):
        return None


def _parse_page_args():
    page_raw = request.args.get("page", "1")
    page_size_raw = request.args.get("page_size", "20")
    try:
        page = int(page_raw)
        page_size = int(page_size_raw)
    except (TypeError, ValueError):
        raise DashboardValidationError("page 和 page_size 必须是整数。")

    if page < 1:
        raise DashboardValidationError("page 不能小于 1。")
    if page_size < 1 or page_size > 100:
        raise DashboardValidationError("page_size 需在 1 到 100 之间。")
    return page, page_size


def _dashboard_payload(dashboard, with_components=False):
    payload = dashboard.to_dict()
    if with_components:
        payload["components"] = [
            component.to_dict()
            for component in sorted(dashboard.components, key=lambda item: (item.z_index, item.id))
        ]
    return payload


@dashboard_bp.get("")
@jwt_required()
def dashboard_list():
    user_id = _current_user_id()
    if user_id is None:
        return _bad_request("登录状态无效，请重新登录。", status_code=401)

    try:
        page, page_size = _parse_page_args()
    except DashboardValidationError as error:
        return _bad_request(str(error))

    query = list_dashboards(user_id=user_id)
    total = query.count()
    dashboards = (
        query.order_by(Dashboard.updated_at.desc(), Dashboard.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    data = []
    for dashboard in dashboards:
        item = _dashboard_payload(dashboard, with_components=False)
        item["component_count"] = len(dashboard.components)
        data.append(item)
    return jsonify(
        {
            "code": 0,
            "message": "ok",
            "data": data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            },
        }
    )


@dashboard_bp.post("")
@jwt_required()
def dashboard_create():
    user_id = _current_user_id()
    if user_id is None:
        return _bad_request("登录状态无效，请重新登录。", status_code=401)

    payload = request.get_json(silent=True) or {}
    try:
        dashboard = create_dashboard(user_id=user_id, payload=payload)
    except DashboardValidationError as error:
        return _bad_request(str(error))
    except Exception:
        db.session.rollback()
        return _bad_request("创建大屏失败。", status_code=500)
    return jsonify({"code": 0, "message": "创建成功", "data": _dashboard_payload(dashboard, with_components=True)})


@dashboard_bp.get("/<int:dashboard_id>")
@jwt_required()
def dashboard_detail(dashboard_id):
    user_id = _current_user_id()
    if user_id is None:
        return _bad_request("登录状态无效，请重新登录。", status_code=401)

    try:
        dashboard = get_dashboard_for_user(user_id=user_id, dashboard_id=dashboard_id)
    except DashboardValidationError as error:
        return _bad_request(str(error), status_code=404)
    return jsonify({"code": 0, "message": "ok", "data": _dashboard_payload(dashboard, with_components=True)})


@dashboard_bp.put("/<int:dashboard_id>")
@jwt_required()
def dashboard_update(dashboard_id):
    user_id = _current_user_id()
    if user_id is None:
        return _bad_request("登录状态无效，请重新登录。", status_code=401)

    payload = request.get_json(silent=True) or {}
    try:
        dashboard = get_dashboard_for_user(user_id=user_id, dashboard_id=dashboard_id)
        dashboard = update_dashboard_meta(dashboard=dashboard, payload=payload)
    except DashboardValidationError as error:
        return _bad_request(str(error))
    except Exception:
        db.session.rollback()
        return _bad_request("更新大屏失败。", status_code=500)
    return jsonify({"code": 0, "message": "更新成功", "data": _dashboard_payload(dashboard, with_components=False)})


@dashboard_bp.delete("/<int:dashboard_id>")
@jwt_required()
def dashboard_remove(dashboard_id):
    user_id = _current_user_id()
    if user_id is None:
        return _bad_request("登录状态无效，请重新登录。", status_code=401)

    try:
        dashboard = get_dashboard_for_user(user_id=user_id, dashboard_id=dashboard_id)
        delete_dashboard(dashboard)
    except DashboardValidationError as error:
        return _bad_request(str(error), status_code=404)
    except Exception:
        db.session.rollback()
        return _bad_request("删除大屏失败。", status_code=500)
    return jsonify({"code": 0, "message": "删除成功"})


@dashboard_bp.put("/<int:dashboard_id>/layout")
@jwt_required()
def dashboard_save_layout(dashboard_id):
    user_id = _current_user_id()
    if user_id is None:
        return _bad_request("登录状态无效，请重新登录。", status_code=401)

    payload = request.get_json(silent=True) or {}
    try:
        dashboard = get_dashboard_for_user(user_id=user_id, dashboard_id=dashboard_id)
        dashboard = save_dashboard_layout(dashboard=dashboard, payload=payload, user_id=user_id)
    except DashboardValidationError as error:
        db.session.rollback()
        return _bad_request(str(error))
    except Exception:
        db.session.rollback()
        return _bad_request("保存布局失败。", status_code=500)
    return jsonify({"code": 0, "message": "保存成功", "data": _dashboard_payload(dashboard, with_components=True)})


@dashboard_bp.put("/<int:dashboard_id>/publish")
@jwt_required()
def dashboard_publish(dashboard_id):
    user_id = _current_user_id()
    if user_id is None:
        return _bad_request("登录状态无效，请重新登录。", status_code=401)

    payload = request.get_json(silent=True) or {}
    is_published = payload.get("is_published", 1)
    try:
        dashboard = get_dashboard_for_user(user_id=user_id, dashboard_id=dashboard_id)
        dashboard = set_publish_status(dashboard=dashboard, is_published=is_published)
    except DashboardValidationError as error:
        db.session.rollback()
        return _bad_request(str(error))
    except Exception:
        db.session.rollback()
        return _bad_request("发布状态更新失败。", status_code=500)
    return jsonify({"code": 0, "message": "发布状态已更新", "data": _dashboard_payload(dashboard, with_components=False)})


@dashboard_bp.get("/status")
def dashboard_status():
    return jsonify({"module": "dashboard", "status": "ready"})
