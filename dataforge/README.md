# EV DataForge

EV DataForge 是新能源汽车数据准备辅助工具，负责字段识别、字段映射、单位统一、缺失值处理、重复值检测、异常标记和质量报告生成。

## 使用方式

```powershell
python dataforge/cli.py input.csv --output data/processed/battery_readings.csv
```

工具会同时生成同名的 `.quality.json` 质量报告。业务风险异常会被保留并标记，不会被无条件删除。

## 当前支持的标准字段

`vehicle_id`、`timestamp`、`temperature_c`、`voltage_v`、`current_a`、`soc_percent`、`remaining_capacity_kwh`、`estimated_range_km`、`mileage_km`、`power_kw`。
