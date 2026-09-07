from __future__ import annotations

import statistics
import time

from services.clustering import cluster_regions
from services.dimensionality import reduce_dimensions
from services.metrics import evaluate_clustering
from services.preprocess import preprocess_dataset
from services.validation import sanitize_analysis_request


DEFAULT_BENCHMARK_SCENARIOS = [
    {"label": "UMAP + DBSCAN", "reduction": {"method": "umap"}, "clustering": {"method": "dbscan"}},
    {"label": "PCA + DBSCAN", "reduction": {"method": "pca"}, "clustering": {"method": "dbscan"}},
    {"label": "UMAP + KMeans", "reduction": {"method": "umap"}, "clustering": {"method": "kmeans"}},
    {"label": "PCA + KMeans", "reduction": {"method": "pca"}, "clustering": {"method": "kmeans"}},
    {"label": "t-SNE + DBSCAN", "reduction": {"method": "tsne"}, "clustering": {"method": "dbscan"}},
    {"label": "UMAP + Agglomerative", "reduction": {"method": "umap"}, "clustering": {"method": "agglomerative"}},
]


def run_benchmark(frame, dataset_id: int, payload: dict | None = None) -> dict:
    payload = payload or {}
    repeats = _clamp_int(payload.get("repeats", 2), 1, 6, 2)
    base = sanitize_analysis_request(payload)
    scenarios = _resolve_scenarios(payload, base)

    benchmark_results = []
    for scenario in scenarios:
        scenario_runs = []
        for iteration in range(repeats):
            start = time.perf_counter()
            preprocess_result = preprocess_dataset(frame, scenario["preprocess"])
            if not preprocess_result.feature_columns:
                raise ValueError(f"场景 {scenario['label']} 预处理后没有可用特征。")
            feature_matrix = preprocess_result.processed_frame[preprocess_result.feature_columns].to_numpy()
            embedding, reduction_metrics = reduce_dimensions(feature_matrix, scenario["reduction"])
            labels, cluster_metrics = cluster_regions(feature_matrix, embedding, scenario["clustering"])
            quality_metrics = evaluate_clustering(feature_matrix, labels, reduction_metrics, cluster_metrics)
            total_ms = float((time.perf_counter() - start) * 1000)
            scenario_runs.append(
                {
                    "iteration": iteration + 1,
                    "totalElapsedMs": total_ms,
                    "reductionElapsedMs": float(reduction_metrics.get("elapsedMs", 0.0)),
                    "clusteringElapsedMs": float(cluster_metrics.get("elapsedMs", 0.0)),
                    "preservationScore": float(quality_metrics.get("preservationScore", 0.0)),
                    "silhouette": float(quality_metrics.get("silhouette", 0.0)),
                    "noiseRatio": float(quality_metrics.get("noiseRatio", 0.0)),
                    "clusterCount": int(cluster_metrics.get("clusterCount", 0)),
                    "dimensionsUsed": int(len(preprocess_result.feature_columns)),
                }
            )

        benchmark_results.append(_aggregate_scenario(dataset_id, scenario, scenario_runs))

    best_quality = max(benchmark_results, key=lambda item: item["aggregate"]["preservationScoreMean"])
    fastest = min(benchmark_results, key=lambda item: item["aggregate"]["totalElapsedMsMean"])

    return {
        "datasetId": dataset_id,
        "repeats": repeats,
        "scenarioCount": len(benchmark_results),
        "results": benchmark_results,
        "summary": {
            "bestQualityLabel": best_quality["label"],
            "bestQualityScore": best_quality["aggregate"]["preservationScoreMean"],
            "fastestLabel": fastest["label"],
            "fastestElapsedMs": fastest["aggregate"]["totalElapsedMsMean"],
        },
    }


def _resolve_scenarios(payload: dict, base: dict) -> list[dict]:
    scenarios = payload.get("scenarios")
    if scenarios:
        scenarios = list(scenarios)[:12]
        resolved = []
        for index, scenario in enumerate(scenarios, 1):
            scenario_payload = {
                "datasetId": base["datasetId"],
                "preprocess": {**base["preprocess"], **(scenario.get("preprocess") or {})},
                "reduction": {**base["reduction"], **(scenario.get("reduction") or {})},
                "clustering": {**base["clustering"], **(scenario.get("clustering") or {})},
            }
            sanitized = sanitize_analysis_request(scenario_payload)
            resolved.append(
                {
                    "label": scenario.get("label") or f"Scenario {index}",
                    "preprocess": sanitized["preprocess"],
                    "reduction": sanitized["reduction"],
                    "clustering": sanitized["clustering"],
                }
            )
        return resolved

    resolved = []
    for scenario in DEFAULT_BENCHMARK_SCENARIOS:
        scenario_payload = {
            "datasetId": base["datasetId"],
            "preprocess": base["preprocess"],
            "reduction": {**base["reduction"], **scenario["reduction"]},
            "clustering": {**base["clustering"], **scenario["clustering"]},
        }
        sanitized = sanitize_analysis_request(scenario_payload)
        resolved.append(
            {
                "label": scenario["label"],
                "preprocess": sanitized["preprocess"],
                "reduction": sanitized["reduction"],
                "clustering": sanitized["clustering"],
            }
        )
    return resolved


def _aggregate_scenario(dataset_id: int, scenario: dict, runs: list[dict]) -> dict:
    def mean_of(key: str) -> float:
        return float(statistics.fmean(item[key] for item in runs))

    def min_of(key: str) -> float:
        return float(min(item[key] for item in runs))

    def max_of(key: str) -> float:
        return float(max(item[key] for item in runs))

    return {
        "datasetId": dataset_id,
        "label": scenario["label"],
        "preprocess": scenario["preprocess"],
        "reduction": scenario["reduction"],
        "clustering": scenario["clustering"],
        "runs": runs,
        "aggregate": {
            "totalElapsedMsMean": mean_of("totalElapsedMs"),
            "totalElapsedMsMin": min_of("totalElapsedMs"),
            "totalElapsedMsMax": max_of("totalElapsedMs"),
            "preservationScoreMean": mean_of("preservationScore"),
            "silhouetteMean": mean_of("silhouette"),
            "noiseRatioMean": mean_of("noiseRatio"),
            "clusterCountMean": mean_of("clusterCount"),
            "dimensionsUsedMean": mean_of("dimensionsUsed"),
        },
    }


def _clamp_int(value, lower: int, upper: int, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return min(max(parsed, lower), upper)
