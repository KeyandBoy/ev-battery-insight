from __future__ import annotations

import time

from flask import Blueprint, Response, jsonify, request

from services.benchmark import run_benchmark
from services.clustering import cluster_regions
from services.dataset_service import list_analysis_runs, load_dataset_frame, save_analysis_run
from services.dimensionality import reduce_dimensions
from services.metrics import evaluate_clustering
from services.preprocess import preprocess_dataset
from services.run_service import compare_runs, export_run_json, export_run_points_csv, get_run_or_404, serialize_run_detail
from services.validation import sanitize_analysis_request
from services.visualization import build_visualization_payload
from utils.serialization import to_jsonable

analysis_bp = Blueprint("analysis", __name__, url_prefix="/api/analysis")


@analysis_bp.get("/runs")
def get_runs():
    return jsonify({"items": list_analysis_runs()})


@analysis_bp.get("/runs/<int:run_id>")
def get_run_detail(run_id: int):
    run = get_run_or_404(run_id)
    return jsonify({"run": serialize_run_detail(run)})


@analysis_bp.get("/runs/<int:run_id>/export")
def export_run(run_id: int):
    run = get_run_or_404(run_id)
    export_format = request.args.get("format", "json")
    if export_format == "csv":
        content = export_run_points_csv(run)
        return Response(
            content,
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="analysis_run_{run_id}_points.csv"'},
        )
    content = export_run_json(run)
    return Response(
        content,
        mimetype="application/json; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="analysis_run_{run_id}.json"'},
    )


@analysis_bp.post("/compare")
def compare_analysis_runs():
    payload = request.get_json(silent=True) or {}
    run_ids = payload.get("runIds", [])
    try:
        parsed_run_ids = [int(run_id) for run_id in run_ids]
        result = compare_runs(parsed_run_ids)
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    return jsonify(result)


@analysis_bp.post("/benchmark")
def benchmark_analysis():
    payload = request.get_json(silent=True) or {}
    dataset_id = payload.get("datasetId")
    if not dataset_id:
        return jsonify({"message": "datasetId 不能为空。"}), 400
    try:
        dataset_id = int(dataset_id)
    except (TypeError, ValueError):
        return jsonify({"message": "datasetId 格式不正确。"}), 400
    dataset, frame = load_dataset_frame(dataset_id)
    try:
        result = run_benchmark(frame, dataset.id, payload)
    except (ValueError, RuntimeError) as error:
        return jsonify({"message": str(error)}), 400
    return jsonify(result)


@analysis_bp.post("/run")
def run_analysis():
    payload = sanitize_analysis_request(request.get_json(silent=True) or {})
    dataset_id = payload.get("datasetId")
    if not dataset_id:
        return jsonify({"message": "datasetId 不能为空。"}), 400

    preprocess_config = payload.get("preprocess", {})
    reducer_config = payload.get("reduction", {})
    cluster_config = payload.get("clustering", {})
    label_column = preprocess_config.get("labelColumn", "label")

    dataset, frame = load_dataset_frame(int(dataset_id))
    overall_start = time.perf_counter()
    preprocess_result = preprocess_dataset(frame, preprocess_config)
    if not preprocess_result.feature_columns:
        return jsonify({"message": "预处理后没有可用数值特征，请调整阈值参数。"}), 400
    feature_matrix = preprocess_result.processed_frame[preprocess_result.feature_columns].to_numpy()
    try:
        embedding, reduction_metrics = reduce_dimensions(feature_matrix, reducer_config)
        labels, cluster_metrics = cluster_regions(feature_matrix, embedding, cluster_config)
    except (ValueError, RuntimeError) as error:
        return jsonify({"message": str(error)}), 400
    quality_metrics = evaluate_clustering(feature_matrix, labels, reduction_metrics, cluster_metrics)
    visualization_payload = build_visualization_payload(
        raw_frame=preprocess_result.raw_frame,
        processed_frame=preprocess_result.processed_frame,
        feature_columns=preprocess_result.feature_columns,
        embedding=embedding,
        labels=labels,
        cluster_metrics=cluster_metrics,
        quality_metrics=quality_metrics,
        label_column=dataset.label_column or label_column,
    )

    performance_metrics = {
        "totalElapsedMs": float((time.perf_counter() - overall_start) * 1000),
        "reductionElapsedMs": float(reduction_metrics.get("elapsedMs", 0.0)),
        "clusteringElapsedMs": float(cluster_metrics.get("elapsedMs", 0.0)),
        "pointsRendered": len(visualization_payload["points"]),
        "dimensionsUsed": len(preprocess_result.feature_columns),
    }

    run = save_analysis_run(
        dataset_id=int(dataset_id),
        reducer=reducer_config.get("method", "umap"),
        algorithm=cluster_config.get("method", "dbscan"),
        preprocess_config=to_jsonable(preprocess_config),
        algorithm_config=to_jsonable({"reduction": reducer_config, "clustering": cluster_config}),
        quality_metrics=to_jsonable(quality_metrics),
        performance_metrics=to_jsonable(performance_metrics),
        result_payload=to_jsonable(
            {
                "dataset": {
                    "id": dataset.id,
                    "name": dataset.name,
                    "sampleCount": dataset.sample_count,
                    "dimensionCount": dataset.dimension_count,
                },
                "preprocessSummary": preprocess_result.summary,
                "reductionMetrics": reduction_metrics,
                "clusteringMetrics": {key: value for key, value in cluster_metrics.items() if key != "pointDensities"},
                "visualization": visualization_payload,
            }
        ),
        preservation_score=float(quality_metrics["preservationScore"]),
    )

    return jsonify(
        {
            "runId": run.id,
            "dataset": {
                "id": dataset.id,
                "name": dataset.name,
                "sampleCount": dataset.sample_count,
                "dimensionCount": dataset.dimension_count,
            },
            "preprocess": preprocess_result.summary,
            "reduction": reduction_metrics,
            "clustering": {key: value for key, value in cluster_metrics.items() if key != "pointDensities"},
            "quality": quality_metrics,
            "performance": performance_metrics,
            "visualization": visualization_payload,
        }
    )
