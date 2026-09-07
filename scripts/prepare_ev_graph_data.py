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
    {"name": "车型群组"},
    {"name": "电池"},
    {"name": "品牌"},
    {"name": "地区"},
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

    # Similar vehicles are represented by one model-group node instead of one node per VIN.
    frame["model_group"] = frame["brand"].astype(str) + " " + frame["model"].astype(str)
    frame["capacity_group"] = frame["battery_type"].astype(str) + " " + (frame["battery_capacity_kwh"] / 20).round().clip(lower=1).mul(20).astype(int).astype(str) + "kWh级"
    grouped = frame.groupby("model_group", dropna=False)
    for model_name, group in grouped:
        model = safe_id("model", model_name)
        brand_name = str(group["brand"].mode().iloc[0])
        battery_name = str(group["capacity_group"].mode().iloc[0])
        state_name = str(group["state"].mode().iloc[0])
        brand = safe_id("brand", brand_name)
        battery = safe_id("battery", battery_name)
        state = safe_id("state", state_name)
        add_node(nodes, model, model_name, 0, len(group), f"{len(group)}辆车，平均健康分 {group.health_score.mean():.1f}，平均续航 {group.electric_range_km.mean():.0f} km")
        add_node(nodes, battery, battery_name, 1, int(frame["capacity_group"].eq(battery_name).sum()), "按电池类型和容量区间合并")
        add_node(nodes, brand, brand_name, 2, int(frame["brand"].eq(brand_name).sum()), "制造商品牌合并节点")
        add_node(nodes, state, state_name, 3, int(frame["state"].eq(state_name).sum()), "登记地区合并节点")
        connect(model, battery, "电池类型", len(group))
        connect(model, brand, "品牌", len(group))
        connect(model, state, "地区", len(group))
        for risk, risk_group in group.groupby("risk_level"):
            risk_id = safe_id("risk", RISK_KEYS[str(risk)])
            add_node(nodes, risk_id, str(risk), 4, int(frame["risk_level"].eq(risk).sum()), f"{int(frame['risk_level'].eq(risk).sum())}辆车处于该状态")
            connect(model, risk_id, "风险状态", len(risk_group))

    graph = {
        "name": "新能源汽车电池健康与充电风险关系网络",
        "description": "由公开新能源汽车车辆数据整理生成的聚合关系网络。相同车型合并为车型群组，电池容量、品牌、地区和风险状态也按类别合并，健康指标为测试派生值。",
        "source": "Electric Vehicle Population Data",
        "nodes": list(nodes.values()),
        "links": links,
        "categories": CATEGORIES,
    }
    OUTPUT.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Built {len(graph['nodes'])} nodes and {len(graph['links'])} links -> {OUTPUT}")


if __name__ == "__main__":
    main()
