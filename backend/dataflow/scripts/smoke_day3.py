"""
"""

import io
import json
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app
from app.extensions import db
from app.models import DataRecord


def check(ok, message):
    if not ok:
        raise RuntimeError(message)


def _worst_ratio(node):
    width = max(float(node.get("width") or 0.0), 1e-6)
    height = max(float(node.get("height") or 0.0), 1e-6)
    return max(width / height, height / width)


def main():
    app = create_app("testing")
    with app.app_context():
        db.drop_all()
        db.create_all()
        client = app.test_client()

        register_resp = client.post(
            "/api/auth/register",
            json={"username": "smoke_user", "password": "123456", "email": "smoke@example.com"},
        )
        check(register_resp.status_code == 200, "register failed")

        login_resp = client.post(
            "/api/auth/login",
            json={"username": "smoke_user", "password": "123456"},
        )
        check(login_resp.status_code == 200, "login failed")
        token = login_resp.json["data"]["access_token"]
        headers = {"Authorization": "Bearer {0}".format(token)}

        csv_bytes = (
            "Category,Subcategory,Item,Value\n"
            "Electronics,Phone,iPhone,100\n"
            "Electronics,Phone,Xiaomi,80\n"
            "Electronics,Laptop,MacBook,60\n"
            "Appliance,Air Conditioner,Gree,70\n"
            "Appliance,Fridge,Haier,50\n"
        ).encode("utf-8")
        upload_payload = {
            "name": "smoke_dataset",
            "hierarchy_fields": "Category,Subcategory,Item",
            "value_field": "Value",
            "file": (io.BytesIO(csv_bytes), "smoke.csv"),
        }
        upload_resp = client.post(
            "/api/datasets/upload",
            headers=headers,
            data=upload_payload,
            content_type="multipart/form-data",
        )
        check(upload_resp.status_code == 200, "dataset upload failed")
        dataset_id = upload_resp.json["data"]["dataset"]["id"]

        preview_resp = client.get(
            "/api/datasets/{0}/preview?limit=20".format(dataset_id),
            headers=headers,
        )
        check(preview_resp.status_code == 200, "dataset preview failed")
        processed_preview = preview_resp.json["data"]["processed_preview"]
        check(processed_preview["rows"], "processed preview rows missing")
        check(
            "parent_id" in processed_preview["columns"] and "node_key" in processed_preview["columns"],
            "processed preview columns incomplete",
        )
        check(
            any(row.get("parent_id") is not None for row in processed_preview["rows"]),
            "processed preview should expose parent-child relations in the first page",
        )

        tree_resp = client.get("/api/analysis/tree?dataset_id={0}".format(dataset_id), headers=headers)
        features_resp = client.get("/api/analysis/features?dataset_id={0}".format(dataset_id), headers=headers)
        treemap_resp = client.get(
            "/api/analysis/treemap?dataset_id={0}&width=960&height=560&padding=1".format(dataset_id),
            headers=headers,
        )
        pca_resp = client.get(
            "/api/analysis/pca?dataset_id={0}&max_rows=120&max_features=4".format(dataset_id),
            headers=headers,
        )
        check(tree_resp.status_code == 200, "tree analysis failed")
        check(features_resp.status_code == 200, "features analysis failed")
        check(treemap_resp.status_code == 200, "treemap analysis failed")
        check(pca_resp.status_code == 200, "pca analysis failed")

        stored_records = DataRecord.query.filter_by(dataset_id=dataset_id).all()
        deep_records = [record for record in stored_records if int(record.level or 0) > 0]
        check(deep_records, "missing nested records after preprocessing")
        check(all(record.parent_id is not None for record in deep_records), "nested records missing parent_id")
        check(
            all(
                isinstance(record.raw_payload, dict)
                and isinstance(record.raw_payload.get("path_labels"), list)
                and record.raw_payload.get("path_key")
                for record in stored_records
            ),
            "tree path metadata missing",
        )

        treemap_nodes = treemap_resp.json["data"]["nodes"]
        root_nodes = [node for node in treemap_nodes if node.get("parent_id") is None]
        check(root_nodes, "treemap root nodes missing")
        worst_root_ratio = max(_worst_ratio(node) for node in root_nodes)
        check(worst_root_ratio <= 5.0, "treemap root aspect ratio is too extreme")

        skew_csv_bytes = (
            "L1,L2,L3,Value\n"
            "A,B1,C1,1000\n"
            "A,B2,C2,1\n"
            "A,B3,C3,1\n"
            "A,B4,C4,1\n"
            "A,B5,C5,1\n"
            "A,B6,C6,1\n"
        ).encode("utf-8")
        skew_upload_resp = client.post(
            "/api/datasets/upload",
            headers=headers,
            data={
                "name": "skew_dataset",
                "hierarchy_fields": "L1,L2,L3",
                "value_field": "Value",
                "file": (io.BytesIO(skew_csv_bytes), "skew.csv"),
            },
            content_type="multipart/form-data",
        )
        check(skew_upload_resp.status_code == 200, "skew dataset upload failed")
        skew_dataset_id = skew_upload_resp.json["data"]["dataset"]["id"]
        skew_treemap_resp = client.get(
            "/api/analysis/treemap?dataset_id={0}&width=960&height=560&padding=1&top_n=240&min_ratio=0.002".format(
                skew_dataset_id
            ),
            headers=headers,
        )
        check(skew_treemap_resp.status_code == 200, "skew treemap analysis failed")
        skew_payload = skew_treemap_resp.json["data"]
        skew_nodes = skew_payload["nodes"]
        check(skew_nodes, "skew treemap nodes missing")
        skew_worst_ratio = max(_worst_ratio(node) for node in skew_nodes)
        check(skew_worst_ratio <= 10.0, "skew treemap still contains unreadable thin blocks")
        check(
            int(skew_payload["layout_meta"].get("hidden_other_nodes") or 0) >= 1,
            "skew treemap should hide over-thin aggregated other blocks",
        )

        create_dashboard_resp = client.post(
            "/api/dashboards",
            headers=headers,
            json={"name": "smoke_dashboard", "canvas_width": 1280, "canvas_height": 720},
        )
        check(create_dashboard_resp.status_code == 200, "dashboard create failed")
        dashboard_id = create_dashboard_resp.json["data"]["id"]

        layout_payload = {
            "layout_json": {"version": "v0.3-day3"},
            "components": [
                {
                    "type": "treemap",
                    "title": "Sales Treemap",
                    "x": 20,
                    "y": 20,
                    "w": 560,
                    "h": 320,
                    "z_index": 1,
                    "dataset_id": dataset_id,
                    "config_json": {"color": "#5b8cd9"},
                    "binding_json": {"dimension": "Category", "metric": "Value"},
                },
                {
                    "type": "bar",
                    "title": "Grouped Stats",
                    "x": 600,
                    "y": 20,
                    "w": 420,
                    "h": 260,
                    "z_index": 2,
                    "dataset_id": dataset_id,
                    "config_json": {"color": "#4f82cd"},
                    "binding_json": {"dimension": "Subcategory", "metric": "Value"},
                },
            ],
        }
        save_layout_resp = client.put(
            "/api/dashboards/{0}/layout".format(dashboard_id),
            headers=headers,
            json=layout_payload,
        )
        check(save_layout_resp.status_code == 200, "dashboard layout save failed")
        check(len(save_layout_resp.json["data"]["components"]) == 2, "dashboard component count mismatch")

        publish_resp = client.put(
            "/api/dashboards/{0}/publish".format(dashboard_id),
            headers=headers,
            json={"is_published": 1},
        )
        check(publish_resp.status_code == 200, "dashboard publish failed")

        detail_resp = client.get("/api/dashboards/{0}".format(dashboard_id), headers=headers)
        check(detail_resp.status_code == 200, "dashboard detail failed")
        check(int(detail_resp.json["data"]["is_published"]) == 1, "publish state not applied")

        list_resp = client.get("/api/dashboards?page=1&page_size=20", headers=headers)
        check(list_resp.status_code == 200, "dashboard list failed")

        delete_resp = client.delete("/api/dashboards/{0}".format(dashboard_id), headers=headers)
        check(delete_resp.status_code == 200, "dashboard delete failed")

        summary = {
            "dataset_id": dataset_id,
            "dashboard_id": dashboard_id,
            "analysis_nodes": len(treemap_nodes),
            "root_worst_ratio": round(worst_root_ratio, 4),
            "skew_worst_ratio": round(skew_worst_ratio, 4),
            "deep_record_count": len(deep_records),
            "pca_samples": pca_resp.json["data"]["pca"]["sample_count"],
            "dashboard_total_after_create": list_resp.json["pagination"]["total"],
        }
        print(json.dumps({"ok": True, "summary": summary}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        sys.exit(1)
