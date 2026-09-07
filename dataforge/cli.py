"""EV DataForge: normalize a battery CSV and emit a quality report."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd


ALIASES = {
    "vehicle_id": {"vehicle_id", "vehicleid", "vehicle_no", "vehicle_number", "car_id", "vin"},
    "timestamp": {"timestamp", "time", "datetime", "date_time", "record_time"},
    "temperature_c": {"temp", "temperature", "battery_temp", "battery_temperature", "temperature_c"},
    "voltage_v": {"voltage", "cell_voltage", "battery_voltage", "voltage_v"},
    "current_a": {"current", "battery_current", "current_a"},
    "soc_percent": {"soc", "state_of_charge", "charge_level", "soc_percent"},
    "remaining_capacity_kwh": {"capacity", "remaining_capacity", "battery_capacity", "remaining_capacity_kwh"},
    "estimated_range_km": {"range", "estimated_range", "range_km", "estimated_range_km"},
    "mileage_km": {"mileage", "odometer", "distance", "mileage_km"},
    "power_kw": {"power", "charging_power", "power_kw"},
}


def normalize_name(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "_", str(value).strip().lower())
    return value.strip("_")


def infer_standard_name(column: str) -> str | None:
    normalized = normalize_name(column)
    for standard, aliases in ALIASES.items():
        if normalized in aliases:
            return standard
    return None


def convert_units(frame: pd.DataFrame, source: Path) -> list[str]:
    warnings: list[str] = []
    if "timestamp" in frame:
        parsed = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
        invalid = int(parsed.isna().sum())
        frame["timestamp"] = parsed.dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        if invalid:
            warnings.append(f"timestamp 有 {invalid} 条记录无法解析")
    for column in frame.columns:
        if column == "soc_percent":
            values = pd.to_numeric(frame[column], errors="coerce")
            if values.dropna().max() is not None and values.dropna().max() <= 1:
                frame[column] = values * 100
            else:
                frame[column] = values
        elif column in {"temperature_c", "voltage_v", "current_a", "remaining_capacity_kwh", "estimated_range_km", "mileage_km", "power_kw"}:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return warnings


def clean_file(input_path: Path, output_path: Path) -> dict:
    source = pd.read_csv(input_path)
    original_rows, original_columns = len(source), list(source.columns)
    mappings = {}
    selected = {}
    for column in source.columns:
        standard = infer_standard_name(column)
        if standard and standard not in selected:
            selected[standard] = source[column]
            mappings[column] = standard
    frame = pd.DataFrame(selected)
    warnings = convert_units(frame, input_path)
    duplicate_rows = int(frame.duplicated().sum())
    frame = frame.drop_duplicates().reset_index(drop=True)
    missing_before = float(frame.isna().mean().mean()) if not frame.empty else 0.0
    for column in frame.select_dtypes(include="number").columns:
        frame[column] = frame[column].interpolate(limit_direction="both")
    invalid_ranges = {}
    ranges = {"soc_percent": (0, 100), "temperature_c": (-50, 100), "voltage_v": (0, 1000), "current_a": (-1000, 1000)}
    for column, (low, high) in ranges.items():
        if column in frame:
            invalid = (frame[column] < low) | (frame[column] > high)
            invalid_ranges[column] = int(invalid.sum())
            frame[f"{column}_business_anomaly"] = invalid
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)
    quality = {
        "source_file": str(input_path),
        "input_rows": original_rows,
        "output_rows": len(frame),
        "input_columns": original_columns,
        "mapped_columns": mappings,
        "unmapped_columns": [column for column in original_columns if column not in mappings],
        "duplicate_rows_removed": duplicate_rows,
        "missing_ratio_after_cleaning": float(frame.isna().mean().mean()) if not frame.empty else 0.0,
        "missing_ratio_before_cleaning": missing_before,
        "business_anomalies": invalid_ranges,
        "warnings": warnings,
    }
    quality["quality_score"] = max(0.0, min(1.0, 1 - quality["missing_ratio_after_cleaning"] - min(0.3, duplicate_rows / max(original_rows, 1))))
    report_path = output_path.with_suffix(output_path.suffix + ".quality.json")
    report_path.write_text(json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8")
    return quality


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize an EV battery CSV and create a quality report.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = clean_file(args.input, args.output)
    print(json.dumps({"output": str(args.output), "quality_score": result["quality_score"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
