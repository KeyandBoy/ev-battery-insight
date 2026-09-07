from __future__ import annotations

import numpy as np
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score


def evaluate_clustering(matrix: np.ndarray, labels: np.ndarray, reduction_metrics: dict, cluster_metrics: dict) -> dict:
    valid_mask = labels != -1
    unique_valid = np.unique(labels[valid_mask])
    has_multiple_clusters = len(unique_valid) >= 2 and np.sum(valid_mask) > len(unique_valid)

    if has_multiple_clusters:
        silhouette = float(silhouette_score(matrix[valid_mask], labels[valid_mask]))
        davies_bouldin = float(davies_bouldin_score(matrix[valid_mask], labels[valid_mask]))
        calinski_harabasz = float(calinski_harabasz_score(matrix[valid_mask], labels[valid_mask]))
    else:
        silhouette = 0.0
        davies_bouldin = 0.0
        calinski_harabasz = 0.0

    preservation_score = float(
        0.55 * reduction_metrics.get("trustworthiness", 0.0)
        + 0.45 * max(reduction_metrics.get("distancePreservation", 0.0), 0.0)
    )
    region_balance = _region_balance(cluster_metrics.get("regions", []))

    return {
        "silhouette": silhouette,
        "daviesBouldin": davies_bouldin,
        "calinskiHarabasz": calinski_harabasz,
        "preservationScore": preservation_score,
        "regionBalance": region_balance,
        "noiseRatio": float(cluster_metrics.get("noiseRatio", 0.0)),
    }


def _region_balance(regions: list[dict]) -> float:
    if not regions:
        return 0.0
    if len(regions) == 1:
        return 0.0
    sizes = np.array([region["size"] for region in regions], dtype=float)
    probability = sizes / sizes.sum()
    entropy = -np.sum(probability * np.log2(probability + 1e-9))
    return float(entropy / np.log2(len(sizes)))
