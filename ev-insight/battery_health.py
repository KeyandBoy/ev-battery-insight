"""Explainable vehicle-level battery health scoring for EV-Battery Insight."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return float(max(low, min(high, value)))


def score_battery_health(readings: pd.DataFrame, vehicles: pd.DataFrame | None = None) -> pd.DataFrame:
    frame = readings.copy()
    if "vehicle_id" not in frame.columns:
        raise ValueError("电池数据必须包含 vehicle_id 字段")
    if vehicles is not None and "vehicle_id" in vehicles.columns:
        capacity = vehicles[["vehicle_id", "battery_capacity_kwh"]].drop_duplicates("vehicle_id")
        frame = frame.merge(capacity, on="vehicle_id", how="left")
    elif "battery_capacity_kwh" not in frame.columns:
        frame["battery_capacity_kwh"] = np.nan

    for column in ["temperature_c", "voltage_v", "remaining_capacity_kwh", "estimated_range_km", "battery_capacity_kwh"]:
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

    rows = []
    for vehicle_id, group in frame.groupby("vehicle_id", sort=True):
        temperature = group.get("temperature_c", pd.Series(dtype=float)).dropna()
        voltage = group.get("voltage_v", pd.Series(dtype=float)).dropna()
        capacity = group.get("remaining_capacity_kwh", pd.Series(dtype=float)).dropna()
        rated = group.get("battery_capacity_kwh", pd.Series(dtype=float)).dropna()
        ranges = group.get("estimated_range_km", pd.Series(dtype=float)).dropna()

        mean_temp = float(temperature.mean()) if not temperature.empty else 30.0
        max_temp = float(temperature.max()) if not temperature.empty else 30.0
        voltage_std = float(voltage.std(ddof=0)) if len(voltage) > 1 else 0.0
        capacity_retention = float(capacity.mean() / rated.mean()) if not capacity.empty and not rated.empty and rated.mean() > 0 else np.nan
        capacity_score = clamp(capacity_retention * 100) if not np.isnan(capacity_retention) else 75.0
        temperature_score = clamp(100 - max(0, mean_temp - 30) * 4 - max(0, max_temp - 45) * 3)
        voltage_score = clamp(100 - voltage_std * 8)
        range_score = clamp((float(ranges.mean()) / (rated.mean() * 6) * 100)) if not ranges.empty and not rated.empty and rated.mean() > 0 else 75.0
        health_score = round(0.35 * capacity_score + 0.25 * range_score + 0.2 * temperature_score + 0.2 * voltage_score, 2)

        reasons = []
        if capacity_score < 75:
            reasons.append("容量保持率偏低")
        if max_temp > 45:
            reasons.append("存在高温记录")
        if voltage_std > 3:
            reasons.append("电压波动较大")
        if range_score < 75:
            reasons.append("估算续航偏低")
        if not reasons:
            reasons.append("未发现明显风险")
        risk_level = "健康" if health_score >= 90 else "良好" if health_score >= 75 else "关注" if health_score >= 60 else "高风险"
        rows.append({
            "vehicle_id": vehicle_id,
            "sample_count": len(group),
            "health_score": health_score,
            "risk_level": risk_level,
            "capacity_score": round(capacity_score, 2),
            "range_score": round(range_score, 2),
            "temperature_score": round(temperature_score, 2),
            "voltage_score": round(voltage_score, 2),
            "mean_temperature_c": round(mean_temp, 2),
            "max_temperature_c": round(max_temp, 2),
            "voltage_std": round(voltage_std, 4),
            "capacity_retention": round(float(capacity_retention), 4) if not np.isnan(capacity_retention) else None,
            "risk_reasons": "；".join(reasons),
        })
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Score vehicle battery health from standardized EV data.")
    parser.add_argument("readings", type=Path)
    parser.add_argument("--vehicles", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    readings = pd.read_csv(args.readings)
    vehicles = pd.read_csv(args.vehicles) if args.vehicles else None
    result = score_battery_health(readings, vehicles)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(f"Scored {len(result)} vehicles -> {args.output}")


if __name__ == "__main__":
    main()
