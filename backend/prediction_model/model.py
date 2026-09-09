"""
EEQS-RAG 模拟水文预测模型（文件交换式）。

约定：
- 从容器内 /io/input/ 读取输入文件：
    - _meta.json          运行元信息（run_id / target_date=基准日D / input_days）
    - station_<id>.json   每个站点一个文件，含近 N 天日观测序列
- 把结果写到 /io/output/：
    - station_<id>.json   每个站点一个预测结果文件
    - 出错时写 _error.json 并以非零码退出

模拟逻辑：以输入序列最后 7 天 total_rainsnow（日累计降水）的均值作为基准流量
（全缺失时退化为全部可用天数均值，再退化为 0），未来 D+1..D+7 七个预测日
分别乘以 0.7 / 0.8 / 0.9 / 1.0 / 1.1 / 1.2 / 1.3 得到 flow_avg。
"""

import json
import os
import sys
import traceback
from datetime import date, timedelta
from pathlib import Path

INPUT_DIR = Path("/io/input")
OUTPUT_DIR = Path("/io/output")

MODEL_NAME = os.environ.get("MODEL_NAME", "mock-scale-7day")
MODEL_VERSION = os.environ.get("MODEL_VERSION", "v1")

SCALE_FACTORS = [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]  # 对应 D+1 .. D+7
BASELINE_FIELD = "total_rainsnow"
BASELINE_WINDOW = 7


def compute_baseline(series):
    values = [row.get(BASELINE_FIELD) for row in series]
    values = [float(v) for v in values if v is not None]
    if not values:
        return 0.0
    window = values[-BASELINE_WINDOW:] or values
    return sum(window) / len(window)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    meta_path = INPUT_DIR / "_meta.json"
    if not meta_path.exists():
        raise FileNotFoundError("缺少输入元信息文件: /io/input/_meta.json")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    base_date = date.fromisoformat(meta["target_date"])

    station_files = sorted(p for p in INPUT_DIR.glob("station_*.json"))
    if not station_files:
        raise FileNotFoundError("输入目录中没有任何 station_*.json 文件")

    written = 0
    for path in station_files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        series = payload.get("series") or []
        baseline = compute_baseline(series)

        forecasts = []
        for i, factor in enumerate(SCALE_FACTORS, start=1):
            forecasts.append(
                {
                    "target_date": (base_date + timedelta(days=i)).isoformat(),
                    "flow_avg": round(baseline * factor, 3),
                    "scale_factor": factor,
                }
            )

        result = {
            "station": payload.get("station_name"),
            "station_id": payload.get("station_id"),
            "model_name": MODEL_NAME,
            "model_version": MODEL_VERSION,
            "base_date": base_date.isoformat(),
            "baseline": round(baseline, 3),
            "forecasts": forecasts,
        }
        (OUTPUT_DIR / path.name).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        written += 1

    print(f"[model] done: {written} station forecast file(s) written to /io/output")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # 写错误文件并非零退出，便于后端诊断
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "_error.json").write_text(
            json.dumps(
                {"error": str(exc), "traceback": traceback.format_exc()},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"[model] ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
