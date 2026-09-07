from __future__ import annotations

import time

import numpy as np
from scipy.spatial import Voronoi
from sklearn.cluster import AgglomerativeClustering, DBSCAN, KMeans
from sklearn.metrics import pairwise_distances
from sklearn.neighbors import KernelDensity


def cluster_regions(matrix: np.ndarray, embedding: np.ndarray, config: dict | None = None) -> tuple[np.ndarray, dict]:
    config = config or {}
    algorithm = config.get("method", "dbscan")
    start = time.perf_counter()

    if algorithm == "kmeans":
        estimator = KMeans(n_clusters=int(config.get("clusters", 4)), n_init=10, random_state=42)
        labels = estimator.fit_predict(matrix)
    elif algorithm == "agglomerative":
        estimator = AgglomerativeClustering(
            n_clusters=int(config.get("clusters", 4)),
            linkage=config.get("linkage", "ward"),
        )
        labels = estimator.fit_predict(matrix)
    else:
        estimator = DBSCAN(
            eps=float(config.get("eps", 0.85)),
            min_samples=int(config.get("minSamples", 8)),
            metric=config.get("metric", "euclidean"),
        )
        labels = estimator.fit_predict(matrix)

    elapsed_ms = (time.perf_counter() - start) * 1000
    unique_labels = sorted(label for label in np.unique(labels) if label != -1)
    regions = []
    centroids = []
    kde = KernelDensity(kernel="gaussian", bandwidth=float(config.get("densityBandwidth", 0.75))).fit(embedding)
    densities = np.exp(kde.score_samples(embedding))

    for region_id in unique_labels:
        indices = np.where(labels == region_id)[0]
        region_points = embedding[indices]
        centroid = region_points.mean(axis=0)
        centroids.append(centroid)
        regions.append(
            {
                "regionId": int(region_id),
                "size": int(len(indices)),
                "centroid": centroid.tolist(),
                "densityMean": float(densities[indices].mean()),
                "densityMax": float(densities[indices].max()),
                "featureSpread": float(np.linalg.norm(region_points.std(axis=0))),
                "pointIndices": indices.tolist(),
            }
        )

    metrics = {
        "algorithm": algorithm,
        "clusterCount": int(len(unique_labels)),
        "noiseCount": int(np.sum(labels == -1)),
        "noiseRatio": float(np.mean(labels == -1)) if len(labels) else 0.0,
        "elapsedMs": float(elapsed_ms),
        "regions": regions,
        "links": _build_region_links(np.array(centroids), regions) if centroids else [],
        "voronoiPolygons": _build_voronoi(np.array(centroids), regions) if len(centroids) >= 3 else [],
        "pointDensities": densities.tolist(),
    }
    return labels, metrics


def _build_region_links(centroids: np.ndarray, regions: list[dict]) -> list[dict]:
    if len(centroids) < 2:
        return []
    distances = pairwise_distances(centroids)
    links = []
    for index in range(len(centroids)):
        nearest = np.argsort(distances[index])[1 : min(4, len(centroids))]
        for target in nearest:
            if index < target:
                average_size = (regions[index]["size"] + regions[target]["size"]) / 2
                links.append(
                    {
                        "source": int(regions[index]["regionId"]),
                        "target": int(regions[target]["regionId"]),
                        "distance": float(distances[index, target]),
                        "weight": float(average_size / (distances[index, target] + 1e-6)),
                    }
                )
    return links


def _build_voronoi(centroids: np.ndarray, regions: list[dict]) -> list[dict]:
    try:
        vor = Voronoi(centroids)
        finite_regions, vertices = _voronoi_finite_polygons_2d(vor)
    except Exception:
        return []

    polygons = []
    for region_index, region in enumerate(finite_regions):
        polygons.append(
            {
                "regionId": int(regions[region_index]["regionId"]),
                "points": vertices[region].tolist(),
            }
        )
    return polygons


def _voronoi_finite_polygons_2d(vor: Voronoi, radius: float | None = None):
    if vor.points.shape[1] != 2:
        raise ValueError("Voronoi finite polygons require 2D input.")

    new_regions = []
    new_vertices = vor.vertices.tolist()
    center = vor.points.mean(axis=0)
    radius = radius or np.ptp(vor.points, axis=0).max() * 2

    all_ridges: dict[int, list[tuple[int, int, int]]] = {}
    for (point_a, point_b), (vertex_a, vertex_b) in zip(vor.ridge_points, vor.ridge_vertices):
        all_ridges.setdefault(point_a, []).append((point_b, vertex_a, vertex_b))
        all_ridges.setdefault(point_b, []).append((point_a, vertex_a, vertex_b))

    for point_index, region_index in enumerate(vor.point_region):
        vertices = vor.regions[region_index]
        if all(vertex >= 0 for vertex in vertices):
            new_regions.append(vertices)
            continue

        ridges = all_ridges[point_index]
        new_region = [vertex for vertex in vertices if vertex >= 0]
        for point_b, vertex_a, vertex_b in ridges:
            if vertex_b < 0:
                vertex_a, vertex_b = vertex_b, vertex_a
            if vertex_a >= 0:
                continue
            tangent = vor.points[point_b] - vor.points[point_index]
            tangent /= np.linalg.norm(tangent)
            normal = np.array([-tangent[1], tangent[0]])
            midpoint = vor.points[[point_index, point_b]].mean(axis=0)
            direction = np.sign(np.dot(midpoint - center, normal)) * normal
            far_point = vor.vertices[vertex_b] + direction * radius
            new_vertices.append(far_point.tolist())
            new_region.append(len(new_vertices) - 1)

        region_vertices = np.asarray([new_vertices[index] for index in new_region])
        region_center = region_vertices.mean(axis=0)
        angles = np.arctan2(region_vertices[:, 1] - region_center[1], region_vertices[:, 0] - region_center[0])
        new_regions.append([vertex for _, vertex in sorted(zip(angles, new_region))])

    return new_regions, np.asarray(new_vertices)
