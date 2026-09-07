from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.services.analysis_service import (
    AnalysisValidationError,
    build_pca_projection,
    build_treemap_layout,
    build_tree,
    extract_features,
    load_dataset_records,
    prepare_treemap_tree,
)

analysis_bp = Blueprint("analysis", __name__, url_prefix="/api/analysis")


def _bad_request(message, status_code=400):
    return jsonify({"code": status_code, "message": message}), status_code


def _current_user_id():
    identity = get_jwt_identity()
    try:
        return int(identity)
    except (TypeError, ValueError):
        return None


def _parse_int_query(name, default_value=None, minimum=None):
    raw = request.args.get(name)
    if raw is None or raw == "":
        return default_value

    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise AnalysisValidationError("{0} 参数必须是整数。".format(name))

    if minimum is not None and value < minimum:
        raise AnalysisValidationError("{0} 参数不能小于 {1}。".format(name, minimum))
    return value


def _parse_float_query(name, default_value=None, minimum=None, maximum=None):
    raw = request.args.get(name)
    if raw is None or raw == "":
        return default_value

    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise AnalysisValidationError("{0} 参数必须是数字。".format(name))

    if minimum is not None and value < minimum:
        raise AnalysisValidationError("{0} 参数不能小于 {1}。".format(name, minimum))
    if maximum is not None and value > maximum:
        raise AnalysisValidationError("{0} 参数不能大于 {1}。".format(name, maximum))
    return value


def _tree_to_payload(node):
    return {
        "id": node["id"],
        "parent_id": node["parent_id"],
        "node_key": node["node_key"],
        "node_name": node["node_name"],
        "level": node["level"],
        "value_num": round(float(node["value_num"]), 4),
        "is_abnormal": node["is_abnormal"],
        "children": [_tree_to_payload(child) for child in node.get("children", [])],
    }


@analysis_bp.get("/tree")
@jwt_required()
def analysis_tree():
    user_id = _current_user_id()
    if user_id is None:
        return _bad_request("登录状态无效，请重新登录。", status_code=401)

    try:
        dataset_id = _parse_int_query("dataset_id", minimum=1)
        if dataset_id is None:
            raise AnalysisValidationError("dataset_id 参数不能为空。")
        dataset, records = load_dataset_records(dataset_id=dataset_id, user_id=user_id)
        tree = build_tree(records)
    except AnalysisValidationError as error:
        return _bad_request(str(error))

    return jsonify(
        {
            "code": 0,
            "message": "ok",
            "data": {
                "dataset": dataset.to_dict(),
                "tree": _tree_to_payload(tree),
            },
        }
    )


@analysis_bp.get("/features")
@jwt_required()
def analysis_features():
    user_id = _current_user_id()
    if user_id is None:
        return _bad_request("登录状态无效，请重新登录。", status_code=401)

    try:
        dataset_id = _parse_int_query("dataset_id", minimum=1)
        if dataset_id is None:
            raise AnalysisValidationError("dataset_id 参数不能为空。")
        dataset, records = load_dataset_records(dataset_id=dataset_id, user_id=user_id)
        tree = build_tree(records)
        features = extract_features(tree)
    except AnalysisValidationError as error:
        return _bad_request(str(error))

    return jsonify(
        {
            "code": 0,
            "message": "ok",
            "data": {
                "dataset": dataset.to_dict(),
                "features": features,
            },
        }
    )


@analysis_bp.get("/treemap")
@jwt_required()
def analysis_treemap():
    user_id = _current_user_id()
    if user_id is None:
        return _bad_request("登录状态无效，请重新登录。", status_code=401)

    try:
        dataset_id = _parse_int_query("dataset_id", minimum=1)
        width = _parse_int_query("width", default_value=1200, minimum=200)
        height = _parse_int_query("height", default_value=640, minimum=200)
        padding = _parse_int_query("padding", default_value=1, minimum=0)
        top_n = _parse_int_query("top_n", default_value=120, minimum=0)
        min_ratio = _parse_float_query("min_ratio", default_value=0.002, minimum=0, maximum=0.5)
        if dataset_id is None:
            raise AnalysisValidationError("dataset_id 参数不能为空。")

        dataset, records = load_dataset_records(dataset_id=dataset_id, user_id=user_id)
        tree = build_tree(records)
        features = extract_features(tree)
        treemap_tree, aggregation_stats = prepare_treemap_tree(tree, top_n=top_n, min_ratio=min_ratio)
        layout_stats = {
            "hidden_other_nodes": 0,
            "hidden_other_value": 0.0,
        }
        layout_nodes = build_treemap_layout(
            treemap_tree,
            width=width,
            height=height,
            padding=padding,
            layout_stats=layout_stats,
        )
    except AnalysisValidationError as error:
        return _bad_request(str(error))

    return jsonify(
        {
            "code": 0,
            "message": "ok",
            "data": {
                "dataset": dataset.to_dict(),
                "container": {"width": width, "height": height, "padding": padding},
                "features": features,
                "layout_meta": {
                    "top_n": top_n,
                    "min_ratio": min_ratio,
                    "aggregated_nodes": aggregation_stats["aggregated_nodes"],
                    "others_nodes": aggregation_stats["others_nodes"],
                    "hidden_other_nodes": layout_stats["hidden_other_nodes"],
                    "hidden_other_value": layout_stats["hidden_other_value"],
                    "output_node_count": len(layout_nodes),
                },
                "nodes": layout_nodes,
            },
        }
    )


@analysis_bp.get("/pca")
@jwt_required()
def analysis_pca():
    user_id = _current_user_id()
    if user_id is None:
        return _bad_request("登录状态无效，请重新登录。", status_code=401)

    try:
        dataset_id = _parse_int_query("dataset_id", minimum=1)
        max_rows = _parse_int_query("max_rows", default_value=300, minimum=20)
        max_features = _parse_int_query("max_features", default_value=6, minimum=2)
        if dataset_id is None:
            raise AnalysisValidationError("dataset_id 参数不能为空。")

        pca_result = build_pca_projection(
            dataset_id=dataset_id,
            user_id=user_id,
            max_rows=max_rows,
            max_features=max_features,
        )
    except AnalysisValidationError as error:
        return _bad_request(str(error))

    return jsonify(
        {
            "code": 0,
            "message": "ok",
            "data": {
                "dataset": pca_result["dataset"].to_dict(),
                "pca": {
                    "sample_count": pca_result["sample_count"],
                    "feature_count": pca_result["feature_count"],
                    "label_field": pca_result["label_field"],
                    "features": pca_result["features"],
                    "explained_variance_ratio": pca_result["explained_variance_ratio"],
                    "points": pca_result["points"],
                    "component_weights": pca_result["component_weights"],
                },
            },
        }
    )


@analysis_bp.get("/status")
def analysis_status():
    return jsonify({"module": "analysis", "status": "ready"})
