"""Small HTTP adapter for the EV-Battery Insight health scoring core."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ev_insight import score_battery_health  # noqa: E402


app = Flask(__name__)
CORS(app)


@app.get("/api/ev-insight/health")
def health():
    return jsonify({"service": "ev-insight", "status": "ready"})


@app.post("/api/ev-insight/health-score")
def health_score():
    readings_file = request.files.get("readings")
    vehicles_file = request.files.get("vehicles")
    if readings_file is None:
        return jsonify({"message": "请上传 readings CSV 文件。"}), 400
    try:
        readings = pd.read_csv(readings_file)
        vehicles = pd.read_csv(vehicles_file) if vehicles_file else None
        result = score_battery_health(readings, vehicles)
    except (ValueError, pd.errors.ParserError) as error:
        return jsonify({"message": str(error)}), 400
    return jsonify({
        "summary": {
            "vehicleCount": len(result),
            "highRiskCount": int((result["risk_level"] == "高风险").sum()),
            "attentionCount": int((result["risk_level"] == "关注").sum()),
            "averageHealthScore": round(float(result["health_score"].mean()), 2) if len(result) else 0,
        },
        "items": result.where(result.notna(), None).to_dict(orient="records"),
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=False)
