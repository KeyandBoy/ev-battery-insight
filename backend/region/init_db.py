from __future__ import annotations

from app import app
from database import db
from models import Dataset
from services.dataset_service import create_generated_dataset


def main():
    with app.app_context():
        db.create_all()
        existing_types = {
            (dataset.meta_info or {}).get("datasetType")
            for dataset in Dataset.query.all()
            if dataset.meta_info
        }
        for dataset_type in ["gene_expression", "image_features", "finance_behavior"]:
            if dataset_type not in existing_types:
                create_generated_dataset(dataset_type)
        print("数据库初始化完成。")


if __name__ == "__main__":
    main()
