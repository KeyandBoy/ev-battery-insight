# 测试数据

`public_ev_vehicles.csv` 和 `public_ev_readings.csv` 是由公开的 Electric Vehicle Population Data 前 200 条有效记录整理生成的上传测试文件。

`public_ev_battery_network.json` 是面向关系网络可视化的多层聚合图数据，可直接在 Chain-Connect 的“导入 JSON”中上传，也会在服务重新初始化时作为示例数据集出现。相同车型、电池容量区间、品牌、地区和风险状态已合并，避免节点过多导致画布卡顿。

```text
readings：data/processed/public_ev_readings.csv
vehicles：data/processed/public_ev_vehicles.csv
```

原始公开数据只有车辆登记和续航字段，不包含电池运行遥测。因此 `temperature_c`、`voltage_v`、`remaining_capacity_kwh` 和 `estimated_range_km` 是为验证本项目接口而生成的派生测试值，不能用于真实电池安全结论。

生成命令：

```powershell
python scripts/prepare_public_ev_test_data.py
```
