from __future__ import annotations

import time

import numpy as np
from scipy.stats import spearmanr
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE, trustworthiness

try:
    import umap
except ImportError:  # pragma: no cover
    umap = None


def reduce_dimensions(matrix: np.ndarray, config: dict | None = None) -> tuple[np.ndarray, dict]:
    config = config or {}
    method = config.get("method", "umap")
    if matrix.ndim != 2 or len(matrix) == 0 or matrix.shape[1] == 0:
        raise ValueError("降维输入不能为空，且至少需要 1 个样本和 1 个特征。")

    n_components = max(1, int(config.get("nComponents", 2)))
    n_components = min(n_components, matrix.shape[1], len(matrix))
    start = time.perf_counter()

    if method == "pca":
        reducer = PCA(n_components=n_components, random_state=42)
        embedding = reducer.fit_transform(matrix)
        details = {"explainedVariance": reducer.explained_variance_ratio_.tolist()}
    elif method == "tsne":
        if len(matrix) < 3:
            raise ValueError("t-SNE 至少需要 3 个样本。")
        max_perplexity = max(1.0, len(matrix) - 1.0)
        requested_perplexity = float(config.get("perplexity", 30))
        perplexity = min(requested_perplexity, max_perplexity)
        if perplexity >= len(matrix):
            perplexity = float(len(matrix) - 1)
        if perplexity < 1:
            raise ValueError("t-SNE perplexity 必须大于等于 1。")
        reducer = TSNE(
            n_components=n_components,
            perplexity=perplexity,
            learning_rate=float(config.get("learningRate", 200)),
            init="pca",
            random_state=42,
        )
        embedding = reducer.fit_transform(matrix)
        details = {"klDivergence": float(getattr(reducer, "kl_divergence_", 0.0))}
    else:
        if umap is None:
            raise RuntimeError("缺少 umap-learn 依赖，无法执行 UMAP。")
        if len(matrix) < 3:
            raise ValueError("UMAP 至少需要 3 个样本。")
        n_neighbors = min(int(config.get("neighbors", 15)), max(2, len(matrix) - 1))
        reducer = umap.UMAP(
            n_components=n_components,
            n_neighbors=n_neighbors,
            min_dist=float(config.get("minDist", 0.1)),
            metric=config.get("metric", "euclidean"),
            random_state=42,
        )
        embedding = reducer.fit_transform(matrix)
        details = {"embeddingShape": list(embedding.shape)}

    elapsed_ms = (time.perf_counter() - start) * 1000
    sample_size = min(len(matrix), 300)
    distance_preservation = 0.0
    if sample_size >= 5:
        indices = np.linspace(0, len(matrix) - 1, sample_size, dtype=int)
        original_distance = _pairwise_distance_vector(matrix[indices])
        reduced_distance = _pairwise_distance_vector(embedding[indices])
        statistic = spearmanr(original_distance, reduced_distance).statistic
        distance_preservation = float(0.0 if statistic is None or np.isnan(statistic) else statistic)

    max_trust_neighbors = max(1, (len(matrix) - 1) // 2)
    trust_n = max(1, min(10, max_trust_neighbors))
    metrics = {
        "method": method,
        "nComponents": n_components,
        "trustworthiness": float(trustworthiness(matrix, embedding, n_neighbors=trust_n)) if len(matrix) > 2 else 0.0,
        "distancePreservation": distance_preservation,
        "elapsedMs": float(elapsed_ms),
        "details": details,
    }
    return embedding, metrics


def _pairwise_distance_vector(matrix: np.ndarray) -> np.ndarray:
    diff = matrix[:, None, :] - matrix[None, :, :]
    distances = np.linalg.norm(diff, axis=2)
    upper = np.triu_indices_from(distances, k=1)
    return distances[upper]
