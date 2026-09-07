"""Prepare small upload fixtures from a public EV population CSV."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "raw" / "electric_vehicle_population_public.csv"
OUTPUT = ROOT / "data" / "processed"
LIMIT = 200


def number(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def main() -> None:
    vehicles = []
    with SOURCE.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            vehicle_key = row.get("DOL Vehicle ID", "").strip()
            electric_range_miles = number(row.get("Electric Range", ""))
            if not vehicle_key or electric_range_miles <= 0:
                continue
            electric_range = round(electric_range_miles * 1.60934, 2)
            vehicle_id = f"WA-{vehicle_key}"
            battery_type = "BEV" if "Battery Electric" in row.get("Electric Vehicle Type", "") else "PHEV"
            # The source has range but no rated capacity, so this is a documented test estimate.
            capacity = round(max(20.0, min(120.0, electric_range / 5.5)), 2)
            vehicles.append({
                "vehicle_id": vehicle_id,
                "brand": row.get("Make", "").strip(),
                "model": row.get("Model", "").strip(),
                "battery_type": battery_type,
                "battery_capacity_kwh": capacity,
                "model_year": row.get("Model Year", "").strip(),
                "electric_range_km": electric_range,
                "state": row.get("State", "").strip(),
            })
            if len(vehicles) >= LIMIT:
                break

    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / "public_ev_vehicles.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = list(vehicles[0])
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(vehicles)

    with (OUTPUT / "public_ev_readings.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = ["vehicle_id", "temperature_c", "voltage_v", "remaining_capacity_kwh", "estimated_range_km"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for index, vehicle in enumerate(vehicles):
            base = vehicle["battery_capacity_kwh"]
            source_range = vehicle["electric_range_km"]
            for sample in range(4):
                factor = 0.76 + ((index * 7 + sample * 3) % 20) / 100
                temperature = 25 + ((index * 11 + sample * 5) % 19)
                voltage = round(360 + ((index * 13 + sample * 2) % 16) / 10, 2)
                writer.writerow({
                    "vehicle_id": vehicle["vehicle_id"],
                    "temperature_c": temperature,
                    "voltage_v": voltage,
                    "remaining_capacity_kwh": round(base * factor, 2),
                    "estimated_range_km": round(source_range * factor, 2),
                })

    print(f"Prepared {len(vehicles)} vehicles and {len(vehicles) * 4} readings in {OUTPUT}")


if __name__ == "__main__":
    main()
