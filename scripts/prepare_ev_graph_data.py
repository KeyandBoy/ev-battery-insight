"""Build a rich vehicle battery relationship graph for Chain-Connect."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ev_insight import score_battery_health  # noqa: E402

VEHICLES = ROOT / "data" / "processed" / "public_ev_vehicles.csv"
READINGS = ROOT / "data" / "processed" / "public_ev_readings.csv"
OUTPUT = ROOT / "data" / "processed" / "public_ev_battery_network.json"


CATEGORIES = [
    {"name": "品牌群组"},
    {"name": "电池规格"},
    {"name": "风险状态"},
]

RISK_KEYS = {"高风险": "high", "关注": "attention", "良好": "good", "健康": "healthy"}


def safe_id(prefix: str, value: object) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(value).strip()).strip("_")
    return f"{prefix}_{normalized or 'unknown'}"


def add_node(nodes: dict[str, dict], node_id: str, name: str, category: int, value: float, desc: str) -> None:
    nodes[node_id] = {"id": node_id, "name": name, "category": category, "value": round(value, 2), "desc": desc}


def main() -> None:
    vehicles = pd.read_csv(VEHICLES).fillna("")
    readings = pd.read_csv(READINGS)
    readings["temperature_c"] = pd.to_numeric(readings["temperature_c"], errors="coerce")
    readings["estimated_range_km"] = pd.to_numeric(readings["estimated_range_km"], errors="coerce")
    metrics = score_battery_health(readings, vehicles)[[
        "vehicle_id", "health_score", "risk_level", "mean_temperature_c", "max_temperature_c"
    ]]
    frame = vehicles.merge(metrics, on="vehicle_id", how="left")
    nodes: dict[str, dict] = {}
    links: list[dict] = []

    def connect(source: str, target: str, relation: str, value: float = 1) -> None:
        links.append({"source": source, "target": target, "value": round(float(value), 2), "relation": relation})

    # Similar vehicles are represented by one brand-group node instead of one node per VIN or model.
    frame["capacity_group"] = frame["battery_type"].astype(str) + " " + (frame["battery_capacity_kwh"] / 20).round().clip(lower=1).mul(20).astype(int).astype(str) + "kWh级"
    grouped = frame.groupby("brand", dropna=False)
    for brand_name, group in grouped:
        brand_name = str(brand_name)
        brand = safe_id("brand", brand_name)
        add_node(nodes, brand, brand_name, 0, len(group), f"{len(group)}辆车，平均健康分 {group.health_score.mean():.1f}，覆盖 {group.model.nunique()} 个车型")
        for battery_name, battery_group in group.groupby("capacity_group"):
            battery = safe_id("battery", battery_name)
            add_node(nodes, battery, str(battery_name), 1, int(frame["capacity_group"].eq(battery_name).sum()), "按电池类型和容量区间合并")
            connect(brand, battery, "电池规格", len(battery_group))
        for risk, risk_group in group.groupby("risk_level"):
            risk_id = safe_id("risk", RISK_KEYS[str(risk)])
            add_node(nodes, risk_id, str(risk), 2, int(frame["risk_level"].eq(risk).sum()), f"{int(frame['risk_level'].eq(risk).sum())}辆车处于该状态")
            connect(brand, risk_id, "风险状态", len(risk_group))

    graph = {
        "name": "新能源汽车电池健康与充电风险关系网络",
        "description": "由公开新能源汽车车辆数据整理生成的深度聚合关系网络。相同品牌、电池规格和风险状态合并为群组，健康指标为测试派生值。",
        "source": "Electric Vehicle Population Data",
        "nodes": list(nodes.values()),
        "links": links,
        "categories": CATEGORIES,
    }
    OUTPUT.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Built {len(graph['nodes'])} nodes and {len(graph['links'])} links -> {OUTPUT}")


if __name__ == "__main__":
    main()
