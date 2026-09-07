from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class SyntheticDataset:
    frame: pd.DataFrame
    label_column: str
    description: str


def _inject_missing_values(frame: pd.DataFrame, ratio: float = 0.03) -> pd.DataFrame:
    copied = frame.copy()
    rng = np.random.default_rng(42)
    numeric_columns = [column for column in copied.columns if column != "label"]
    total_cells = len(copied) * len(numeric_columns)
    missing_count = max(1, int(total_cells * ratio))
    indices = rng.choice(total_cells, size=missing_count, replace=False)
    rows = indices // len(numeric_columns)
    cols = indices % len(numeric_columns)
    for row_index, column_index in zip(rows, cols):
        copied.loc[row_index, numeric_columns[column_index]] = np.nan
    return copied


def create_gene_expression_dataset(samples: int = 420, dimensions: int = 18) -> SyntheticDataset:
    rng = np.random.default_rng(7)
    centers = rng.normal(0, 3, size=(4, dimensions))
    labels = rng.integers(0, len(centers), size=samples)
    data = np.vstack(
        [rng.normal(centers[label], 0.7 + label * 0.2, size=(1, dimensions)) for label in labels]
    )
    frame = pd.DataFrame(data, columns=[f"gene_{index + 1}" for index in range(dimensions)])
    frame["signal_strength"] = frame.iloc[:, :5].mean(axis=1) * 0.6 + rng.normal(0, 0.4, size=samples)
    frame["mutation_score"] = frame.iloc[:, 5:10].sum(axis=1) * 0.1 + rng.normal(0, 0.6, size=samples)
    frame["label"] = labels
    frame = _inject_missing_values(frame)
    return SyntheticDataset(
        frame=frame,
        label_column="label",
        description="模拟基因表达高维数据，包含多簇表达模式、信号强度与突变分值。",
    )


def create_image_feature_dataset(samples: int = 500, dimensions: int = 24) -> SyntheticDataset:
    rng = np.random.default_rng(11)
    centers = rng.normal(0, 4, size=(5, dimensions))
    labels = rng.integers(0, len(centers), size=samples)
    data = np.vstack(
        [rng.normal(centers[label], 1.2, size=(1, dimensions)) + label * 0.35 for label in labels]
    )
    frame = pd.DataFrame(data, columns=[f"feat_{index + 1}" for index in range(dimensions)])
    frame["texture_entropy"] = frame.iloc[:, :8].std(axis=1) * 1.4
    frame["edge_density"] = frame.iloc[:, 8:16].mean(axis=1) * 0.8
    frame["label"] = labels
    frame = _inject_missing_values(frame)
    return SyntheticDataset(
        frame=frame,
        label_column="label",
        description="模拟图像特征高维数据，覆盖纹理、边缘与局部模式信息。",
    )


def create_finance_behavior_dataset(samples: int = 620, dimensions: int = 20) -> SyntheticDataset:
    rng = np.random.default_rng(23)
    segments = rng.integers(0, 4, size=samples)
    base = np.vstack(
        [
            rng.normal(loc=segment * 1.6, scale=0.9 + segment * 0.15, size=(1, dimensions))
            for segment in segments
        ]
    )
    trend = rng.normal(0, 0.8, size=(samples, dimensions)) + np.linspace(-1.5, 1.5, dimensions)
    data = base + trend
    frame = pd.DataFrame(data, columns=[f"behavior_{index + 1}" for index in range(dimensions)])
    frame["risk_score"] = frame.iloc[:, :6].mean(axis=1) * 0.9 + rng.normal(0, 0.5, size=samples)
    frame["asset_ratio"] = np.abs(frame.iloc[:, 6:12].sum(axis=1) / 12)
    frame["label"] = segments
    frame = _inject_missing_values(frame)
    return SyntheticDataset(
        frame=frame,
        label_column="label",
        description="模拟金融用户行为高维数据，用于风险分区和区域异常定位分析。",
    )


DATASET_BUILDERS = {
    "gene_expression": create_gene_expression_dataset,
    "image_features": create_image_feature_dataset,
    "finance_behavior": create_finance_behavior_dataset,
}
