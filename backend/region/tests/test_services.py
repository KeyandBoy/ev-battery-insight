from __future__ import annotations

from io import BytesIO

from werkzeug.datastructures import FileStorage

from app import app
from models import AnalysisRun, Dataset
from services.dataset_service import create_uploaded_dataset
from services.clustering import cluster_regions
from services.dimensionality import reduce_dimensions
from services.metrics import evaluate_clustering
from services.preprocess import preprocess_dataset
from services.visualization import build_visualization_payload
from utils.sample_data import create_gene_expression_dataset


def test_full_analysis_pipeline():
    synthetic = create_gene_expression_dataset(samples=120, dimensions=12)
    result = preprocess_dataset(
        synthetic.frame,
        {
            "labelColumn": "label",
            "missingStrategy": "median",
            "scaler": "standard",
            "varianceThreshold": 0.01,
            "correlationThreshold": 0.97,
            "maxFeatures": 10,
        },
    )
    matrix = result.processed_frame[result.feature_columns].to_numpy()
    embedding, reduction_metrics = reduce_dimensions(matrix, {"method": "pca"})
    labels, cluster_metrics = cluster_regions(matrix, embedding, {"method": "dbscan", "eps": 1.2, "minSamples": 5})
    quality = evaluate_clustering(matrix, labels, reduction_metrics, cluster_metrics)
    payload = build_visualization_payload(
        raw_frame=synthetic.frame.fillna(synthetic.frame.median(numeric_only=True)),
        processed_frame=result.processed_frame,
        feature_columns=result.feature_columns,
        embedding=embedding,
        labels=labels,
        cluster_metrics=cluster_metrics,
        quality_metrics=quality,
    )

    assert len(payload["points"]) == len(synthetic.frame)
    assert "parallelCoordinates" in payload
    assert quality["preservationScore"] >= 0


def test_tsne_handles_small_sample_perplexity():
    synthetic = create_gene_expression_dataset(samples=8, dimensions=6)
    result = preprocess_dataset(synthetic.frame, {"labelColumn": "label", "scaler": "standard"})
    matrix = result.processed_frame[result.feature_columns].to_numpy()
    embedding, metrics = reduce_dimensions(matrix, {"method": "tsne", "perplexity": 30, "nComponents": 2})

    assert embedding.shape == (8, 2)
    assert metrics["method"] == "tsne"


def test_upload_dataset_rejects_non_csv_extension():
    file = FileStorage(stream=BytesIO(b"demo"), filename="invalid.txt")

    try:
        create_uploaded_dataset("invalid", "bad", file)
    except ValueError as error:
        assert "CSV" in str(error)
    else:  # pragma: no cover
        raise AssertionError("Expected ValueError for non-CSV upload")


def test_dataset_summary_and_compare_endpoints():
    client = app.test_client()

    with app.app_context():
        dataset = Dataset.query.first()
        if dataset is None:
            raise AssertionError("Expected initialized datasets in database")
        run_count = AnalysisRun.query.count()

    summary_response = client.get(f"/api/datasets/{dataset.id}/summary")
    assert summary_response.status_code == 200
    summary = summary_response.get_json()
    assert "missingOverview" in summary
    assert "featureOverview" in summary

    if run_count < 2:
        for _ in range(2 - run_count):
            run_response = client.post(
                "/api/analysis/run",
                json={
                    "datasetId": dataset.id,
                    "preprocess": {
                        "labelColumn": "label",
                        "missingStrategy": "median",
                        "scaler": "standard",
                        "varianceThreshold": 0.01,
                        "correlationThreshold": 0.97,
                        "maxFeatures": 10,
                    },
                    "reduction": {"method": "pca", "nComponents": 2},
                    "clustering": {"method": "dbscan", "eps": 1.2, "minSamples": 5},
                },
            )
            assert run_response.status_code == 200

    runs_response = client.get("/api/analysis/runs")
    runs = runs_response.get_json()["items"]
    compare_response = client.post("/api/analysis/compare", json={"runIds": [runs[0]["id"], runs[1]["id"]]})
    assert compare_response.status_code == 200
    compare_data = compare_response.get_json()
    assert "metrics" in compare_data

    detail_response = client.get(f"/api/analysis/runs/{runs[0]['id']}")
    assert detail_response.status_code == 200
    assert "run" in detail_response.get_json()

    export_response = client.get(f"/api/analysis/runs/{runs[0]['id']}/export?format=csv")
    assert export_response.status_code == 200
    assert "id,x,y,region,density,label" in export_response.get_data(as_text=True)

    benchmark_response = client.post(
        "/api/analysis/benchmark",
        json={
            "datasetId": dataset.id,
            "repeats": 1,
            "preprocess": {"labelColumn": "label", "maxFeatures": 8},
            "reduction": {"method": "pca", "nComponents": 2},
            "clustering": {"method": "dbscan", "eps": 1.2, "minSamples": 5},
        },
    )
    assert benchmark_response.status_code == 200
    benchmark_data = benchmark_response.get_json()
    assert benchmark_data["scenarioCount"] >= 1
    assert "summary" in benchmark_data
