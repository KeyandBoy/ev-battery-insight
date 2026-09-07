# 公开数据登记表

每引入一个公开数据集，请记录以下信息：

```text
数据集名称：
来源链接：
下载时间：
许可协议：
原始字段：
原始单位：
处理方式：
是否包含个人信息：
是否为模拟扩展：
```

## 当前测试源

数据集名称：Electric Vehicle Population Data
来源链接：https://github.com/nurdoolotov/Electric_Vehicle_Population_Data.csv-/blob/main/Electric_Vehicle_Population_Data.csv
直接下载：https://raw.githubusercontent.com/nurdoolotov/Electric_Vehicle_Population_Data.csv-/main/Electric_Vehicle_Population_Data.csv
下载时间：2026-09-08
许可协议：该公开镜像未随文件提供明确 LICENSE；仅用于本地测试，正式发布前需核实原始数据授权
原始字段：VIN、County、City、State、Model Year、Make、Model、Electric Vehicle Type、Electric Range 等
原始单位：Electric Range 为英里
处理方式：取前 200 条有有效车辆编号和续航数据的记录；转换为本项目车辆字段，并生成派生测试 readings
是否包含个人信息：未使用车主姓名、联系方式等个人字段；保留公开车辆登记汇总字段
是否为模拟扩展：是，temperature_c、voltage_v、remaining_capacity_kwh 和 estimated_range_km 为测试派生值，不是原始遥测
