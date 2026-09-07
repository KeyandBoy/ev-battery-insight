from __future__ import annotations

import numpy as np
import pandas as pd


def build_visualization_payload(
    raw_frame: pd.DataFrame,
    processed_frame: pd.DataFrame,
    feature_columns: list[str],
    embedding: np.ndarray,
    labels: np.ndarray,
    cluster_metrics: dict,
    quality_metrics: dict,
    label_column: str = "label",
) -> dict:
    processed_features = processed_frame[feature_columns]
    top_dimensions = processed_features.var().sort_values(ascending=False).head(8).index.tolist()
    filled_parallel = raw_frame[top_dimensions].copy()
    filled_parallel = filled_parallel.fillna(filled_parallel.median(numeric_only=True))
    filled_parallel["region"] = labels
    if label_column in raw_frame.columns:
        filled_parallel[label_column] = raw_frame[label_column]

    points = []
    point_densities = cluster_metrics.get("pointDensities", [0.0] * len(raw_frame))
    for index, (x, y) in enumerate(embedding[:, :2]):
        record = {
            "id": int(index),
            "x": float(x),
            "y": float(y),
            "region": int(labels[index]),
            "density": float(point_densities[index]),
            "sample": {column: _safe_value(raw_frame.iloc[index][column]) for column in top_dimensions[:5]},
        }
        if label_column in raw_frame.columns:
            record["label"] = _safe_value(raw_frame.iloc[index][label_column])
        points.append(record)

    regions = []
    for region in cluster_metrics.get("regions", []):
        indices = region["pointIndices"]
        region_slice = raw_frame.iloc[indices].copy()
        region_slice[top_dimensions] = region_slice[top_dimensions].fillna(region_slice[top_dimensions].median(numeric_only=True))
        summary = {
            "regionId": region["regionId"],
            "size": region["size"],
            "densityMean": region["densityMean"],
            "featureSpread": region["featureSpread"],
            "centroid": region["centroid"],
            "topFeatureMeans": {
                column: float(region_slice[column].mean()) for column in top_dimensions[:6]
            },
        }
        if label_column in region_slice.columns:
            summary["labelDistribution"] = region_slice[label_column].value_counts(normalize=True).round(4).to_dict()
        regions.append(summary)

    correlation_source = raw_frame[top_dimensions].copy().fillna(raw_frame[top_dimensions].median(numeric_only=True))

    return {
        "points": points,
        "regions": regions,
        "regionLinks": cluster_metrics.get("links", []),
        "voronoiPolygons": cluster_metrics.get("voronoiPolygons", []),
        "parallelCoordinates": {
            "dimensions": top_dimensions,
            "records": filled_parallel.head(160).to_dict(orient="records"),
        },
        "featureCorrelation": correlation_source.corr().round(4).to_dict(),
        "metricsSummary": quality_metrics,
    }


def _safe_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value)
    return value
