from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError, ParserError
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from config import GENERATED_DIR, UPLOAD_DIR
from database import db
from models import AnalysisRun, Dataset
from utils.sample_data import DATASET_BUILDERS


def ensure_data_directories():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def serialize_dataset(dataset: Dataset) -> dict:
    return {
        "id": dataset.id,
        "name": dataset.name,
        "description": dataset.description,
        "sourceType": dataset.source_type,
        "sampleCount": dataset.sample_count,
        "dimensionCount": dataset.dimension_count,
        "labelColumn": dataset.label_column,
        "metaInfo": dataset.meta_info or {},
        "createdAt": dataset.created_at.isoformat(),
    }


def list_datasets() -> list[dict]:
    datasets = Dataset.query.order_by(Dataset.created_at.desc()).all()
    return [serialize_dataset(dataset) for dataset in datasets]


def load_dataset_frame(dataset_id: int) -> tuple[Dataset, pd.DataFrame]:
    dataset = db.get_or_404(Dataset, dataset_id)
    frame = pd.read_csv(dataset.file_path)
    return dataset, frame


def summarize_dataset(dataset_id: int) -> dict:
    dataset, frame = load_dataset_frame(dataset_id)
    numeric_columns = frame.select_dtypes(include="number").columns.tolist()
    label_column = dataset.label_column if dataset.label_column in frame.columns else None
    feature_columns = [column for column in numeric_columns if column != label_column]

    numeric_frame = frame[feature_columns] if feature_columns else pd.DataFrame()
    missing_counts = frame.isna().sum().sort_values(ascending=False)
    top_missing = [
        {"column": column, "missingCount": int(count), "missingRatio": float(count / len(frame) if len(frame) else 0.0)}
        for column, count in missing_counts.head(8).items()
        if count > 0
    ]

    top_variance = []
    if not numeric_frame.empty:
        filled_numeric = numeric_frame.fillna(numeric_frame.median(numeric_only=True))
        for column, variance in filled_numeric.var().sort_values(ascending=False).head(8).items():
            top_variance.append(
                {
                    "column": column,
                    "variance": float(variance),
                    "mean": float(filled_numeric[column].mean()),
                    "std": float(filled_numeric[column].std()),
                }
            )

    label_distribution = {}
    if label_column:
        label_distribution = frame[label_column].value_counts(dropna=False, normalize=True).round(4).to_dict()

    return {
        "dataset": serialize_dataset(dataset),
        "missingOverview": {
            "totalMissingCells": int(frame.isna().sum().sum()),
            "rowsWithMissing": int(frame.isna().any(axis=1).sum()),
            "columnsWithMissing": int((frame.isna().sum() > 0).sum()),
            "topMissingColumns": top_missing,
        },
        "featureOverview": {
            "numericFeatureCount": int(len(feature_columns)),
            "topVarianceFeatures": top_variance,
        },
        "labelDistribution": label_distribution,
    }


def create_generated_dataset(dataset_type: str) -> dict:
    ensure_data_directories()
    if dataset_type not in DATASET_BUILDERS:
        raise ValueError(f"不支持的数据集类型: {dataset_type}")
    generated = DATASET_BUILDERS[dataset_type]()
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    file_path = GENERATED_DIR / f"{dataset_type}_{timestamp}.csv"
    generated.frame.to_csv(file_path, index=False)
    dataset = Dataset(
        name=f"{dataset_type}_{timestamp}",
        description=generated.description,
        source_type="generated",
        file_path=str(file_path),
        sample_count=len(generated.frame),
        dimension_count=len(generated.frame.columns) - 1,
        label_column=generated.label_column,
        meta_info={"datasetType": dataset_type},
    )
    db.session.add(dataset)
    db.session.commit()
    return serialize_dataset(dataset)


def create_uploaded_dataset(name: str, description: str, file: FileStorage, label_column: str = "label") -> dict:
    ensure_data_directories()
    filename = secure_filename(file.filename or "dataset.csv")
    if not filename.lower().endswith(".csv"):
        raise ValueError("仅支持上传 CSV 格式的数据文件。")
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    file_path = UPLOAD_DIR / f"{timestamp}_{filename}"
    file.save(file_path)
    try:
        frame = pd.read_csv(file_path)
    except (EmptyDataError, ParserError, UnicodeDecodeError) as error:
        file_path.unlink(missing_ok=True)
        raise ValueError("CSV 文件无法解析，请检查编码、分隔符或文件内容。") from error
    if frame.empty:
        file_path.unlink(missing_ok=True)
        raise ValueError("上传的数据集为空，请提供至少一行记录。")
    dataset = Dataset(
        name=name or Path(filename).stem,
        description=description,
        source_type="upload",
        file_path=str(file_path),
        sample_count=len(frame),
        dimension_count=len(frame.columns) - (1 if label_column in frame.columns else 0),
        label_column=label_column if label_column in frame.columns else None,
        meta_info={"originalFilename": filename},
    )
    db.session.add(dataset)
    db.session.commit()
    return serialize_dataset(dataset)


def save_analysis_run(
    dataset_id: int,
    reducer: str,
    algorithm: str,
    preprocess_config: dict,
    algorithm_config: dict,
    quality_metrics: dict,
    performance_metrics: dict,
    result_payload: dict,
    preservation_score: float,
) -> AnalysisRun:
    run = AnalysisRun(
        dataset_id=dataset_id,
        reducer=reducer,
        algorithm=algorithm,
        preprocess_config=preprocess_config,
        algorithm_config=algorithm_config,
        quality_metrics=quality_metrics,
        performance_metrics=performance_metrics,
        result_payload=result_payload,
        preservation_score=preservation_score,
    )
    db.session.add(run)
    db.session.commit()
    return run


def list_analysis_runs() -> list[dict]:
    runs = AnalysisRun.query.order_by(AnalysisRun.created_at.desc()).limit(20).all()
    dataset_map = {dataset.id: dataset.name for dataset in Dataset.query.filter(Dataset.id.in_([run.dataset_id for run in runs])).all()} if runs else {}
    return [
        {
            "id": run.id,
            "datasetId": run.dataset_id,
            "datasetName": dataset_map.get(run.dataset_id),
            "algorithm": run.algorithm,
            "reducer": run.reducer,
            "preservationScore": run.preservation_score,
            "createdAt": run.created_at.isoformat(),
        }
        for run in runs
    ]
