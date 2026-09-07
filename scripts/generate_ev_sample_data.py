"""Generate coherent synthetic EV data for local development and demos."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def generate(output: Path, vehicles: int, seed: int) -> None:
    rng = np.random.default_rng(seed)
    output.mkdir(parents=True, exist_ok=True)
    vehicle_ids = [f"EV{i:06d}" for i in range(1, vehicles + 1)]
    brands = np.array(["Aurora", "Voltix", "E-Motion", "GreenDrive"])
    models = np.array(["A1", "A2", "V1", "V2", "E3", "G1"])
    types = np.array(["LFP", "NMC"])
    risk_types = rng.choice(["healthy", "mileage", "hot", "degraded", "charging", "fault"], vehicles, p=[.45, .15, .12, .1, .1, .08])
    vehicle_frame = pd.DataFrame({
        "vehicle_id": vehicle_ids,
        "brand": rng.choice(brands, vehicles),
        "model": rng.choice(models, vehicles),
        "battery_type": rng.choice(types, vehicles),
        "battery_capacity_kwh": rng.choice([50, 60, 70, 80], vehicles),
        "production_date": pd.date_range("2022-01-01", periods=vehicles, freq="2D").strftime("%Y-%m-%d"),
        "risk_type": risk_types,
    })
    vehicle_frame["total_mileage_km"] = np.round(rng.normal(38000, 18000, vehicles).clip(1000, 140000), 1)
    vehicle_frame.to_csv(output / "vehicles.csv", index=False)

    reading_count = max(vehicles * 12, 120)
    reading_vehicle = rng.choice(vehicle_ids, reading_count)
    risk_by_vehicle = dict(zip(vehicle_ids, risk_types))
    risk = np.array([risk_by_vehicle[v] for v in reading_vehicle])
    mileage = rng.uniform(5000, 140000, reading_count)
    base_temp = np.where(risk == "hot", 46, 29) + rng.normal(0, 3, reading_count)
    retention = np.where(np.isin(risk, ["degraded", "mileage"]), .72, .91) - mileage / 1000000 + rng.normal(0, .025, reading_count)
    readings = pd.DataFrame({
        "vehicle_id": reading_vehicle,
        "timestamp": pd.date_range("2025-01-01", periods=reading_count, freq="6h").strftime("%Y-%m-%dT%H:%M:%SZ"),
        "voltage_v": np.round(rng.normal(365, 8, reading_count), 3),
        "current_a": np.round(rng.normal(42, 14, reading_count), 3),
        "temperature_c": np.round(base_temp, 3),
        "soc_percent": np.round(rng.uniform(15, 95, reading_count), 2),
        "remaining_capacity_kwh": np.round(retention * 60, 3),
        "estimated_range_km": np.round(retention * 480 + rng.normal(0, 12, reading_count), 2),
        "mileage_km": np.round(mileage, 1),
    })
    readings.to_csv(output / "battery_readings.csv", index=False)

    charge_count = max(vehicles * 8, 80)
    charge_vehicle = rng.choice(vehicle_ids, charge_count)
    charge_risk = np.array([risk_by_vehicle[v] for v in charge_vehicle])
    charging = pd.DataFrame({
        "charge_id": [f"CHG{i:07d}" for i in range(1, charge_count + 1)],
        "vehicle_id": charge_vehicle,
        "station_id": rng.choice(["ST001", "ST002", "ST003", "ST004"], charge_count),
        "start_time": pd.date_range("2025-02-01", periods=charge_count, freq="3h").strftime("%Y-%m-%dT%H:%M:%SZ"),
        "charge_duration_min": np.round(np.where(charge_risk == "charging", rng.normal(95, 12, charge_count), rng.normal(48, 8, charge_count)).clip(15, 150), 1),
        "start_soc_percent": np.round(rng.uniform(10, 45, charge_count), 2),
        "end_soc_percent": np.round(rng.uniform(70, 98, charge_count), 2),
        "average_power_kw": np.round(rng.normal(55, 9, charge_count).clip(10, 100), 2),
        "max_temperature_c": np.round(np.where(charge_risk == "hot", rng.normal(51, 3, charge_count), rng.normal(38, 4, charge_count)), 2),
        "charging_status": "completed",
    })
    charging.to_csv(output / "charging_records.csv", index=False)

    fault_vehicle = rng.choice(vehicle_ids, max(vehicles, 50))
    fault_risk = np.array([risk_by_vehicle[v] for v in fault_vehicle])
    faults = pd.DataFrame({
        "fault_id": [f"FLT{i:06d}" for i in range(1, len(fault_vehicle) + 1)],
        "vehicle_id": fault_vehicle,
        "fault_time": pd.date_range("2025-03-01", periods=len(fault_vehicle), freq="8h").strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fault_type": np.where(fault_risk == "hot", "battery_temperature", np.where(fault_risk == "charging", "charging_efficiency", "none")),
        "fault_level": np.where(np.isin(fault_risk, ["hot", "degraded", "fault"]), "high", "low"),
        "repair_status": rng.choice(["pending", "resolved", "review"], len(fault_vehicle)),
    })
    faults.to_csv(output / "fault_records.csv", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/simulated"))
    parser.add_argument("--vehicles", type=int, default=500)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    generate(args.output, args.vehicles, args.seed)
    print(f"Generated synthetic EV data in {args.output}")
