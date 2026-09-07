from __future__ import annotations

import csv
import io
import json

from database import db
from models import AnalysisRun
from utils.serialization import to_jsonable


def get_run_or_404(run_id: int) -> AnalysisRun:
    return db.get_or_404(AnalysisRun, run_id)


def serialize_run_summary(run: AnalysisRun) -> dict:
    raw_payload = run.result_payload or {}
    dataset_snapshot = raw_payload.get("dataset", {})
    return {
        "id": run.id,
        "datasetId": run.dataset_id,
        "datasetName": dataset_snapshot.get("name"),
        "algorithm": run.algorithm,
        "reducer": run.reducer,
        "preservationScore": run.preservation_score,
        "createdAt": run.created_at.isoformat(),
    }


def serialize_run_detail(run: AnalysisRun) -> dict:
    raw_payload = run.result_payload or {}
    visualization = raw_payload.get("visualization", raw_payload)
    preprocess_summary = raw_payload.get("preprocessSummary", {})
    reduction_metrics = raw_payload.get("reductionMetrics", {})
    clustering_metrics = raw_payload.get("clusteringMetrics", {})
    dataset_snapshot = raw_payload.get("dataset", {})
    return {
        "id": run.id,
        "datasetId": run.dataset_id,
        "algorithm": run.algorithm,
        "reducer": run.reducer,
        "preprocessConfig": run.preprocess_config or {},
        "algorithmConfig": run.algorithm_config or {},
        "qualityMetrics": run.quality_metrics or {},
        "performanceMetrics": run.performance_metrics or {},
        "preprocessSummary": preprocess_summary,
        "reductionMetrics": reduction_metrics,
        "clusteringMetrics": clustering_metrics,
        "datasetSnapshot": dataset_snapshot,
        "resultPayload": raw_payload,
        "visualization": visualization,
        "preservationScore": run.preservation_score,
        "createdAt": run.created_at.isoformat(),
    }


def export_run_json(run: AnalysisRun) -> str:
    return json.dumps(to_jsonable(serialize_run_detail(run)), ensure_ascii=False, indent=2)


def export_run_points_csv(run: AnalysisRun) -> str:
    payload = run.result_payload or {}
    visualization = payload.get("visualization", payload)
    points = visualization.get("points", [])
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["id", "x", "y", "region", "density", "label"])
    writer.writeheader()
    for point in points:
        writer.writerow(
            {
                "id": point.get("id"),
                "x": point.get("x"),
                "y": point.get("y"),
                "region": point.get("region"),
                "density": point.get("density"),
                "label": point.get("label"),
            }
        )
    return buffer.getvalue()


def compare_runs(run_ids: list[int]) -> dict:
    selected_ids = list(dict.fromkeys(run_ids))
    runs = [get_run_or_404(run_id) for run_id in selected_ids[:2]]
    if len(runs) < 2:
        raise ValueError("至少需要选择两个运行记录进行对比。")

    first, second = runs[0], runs[1]
    first_quality = first.quality_metrics or {}
    second_quality = second.quality_metrics or {}
    first_performance = first.performance_metrics or {}
    second_performance = second.performance_metrics or {}

    metrics = {}
    metric_keys = {
        "preservationScore",
        "silhouette",
        "daviesBouldin",
        "calinskiHarabasz",
        "regionBalance",
        "noiseRatio",
        "totalElapsedMs",
        "dimensionsUsed",
        "pointsRendered",
    }
    for key in metric_keys:
        first_value = first_quality.get(key, first_performance.get(key, first.preservation_score if key == "preservationScore" else None))
        second_value = second_quality.get(key, second_performance.get(key, second.preservation_score if key == "preservationScore" else None))
        if first_value is None and second_value is None:
            continue
        metrics[key] = {
            "left": first_value,
            "right": second_value,
            "delta": _safe_delta(first_value, second_value),
        }

    return {
        "left": serialize_run_summary(first),
        "right": serialize_run_summary(second),
        "metrics": metrics,
    }


def _safe_delta(left, right):
    try:
        if left is None or right is None:
            return None
        return float(right) - float(left)
    except (TypeError, ValueError):
        return None
