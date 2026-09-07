# EV-Battery Insight

面向新能源汽车电池健康与充电风险的多源数据融合智能可视分析平台。

## 项目定位

本项目融合车辆、电池、充电、故障、车型和供应链等多源异构数据，完成数据质量治理、电池健康评分、车辆群体分析、异常识别、多视图联动和风险报告生成。

项目由两部分组成：

- `dataforge/`：EV DataForge 数据筛选、清洗、标准化和质量评估辅助工具。
- `frontend/` 与 `backend/`：在原综合可视化平台基础上改造的主分析平台。

## 当前开发顺序

1. 使用 `scripts/generate_ev_sample_data.py` 生成可控模拟数据。
2. 使用 EV DataForge 将原始 CSV 转换为标准数据并生成质量报告。
3. 接入主平台，完成电池健康评分和车辆聚类。
4. 实现风险车辆、车型、充电和故障的多视图联动。
5. 使用公开电池或充电数据进行第二轮验证。

## Python 环境

项目使用独立 Anaconda 环境 `evBatteryInsight`，Python 3.12。统一依赖清单位于 `requirements-ev-battery-insight.txt`。

```powershell
conda env create -f environment.yml
conda activate evBatteryInsight
python -m pip install -r requirements-ev-battery-insight.txt
```

## EV Insight 服务

健康评分 API 默认使用 5005 端口：

```powershell
python backend/ev-insight/app.py
```

接口：`POST /api/ev-insight/health-score`，字段为 `readings`（必填）和 `vehicles`（可选）两个 CSV 文件。

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

如果直接回车跳过密码，DataFlow 和 Region 会被跳过，EV Insight、Chain-Connect、Voronoi 和前端仍会启动。

## 数据声明

`data/simulated/` 中的数据为程序生成的模拟数据，不代表真实车辆或真实安全结论。公开数据必须在 `data/raw/README.md` 中记录来源、许可协议和处理方式。

## 原始平台

原有四个可视化模块保留在 `frontend/` 和 `backend/` 中，分别提供层次数据、Treemap、大屏、高维降维聚类、Voronoi 和关系图谱能力。后续将通过统一数据模型和新能源汽车业务服务进行整合。

## 风险边界

本项目是研究和辅助分析系统，不用于车辆控制、电池安全认证或替代专业维修诊断。
