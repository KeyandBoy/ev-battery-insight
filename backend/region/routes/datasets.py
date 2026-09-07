from __future__ import annotations

from flask import Blueprint, jsonify, request

from database import db
from models import AnalysisRun, Dataset
from services.dataset_service import (
    create_generated_dataset,
    create_uploaded_dataset,
    list_datasets,
    load_dataset_frame,
    summarize_dataset,
)

datasets_bp = Blueprint("datasets", __name__, url_prefix="/api/datasets")


@datasets_bp.get("")
def get_datasets():
    return jsonify({"items": list_datasets()})


@datasets_bp.post("/generate")
def generate_dataset():
    payload = request.get_json(silent=True) or {}
    dataset_type = payload.get("datasetType", "gene_expression")
    try:
        dataset = create_generated_dataset(dataset_type)
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    return jsonify({"dataset": dataset}), 201


@datasets_bp.post("/upload")
def upload_dataset():
    file = request.files.get("file")
    if file is None:
        return jsonify({"message": "请上传 CSV 文件。"}), 400
    try:
        dataset = create_uploaded_dataset(
            name=request.form.get("name", ""),
            description=request.form.get("description", ""),
            file=file,
            label_column=request.form.get("labelColumn", "label"),
        )
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    return jsonify({"dataset": dataset}), 201


@datasets_bp.get("/<int:dataset_id>/preview")
def preview_dataset(dataset_id: int):
    dataset, frame = load_dataset_frame(dataset_id)
    preview_frame = frame.head(15)
    preview = preview_frame.where(preview_frame.notna(), None).to_dict(orient="records")
    return jsonify(
        {
            "dataset": {
                "id": dataset.id,
                "name": dataset.name,
                "labelColumn": dataset.label_column,
                "sampleCount": dataset.sample_count,
                "dimensionCount": dataset.dimension_count,
            },
            "columns": frame.columns.tolist(),
            "preview": preview,
        }
    )


@datasets_bp.get("/<int:dataset_id>/summary")
def dataset_summary(dataset_id: int):
    return jsonify(summarize_dataset(dataset_id))


@datasets_bp.delete("/<int:dataset_id>")
def delete_dataset(dataset_id: int):
    dataset = db.session.get(Dataset, dataset_id)
    if dataset is None:
        return jsonify({"message": "数据集不存在。"}), 404
    run_count = db.session.query(AnalysisRun).filter_by(dataset_id=dataset_id).delete()
    db.session.delete(dataset)
    db.session.commit()
    return jsonify({"deleted": dataset_id, "runsDeleted": run_count})
