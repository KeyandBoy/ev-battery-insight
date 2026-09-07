# EV Insight Core

核心业务模块目前提供车辆级电池健康评分。输入应为 EV DataForge 输出的标准电池 CSV，可选关联 `vehicles.csv` 获取额定容量。

```powershell
python ev-insight/battery_health.py data/processed/battery_readings.csv --vehicles data/simulated/vehicles.csv --output data/processed/battery_health.csv
```

输出字段包括 `health_score`、`risk_level`、`capacity_score`、`temperature_score`、`voltage_score`、`range_score` 和 `risk_reasons`。

该评分是研究和辅助分析模型，不是车辆安全认证或专业维修诊断结论。
