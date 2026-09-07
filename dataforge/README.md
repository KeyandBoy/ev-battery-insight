# EV DataForge

EV DataForge 是新能源汽车数据准备辅助工具，负责字段识别、字段映射、单位统一、缺失值处理、重复值检测、异常标记和质量报告生成。

## 使用方式

```powershell
python dataforge/cli.py input.csv --output data/processed/battery_readings.csv

# 可选：删除超出业务范围的异常行（默认只标记并保留）
python dataforge/cli.py input.csv --output data/processed/battery_readings.csv --drop-anomalies
```

工具会同时生成同名的 `.quality.json` 质量报告。默认会去重、统一字段名和单位、处理数值缺失、清除空车辆编号，并将业务异常标记在结果中；使用 `--drop-anomalies` 才会删除超出配置范围的异常行。

## 当前支持的标准字段

`vehicle_id`、`timestamp`、`temperature_c`、`voltage_v`、`current_a`、`soc_percent`、`remaining_capacity_kwh`、`estimated_range_km`、`mileage_km`、`power_kw`。
