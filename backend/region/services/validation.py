from __future__ import annotations


ALLOWED_MISSING_STRATEGIES = {"mean", "median", "most_frequent"}
ALLOWED_SCALERS = {"standard", "minmax", "robust", "none"}
ALLOWED_REDUCTION_METHODS = {"umap", "pca", "tsne"}
ALLOWED_CLUSTERING_METHODS = {"dbscan", "kmeans", "agglomerative"}
ALLOWED_CLUSTER_LINKAGES = {"ward", "complete", "average"}
ALLOWED_METRICS = {"euclidean", "manhattan", "cosine"}


def sanitize_analysis_request(payload: dict | None = None) -> dict:
    payload = payload or {}
    preprocess = payload.get("preprocess", {}) or {}
    reduction = payload.get("reduction", {}) or {}
    clustering = payload.get("clustering", {}) or {}

    sanitized = {
        "datasetId": int(payload.get("datasetId")) if payload.get("datasetId") is not None else None,
        "preprocess": {
            "labelColumn": str(preprocess.get("labelColumn", "label")).strip() or "label",
            "missingStrategy": _pick(preprocess.get("missingStrategy"), ALLOWED_MISSING_STRATEGIES, "median"),
            "scaler": _pick(preprocess.get("scaler"), ALLOWED_SCALERS, "standard"),
            "varianceThreshold": _clamp_float(preprocess.get("varianceThreshold", 0.01), 0.0, 999999.0, 0.01),
            "correlationThreshold": _clamp_float(preprocess.get("correlationThreshold", 0.97), 0.0, 0.9999, 0.97),
            "maxFeatures": _clamp_int(preprocess.get("maxFeatures", 12), 0, 5000, 12),
        },
        "reduction": {
            "method": _pick(reduction.get("method"), ALLOWED_REDUCTION_METHODS, "umap"),
            "nComponents": _clamp_int(reduction.get("nComponents", 2), 1, 3, 2),
            "neighbors": _clamp_int(reduction.get("neighbors", 15), 2, 200, 15),
            "minDist": _clamp_float(reduction.get("minDist", 0.1), 0.0, 1.0, 0.1),
            "perplexity": _clamp_float(reduction.get("perplexity", 30), 1.0, 300.0, 30.0),
            "learningRate": _clamp_float(reduction.get("learningRate", 200), 10.0, 5000.0, 200.0),
            "metric": _pick(reduction.get("metric"), ALLOWED_METRICS, "euclidean"),
        },
        "clustering": {
            "method": _pick(clustering.get("method"), ALLOWED_CLUSTERING_METHODS, "dbscan"),
            "eps": _clamp_float(clustering.get("eps", 0.85), 0.01, 9999.0, 0.85),
            "minSamples": _clamp_int(clustering.get("minSamples", 8), 2, 5000, 8),
            "clusters": _clamp_int(clustering.get("clusters", 4), 2, 100, 4),
            "linkage": _pick(clustering.get("linkage"), ALLOWED_CLUSTER_LINKAGES, "ward"),
            "densityBandwidth": _clamp_float(clustering.get("densityBandwidth", 0.75), 0.01, 100.0, 0.75),
            "metric": _pick(clustering.get("metric"), ALLOWED_METRICS, "euclidean"),
        },
    }
    return sanitized


def _pick(value, allowed: set[str], default):
    return value if value in allowed else default


def _clamp_float(value, lower: float, upper: float, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return min(max(parsed, lower), upper)


def _clamp_int(value, lower: int, upper: int, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return min(max(parsed, lower), upper)
