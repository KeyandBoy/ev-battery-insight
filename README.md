# Unified Visualization Platform

通用多源数据可视化与分析工具，支持关系网络、层次数据、高维数据和空间分布等多种分析场景。

## 项目定位

本项目提供数据源管理、数据处理、交互式可视化、统计分析、多视图联动和结果导出能力，适用于社交关系、人物关系、组织架构、学术引用、供应链等多种数据。

新能源汽车电池健康与充电风险分析是当前重点应用案例。该案例将车辆、电池、充电、故障、车型和供应链数据作为数据源，完成健康评分、异常识别、车辆群体分析和风险可视化。

项目由两部分组成：

- `dataforge/`：数据筛选、清洗、标准化和质量评估辅助工具，可用于新能源汽车等数据源。
- `frontend/` 与 `backend/`：通用多源数据可视化分析平台及应用案例服务。

## 当前开发顺序

1. 使用示例数据源验证关系网络、层次数据和高维分析流程。
2. 使用 DataForge 将原始数据转换为标准数据并生成质量报告。
3. 接入新能源汽车电池数据，完成健康评分和充电风险分析。
4. 实现不同数据源的多视图联动、统计分析和结果导出。
5. 使用公开数据验证工具对其他行业和数据类型的适用性。

## Python 环境

项目使用独立 Anaconda 环境 `evBatteryInsight`，Python 3.12。统一依赖清单位于 `requirements-ev-battery-insight.txt`。

```powershell
conda env create -f environment.yml
conda activate evBatteryInsight
python -m pip install -r requirements-ev-battery-insight.txt
```

## 应用案例服务

新能源汽车电池健康评分 API 默认使用 5005 端口：

```powershell
python backend/ev-insight/app.py
```

接口：`POST /api/ev-insight/health-score`，字段为 `readings`（必填）和 `vehicles`（可选）两个 CSV 文件。

## 测试数据

可直接上传以下整理好的公开数据测试文件：

- `data/processed/public_ev_readings.csv`
- `data/processed/public_ev_vehicles.csv`

数据来源和处理说明见 `data/raw/README.md` 与 `data/processed/README.md`。其中 readings 中的运行指标是派生测试值，不代表真实电池遥测。

## 一键启动

双击项目根目录的 `start.bat`，或在 PowerShell 中执行：

```powershell
.\start.bat
```

脚本只保留一个启动控制终端，其他服务在后台运行；它会检查 5001 至 5005、5175 端口，并自动打开浏览器。运行日志位于 `logs/`。停止服务请运行 `stop.bat`。

MySQL 配置有两种方式：

```text
方式一：在项目根目录创建 .env，填写 MYSQL_USER 和 MYSQL_PASSWORD。
方式二：直接运行 start.bat，在终端输入 MySQL 密码。
```

启动时会自动创建 `dataflow_canvas` 和 `highdim_region_vis` 数据库。如果直接回车跳过密码，DataFlow 和 Region 会被跳过，EV Insight、Chain-Connect、Voronoi 和前端仍会启动。

## 数据声明

`data/simulated/` 中的数据为程序生成的模拟数据，不代表真实车辆或真实安全结论。公开数据必须在 `data/raw/README.md` 中记录来源、许可协议和处理方式。

## 分析能力

平台将数据质量治理、关系网络、层次数据、高维聚类、空间分布和应用案例服务整合到统一的分析流程中。DataFlow、Region、Voronoi 和 Chain-Connect 是通用分析组件；新能源汽车电池分析则是当前重点应用案例。

## 风险边界

本项目是研究和辅助分析系统，不用于车辆控制、电池安全认证或替代专业维修诊断。
