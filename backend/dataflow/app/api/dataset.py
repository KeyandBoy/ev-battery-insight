from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Dataset
from app.services.dataset_service import (
    DatasetValidationError,
    build_tree_nodes,
    clean_rows,
    cleanup_file_if_exists,
    delete_dataset,
    get_dataset_for_user,
    normalize_mapping_fields,
    parse_rows,
    persist_dataset_with_records,
    preview_processed_records,
    preview_dataset_rows,
    save_upload_file,
    validate_upload_file,
)

dataset_bp = Blueprint("dataset", __name__, url_prefix="/api/datasets")


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
        raise DatasetValidationError("page 和 page_size 必须是整数。")
    if page < 1:
        raise DatasetValidationError("page 不能小于 1。")
    if page_size < 1 or page_size > 100:
        raise DatasetValidationError("page_size 必须在 1 到 100 之间。")
    return page, page_size


def _parse_preview_limit():
    limit_raw = request.args.get("limit", "20")
    try:
        limit = int(limit_raw)
    except (TypeError, ValueError):
        raise DatasetValidationError("limit 必须是整数。")

    if limit < 1 or limit > 200:
        raise DatasetValidationError("limit 必须在 1 到 200 之间。")
    return limit


@dataset_bp.get("")
@jwt_required()
def list_datasets():
    user_id = _current_user_id()
    if user_id is None:
        return _bad_request("登录状态无效，请重新登录。", status_code=401)

    try:
        page, page_size = _parse_page_args()
    except DatasetValidationError as error:
        return _bad_request(str(error))

    query = Dataset.query.filter_by(user_id=user_id)
    total = query.count()
    datasets = (
        query.order_by(Dataset.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return jsonify(
        {
            "code": 0,
            "message": "ok",
            "data": [dataset.to_dict() for dataset in datasets],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            },
        }
    )


@dataset_bp.post("/upload")
@jwt_required()
def upload_dataset():
    user_id = _current_user_id()
    if user_id is None:
        return _bad_request("登录状态无效，请重新登录。", status_code=401)

    upload_file = request.files.get("file")
    dataset_name = (request.form.get("name") or "").strip()
    value_field = (request.form.get("value_field") or "").strip() or None
    hierarchy_fields_raw = (request.form.get("hierarchy_fields") or "").strip()
    hierarchy_fields = [item.strip() for item in hierarchy_fields_raw.split(",") if item.strip()]

    file_path = None
    try:
        source_type = validate_upload_file(upload_file)
        file_path = save_upload_file(upload_file, user_id=user_id)
        parsed_rows = parse_rows(file_path=file_path, source_type=source_type)
        cleaned_rows, numeric_fields = clean_rows(parsed_rows)
        final_value_field, final_hierarchy_fields = normalize_mapping_fields(
            cleaned_rows=cleaned_rows,
            numeric_fields=numeric_fields,
            value_field=value_field,
            hierarchy_fields=hierarchy_fields,
        )

        if not dataset_name:
            dataset_name = upload_file.filename.rsplit(".", 1)[0][:100]
        tree_nodes = build_tree_nodes(
            cleaned_rows=cleaned_rows,
            hierarchy_fields=final_hierarchy_fields,
            value_field=final_value_field,
        )
        dataset, node_count = persist_dataset_with_records(
            user_id=user_id,
            name=dataset_name,
            source_type=source_type,
            file_path=file_path,
            value_field=final_value_field,
            hierarchy_fields=final_hierarchy_fields,
            cleaned_rows=cleaned_rows,
            nodes=tree_nodes,
        )

        return jsonify(
            {
                "code": 0,
                "message": "数据集上传并处理成功",
                "data": {
                    "dataset": dataset.to_dict(),
                    "summary": {
                        "raw_rows": len(parsed_rows),
                        "clean_rows": len(cleaned_rows),
                        "node_count": node_count,
                        "numeric_fields": numeric_fields,
                        "value_field": final_value_field,
                        "hierarchy_fields": final_hierarchy_fields,
                    },
                },
            }
        )
    except DatasetValidationError as error:
        db.session.rollback()
        cleanup_file_if_exists(file_path)
        return _bad_request(str(error))
    except IntegrityError:
        db.session.rollback()
        cleanup_file_if_exists(file_path)
        return _bad_request("数据集名称重复，请更换名称后重试。")
    except Exception as error:
        db.session.rollback()
        cleanup_file_if_exists(file_path)
        return _bad_request("数据处理失败：{0}".format(str(error)), status_code=500)


@dataset_bp.get("/<int:dataset_id>/preview")
@jwt_required()
def preview_dataset(dataset_id):
    user_id = _current_user_id()
    if user_id is None:
        return _bad_request("登录状态无效，请重新登录。", status_code=401)

    try:
        limit = _parse_preview_limit()
        dataset = get_dataset_for_user(dataset_id=dataset_id, user_id=user_id)
        preview = preview_dataset_rows(dataset=dataset, limit=limit)
        processed_preview = preview_processed_records(dataset=dataset, limit=limit)
    except DatasetValidationError as error:
        return _bad_request(str(error))

    return jsonify(
        {
            "code": 0,
            "message": "ok",
            "data": {
                "dataset": dataset.to_dict(),
                "preview": preview,
                "processed_preview": processed_preview,
            },
        }
    )


@dataset_bp.delete("/<int:dataset_id>")
@jwt_required()
def remove_dataset(dataset_id):
    user_id = _current_user_id()
    if user_id is None:
        return _bad_request("登录状态无效，请重新登录。", status_code=401)

    try:
        dataset = get_dataset_for_user(dataset_id=dataset_id, user_id=user_id)
        delete_dataset(dataset)
    except DatasetValidationError as error:
        return _bad_request(str(error), status_code=404)
    except Exception as error:
        db.session.rollback()
        return _bad_request("删除数据集失败：{0}".format(str(error)), status_code=500)

    return jsonify({"code": 0, "message": "数据集已删除"})


@dataset_bp.get("/status")
def dataset_status():
    return jsonify({"module": "dataset", "status": "ready"})
