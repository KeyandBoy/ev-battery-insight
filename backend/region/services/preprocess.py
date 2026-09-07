from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.feature_selection import VarianceThreshold
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler


@dataclass
class PreprocessResult:
    raw_frame: pd.DataFrame
    processed_frame: pd.DataFrame
    feature_columns: list[str]
    summary: dict


def _build_imputer(strategy: str) -> SimpleImputer:
    return SimpleImputer(strategy={"mean": "mean", "median": "median", "most_frequent": "most_frequent"}.get(strategy, "median"))


def _build_scaler(method: str):
    scaler_map = {
        "standard": StandardScaler(),
        "minmax": MinMaxScaler(),
        "robust": RobustScaler(),
        "none": None,
    }
    return scaler_map.get(method, StandardScaler())


def preprocess_dataset(frame: pd.DataFrame, config: dict | None = None) -> PreprocessResult:
    config = config or {}
    label_column = config.get("labelColumn", "label")
    numeric_columns = [
        column for column in frame.columns if column != label_column and pd.api.types.is_numeric_dtype(frame[column])
    ]
    original_missing_ratio = float(frame[numeric_columns].isna().mean().mean()) if numeric_columns else 0.0
    if not numeric_columns:
        processed = frame[[label_column]].copy() if label_column in frame.columns else pd.DataFrame()
        return PreprocessResult(
            raw_frame=frame.copy(),
            processed_frame=processed,
            feature_columns=[],
            summary={
                "inputRows": int(len(frame)),
                "inputDimensions": 0,
                "outputDimensions": 0,
                "removedLowVariance": [],
                "removedCorrelated": [],
                "missingRatio": original_missing_ratio,
            },
        )
    working = frame[numeric_columns].copy()

    imputer = _build_imputer(config.get("missingStrategy", "median"))
    working = pd.DataFrame(imputer.fit_transform(working), columns=numeric_columns)

    variance_threshold = float(config.get("varianceThreshold", 0.0))
    removed_low_variance: list[str] = []
    if variance_threshold > 0 and not working.empty:
        selector = VarianceThreshold(threshold=variance_threshold)
        try:
            selected_values = selector.fit_transform(working)
            support_mask = selector.get_support()
            removed_low_variance = [column for column, keep in zip(numeric_columns, support_mask) if not keep]
            numeric_columns = [column for column, keep in zip(numeric_columns, support_mask) if keep]
            working = pd.DataFrame(selected_values, columns=numeric_columns)
        except ValueError:
            removed_low_variance = numeric_columns.copy()
            working = pd.DataFrame()
            numeric_columns = []

    correlation_threshold = float(config.get("correlationThreshold", 0.98))
    removed_correlated: list[str] = []
    if 0 < correlation_threshold < 1 and len(numeric_columns) > 1:
        corr_matrix = working.corr().abs()
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        removed_correlated = [column for column in upper.columns if any(upper[column] > correlation_threshold)]
        if removed_correlated:
            working = working.drop(columns=removed_correlated)
            numeric_columns = [column for column in numeric_columns if column not in removed_correlated]

    max_features = int(config.get("maxFeatures", 0))
    if max_features > 0 and len(numeric_columns) > max_features:
        kept_columns = working.var().sort_values(ascending=False).head(max_features).index.tolist()
        working = working[kept_columns]
        numeric_columns = kept_columns

    scaler = _build_scaler(config.get("scaler", "standard"))
    if scaler is not None and not working.empty:
        working = pd.DataFrame(scaler.fit_transform(working), columns=numeric_columns)

    if label_column in frame.columns:
        working[label_column] = frame[label_column].to_numpy()

    summary = {
        "inputRows": int(len(frame)),
        "inputDimensions": int(len(frame.columns) - (1 if label_column in frame.columns else 0)),
        "outputDimensions": int(len(numeric_columns)),
        "removedLowVariance": removed_low_variance,
        "removedCorrelated": removed_correlated,
        "missingRatio": original_missing_ratio,
    }

    return PreprocessResult(
        raw_frame=frame.copy(),
        processed_frame=working,
        feature_columns=numeric_columns,
        summary=summary,
    )
