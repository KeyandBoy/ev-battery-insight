from app.extensions import db
from app.models import Component, Dashboard, Dataset


class DashboardValidationError(ValueError):
    pass


ALLOWED_COMPONENT_TYPES = {"treemap", "bar", "pie", "line", "table"}


def list_dashboards(user_id):
    return Dashboard.query.filter_by(user_id=user_id)


def get_dashboard_for_user(user_id, dashboard_id):
    dashboard = Dashboard.query.filter_by(id=dashboard_id, user_id=user_id).first()
    if dashboard is None:
        raise DashboardValidationError("大屏不存在或无权限访问。")
    return dashboard


def validate_dashboard_payload(payload, for_update=False):
    name = (payload.get("name") or "").strip()
    description = payload.get("description")
    if description is not None:
        description = (description or "").strip() or None
    theme = payload.get("theme")
    if theme is not None:
        theme = (theme or "").strip() or "light"

    width_raw = payload.get("canvas_width")
    height_raw = payload.get("canvas_height")
    canvas_width = _safe_int(width_raw, None) if width_raw is not None else None
    canvas_height = _safe_int(height_raw, None) if height_raw is not None else None

    if not for_update and not name:
        raise DashboardValidationError("大屏名称不能为空。")
    if name and len(name) > 100:
        raise DashboardValidationError("大屏名称长度不能超过 100。")
    if description and len(description) > 255:
        raise DashboardValidationError("描述长度不能超过 255。")
    if canvas_width is not None and (canvas_width < 600 or canvas_width > 4096):
        raise DashboardValidationError("画布宽度需在 600 到 4096 之间。")
    if canvas_height is not None and (canvas_height < 360 or canvas_height > 2160):
        raise DashboardValidationError("画布高度需在 360 到 2160 之间。")

    return {
        "name": name,
        "description": description,
        "theme": theme,
        "canvas_width": canvas_width if canvas_width is not None else 1920,
        "canvas_height": canvas_height if canvas_height is not None else 1080,
    }


def create_dashboard(user_id, payload):
    cleaned = validate_dashboard_payload(payload, for_update=False)
    dashboard = Dashboard(
        user_id=user_id,
        name=cleaned["name"],
        description=cleaned["description"],
        canvas_width=cleaned["canvas_width"],
        canvas_height=cleaned["canvas_height"],
        theme=cleaned["theme"],
        layout_json={},
        is_published=0,
    )
    db.session.add(dashboard)
    db.session.commit()
    return dashboard


def update_dashboard_meta(dashboard, payload):
    cleaned = validate_dashboard_payload(payload, for_update=True)
    if cleaned["name"]:
        dashboard.name = cleaned["name"]
    if "description" in payload:
        dashboard.description = cleaned["description"]
    if "theme" in payload and cleaned["theme"]:
        dashboard.theme = cleaned["theme"]
    if "canvas_width" in payload:
        dashboard.canvas_width = cleaned["canvas_width"]
    if "canvas_height" in payload:
        dashboard.canvas_height = cleaned["canvas_height"]
    if "layout_json" in payload:
        dashboard.layout_json = payload.get("layout_json") or {}
    db.session.commit()
    return dashboard


def delete_dashboard(dashboard):
    db.session.delete(dashboard)
    db.session.commit()


def set_publish_status(dashboard, is_published):
    dashboard.is_published = 1 if int(is_published) == 1 else 0
    db.session.commit()
    return dashboard


def save_dashboard_layout(dashboard, payload, user_id):
    components_payload = payload.get("components")
    if not isinstance(components_payload, list):
        raise DashboardValidationError("components 必须是数组。")

    dashboard.layout_json = payload.get("layout_json") or {}

    existed_components = {component.id: component for component in dashboard.components}
    keep_ids = set()

    for index, item in enumerate(components_payload):
        normalized = _normalize_component_payload(item, index, user_id=user_id)
        component_id = item.get("id")
        component = None
        if component_id:
            try:
                component_id = int(component_id)
            except (TypeError, ValueError):
                component_id = None
            component = existed_components.get(component_id)

        if component is None:
            component = Component(dashboard_id=dashboard.id)
            db.session.add(component)

        component.dataset_id = normalized["dataset_id"]
        component.type = normalized["type"]
        component.title = normalized["title"]
        component.x = normalized["x"]
        component.y = normalized["y"]
        component.w = normalized["w"]
        component.h = normalized["h"]
        component.z_index = normalized["z_index"]
        component.config_json = normalized["config_json"]
        component.binding_json = normalized["binding_json"]
        keep_ids.add(component.id)

    for component in dashboard.components:
        if component.id not in keep_ids:
            db.session.delete(component)

    db.session.commit()
    db.session.refresh(dashboard)
    return dashboard


def _normalize_component_payload(item, index, user_id):
    if not isinstance(item, dict):
        raise DashboardValidationError("组件数据格式错误。")

    component_type = (item.get("type") or "").strip().lower()
    if component_type not in ALLOWED_COMPONENT_TYPES:
        raise DashboardValidationError("组件类型不合法：{0}".format(component_type or "unknown"))

    dataset_id = item.get("dataset_id")
    if dataset_id in ("", None):
        dataset_id = None
    else:
        try:
            dataset_id = int(dataset_id)
        except (TypeError, ValueError):
            raise DashboardValidationError("dataset_id 必须是数字或空。")
        dataset_exists = Dataset.query.filter_by(id=dataset_id, user_id=user_id).first()
        if dataset_exists is None:
            raise DashboardValidationError("绑定的数据集不存在或无权限访问。")

    x = max(_safe_int(item.get("x"), 0), 0)
    y = max(_safe_int(item.get("y"), 0), 0)
    w = _safe_int(item.get("w"), 320)
    h = _safe_int(item.get("h"), 220)
    z_index = _safe_int(item.get("z_index"), index + 1)
    if w < 120 or w > 2400:
        raise DashboardValidationError("组件宽度需在 120 到 2400 之间。")
    if h < 80 or h > 1600:
        raise DashboardValidationError("组件高度需在 80 到 1600 之间。")

    return {
        "dataset_id": dataset_id,
        "type": component_type,
        "title": (item.get("title") or "").strip()[:100] or None,
        "x": x,
        "y": y,
        "w": w,
        "h": h,
        "z_index": z_index,
        "config_json": item.get("config_json") or {},
        "binding_json": item.get("binding_json") or {},
    }


def _safe_int(value, fallback):
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback
