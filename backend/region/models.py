from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database import db


class Dataset(db.Model):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="generated")
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dimension_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    label_column: Mapped[str | None] = mapped_column(String(64))
    meta_info: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class AnalysisRun(db.Model):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(Integer, nullable=False)
    algorithm: Mapped[str] = mapped_column(String(32), nullable=False)
    reducer: Mapped[str] = mapped_column(String(32), nullable=False)
    preprocess_config: Mapped[dict | None] = mapped_column(JSON)
    algorithm_config: Mapped[dict | None] = mapped_column(JSON)
    quality_metrics: Mapped[dict | None] = mapped_column(JSON)
    performance_metrics: Mapped[dict | None] = mapped_column(JSON)
    result_payload: Mapped[dict | None] = mapped_column(JSON)
    preservation_score: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
