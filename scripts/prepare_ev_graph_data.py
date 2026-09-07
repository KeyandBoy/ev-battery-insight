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
    {"name": "车辆"},
    {"name": "电池"},
    {"name": "车型"},
    {"name": "品牌"},
    {"name": "地区"},
    {"name": "风险状态"},
]

RISK_KEYS = {"高风险": "high", "关注": "attention", "良好": "good", "健康": "healthy"}


def safe_id(prefix: str, value: object) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(value).strip()).strip("_")
    return f"{prefix}_{normalized or 'unknown'}"


def add_node(nodes: dict[str, dict], node_id: str, name: str, category: int, value: float, desc: str) -> None:
    if node_id not in nodes:
        nodes[node_id] = {"id": node_id, "name": name, "category": category, "value": round(value, 2), "desc": desc}
    else:
        nodes[node_id]["value"] = round(nodes[node_id]["value"] + value, 2)


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

    for row in frame.itertuples(index=False):
        health = float(row.health_score)
        risk = str(row.risk_level)
        vehicle = safe_id("vehicle", row.vehicle_id)
        battery_name = f"{row.battery_type} {float(row.battery_capacity_kwh):.0f}kWh级"
        battery = safe_id("battery", battery_name)
        model = safe_id("model", f"{row.brand}-{row.model}")
        brand = safe_id("brand", row.brand)
        state = safe_id("state", row.state)
        risk_id = safe_id("risk", RISK_KEYS[risk])
        add_node(nodes, vehicle, str(row.vehicle_id), 0, health, f"健康分 {health:.1f}，平均温度 {row.mean_temperature_c:.1f}°C，最高温度 {row.max_temperature_c:.1f}°C")
        add_node(nodes, battery, battery_name, 1, float(row.battery_capacity_kwh), "按电池类型和额定容量分组")
        add_node(nodes, model, f"{row.brand} {row.model}", 2, 1, f"车型年份 {row.model_year}，续航 {row.electric_range_km:.0f} km")
        add_node(nodes, brand, str(row.brand), 3, 1, "制造商品牌")
        add_node(nodes, state, str(row.state), 4, 1, "车辆登记地区")
        add_node(nodes, risk_id, risk, 5, 1, f"健康评分区间：{risk}")
        connect(vehicle, battery, "搭载电池", health / 20)
        connect(vehicle, model, "车型", 2)
        connect(vehicle, brand, "品牌", 1)
        connect(vehicle, state, "登记地区", 1)
        connect(vehicle, risk_id, "风险状态", max(1, (100 - health) / 10))

    graph = {
        "name": "新能源汽车电池健康与充电风险关系网络",
        "description": "由公开新能源汽车车辆数据整理生成，展示车辆、电池、车型、品牌、地区和风险状态之间的关联。健康指标为测试派生值。",
        "source": "Electric Vehicle Population Data",
        "nodes": list(nodes.values()),
        "links": links,
        "categories": CATEGORIES,
    }
    OUTPUT.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Built {len(graph['nodes'])} nodes and {len(graph['links'])} links -> {OUTPUT}")


if __name__ == "__main__":
    main()
