"""
文件交换式水文预测流水线。

流程：
1. 从 WeatherDailyAgg 导出每个站点最近 N 天的日观测序列到
   <HYDROLOGY_IO_DIR>/<run_id>/input/（每站一个 station_<id>.json，外加 _meta.json）
2. 通过 `docker run --rm -v <run_io_dir>:/io <HYDROLOGY_MODEL_IMAGE>` 运行模型容器，
   模型从容器内 /io/input/ 读取、向 /io/output/ 写回预测结果
3. 解析 <run_io_dir>/output/station_*.json，写入 HydrologyForecastDaily

任何一步失败都会抛出带可读信息的异常，由 run_hydrology_forecast 的重试/失败
记录机制接管（Run 标记 failed 并保存 error_message）。
"""

import json
import shutil
import subprocess
import time
from datetime import date, datetime, time as dt_time, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import HydrologyForecastDaily, HydrologyForecastRun, Station, WeatherDailyAgg

_DOCKER_DESKTOP_FALLBACK = r"C:\Program Files\Docker\Docker\resources\bin\docker.exe"

# 输入序列中导出给模型的字段
INPUT_SERIES_FIELDS = [
    "avg_ta",
    "total_rainsnow",
    "max_snow_depth",
    "max_swe",
    "avg_sw_in",
    "avg_vwc_10cm",
]


def _generate_run_id():
    today = timezone.localdate()
    prefix = f"hydro-{today:%Y%m%d}"
    current_count = HydrologyForecastRun.objects.filter(run_id__startswith=prefix).count()
    return f"{prefix}-{current_count + 1:03d}"


# -----------------------------------------------------------------------------
# Docker 调用
# -----------------------------------------------------------------------------

def _resolve_docker_bin():
    """按 配置 -> PATH -> Docker Desktop 默认路径 的顺序定位 docker 可执行文件。"""
    configured = (settings.HYDROLOGY_DOCKER_BIN or "").strip()
    if configured:
        if Path(configured).exists() or shutil.which(configured):
            return configured
        raise RuntimeError(f"HYDROLOGY_DOCKER_BIN 指向的文件不存在: {configured}")

    found = shutil.which("docker")
    if found:
        return found
    if Path(_DOCKER_DESKTOP_FALLBACK).exists():
        return _DOCKER_DESKTOP_FALLBACK
    raise RuntimeError(
        "找不到 docker 可执行文件：请安装/启动 Docker Desktop，"
        "或设置 HYDROLOGY_DOCKER_BIN 指向 docker.exe 的绝对路径。"
    )


def _ensure_model_image(docker_bin):
    image = settings.HYDROLOGY_MODEL_IMAGE
    proc = subprocess.run(
        [docker_bin, "image", "inspect", image],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"模型镜像不存在: {image}。请先在 backend/prediction_model/ 下执行 "
            f"docker build -t {image} . 后再触发预测。"
        )


def _run_model_container(docker_bin, run_io_dir):
    """运行模型容器；返回进程stderr。失败时抛出带诊断信息的异常。"""
    image = settings.HYDROLOGY_MODEL_IMAGE
    timeout = settings.HYDROLOGY_DOCKER_TIMEOUT_SECONDS
    host_path = str(Path(run_io_dir).resolve())  # Windows 绝对路径，Docker Desktop 可直接挂载

    cmd = [docker_bin, "run", "--rm", "-v", f"{host_path}:/io", image]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"模型容器运行超时（>{timeout}s）: {' '.join(cmd)}") from exc
    except FileNotFoundError as exc:
        raise RuntimeError(f"docker 可执行文件无法启动: {docker_bin} ({exc})") from exc

    error_file = Path(run_io_dir) / "output" / "_error.json"
    if proc.returncode != 0:
        detail = ""
        if error_file.exists():
            try:
                detail = json.loads(error_file.read_text(encoding="utf-8")).get("error", "")
            except Exception:
                detail = ""
        raise RuntimeError(
            f"模型容器退出码 {proc.returncode}。"
            f"{('模型报告: ' + detail) if detail else ''}"
            f"stderr: {(proc.stderr or '').strip()[:500]}"
        )
    return proc


# -----------------------------------------------------------------------------
# 输入导出 / 输出解析
# -----------------------------------------------------------------------------

def _export_inputs(run, target_date, run_io_dir):
    """导出输入文件，返回参与预测的站点名列表。"""
    input_days = settings.HYDROLOGY_INPUT_DAYS
    input_dir = Path(run_io_dir) / "input"
    output_dir = Path(run_io_dir) / "output"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    (input_dir / "_meta.json").write_text(
        json.dumps(
            {
                "run_id": run.run_id,
                "target_date": target_date.isoformat(),
                "input_days": input_days,
                "generated_at": timezone.now().isoformat(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # target_date 之前的最近 input_days 天（day 为当日 00:00 的 DateTimeField）
    window_end = timezone.make_aware(datetime.combine(target_date, dt_time.min))
    station_names = []
    for station in Station.objects.order_by("id"):
        qs = (
            WeatherDailyAgg.objects.filter(station=station, day__lt=window_end)
            .order_by("-day")[:input_days]
        )
        rows = list(qs)
        if not rows:
            continue  # 窗口内无观测数据的站点不参与本次预测
        rows.reverse()  # 转为时间正序

        series = []
        for agg in rows:
            row = {"day": timezone.localdate(agg.day).isoformat() if timezone.is_aware(agg.day) else agg.day.date().isoformat()}
            for field in INPUT_SERIES_FIELDS:
                row[field] = getattr(agg, field)
            series.append(row)

        payload = {
            "station_id": station.id,
            "station_name": station.name,
            "series": series,
        }
        (input_dir / f"station_{station.id}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        station_names.append(station.name)

    if not station_names:
        raise ValueError(
            f"没有站点在 {target_date} 之前 {input_days} 天窗口内存在 WeatherDailyAgg 观测数据，"
            "无法生成模型输入。"
        )
    return station_names


def _collect_outputs(run_io_dir, expected_station_names):
    """解析输出文件，返回 (model_name, model_version, normalized_rows)。"""
    output_dir = Path(run_io_dir) / "output"
    output_files = sorted(output_dir.glob("station_*.json"))
    if not output_files:
        raise ValueError(f"模型未写出任何输出文件: {output_dir}/station_*.json 缺失")

    model_name = None
    model_version = None
    normalized = []
    seen_stations = set()

    for path in output_files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError(f"输出文件格式错误（不是合法 JSON）: {path.name}: {exc}") from exc

        station_name = (payload.get("station") or "").strip()
        if not station_name:
            raise ValueError(f"输出文件缺少 station 字段: {path.name}")
        forecasts = payload.get("forecasts")
        if not isinstance(forecasts, list) or not forecasts:
            raise ValueError(f"输出文件 forecasts 为空或不是列表: {path.name}")

        file_model_name = str(payload.get("model_name") or settings.HYDROLOGY_DEFAULT_MODEL_NAME)
        file_model_version = str(payload.get("model_version") or settings.HYDROLOGY_DEFAULT_MODEL_VERSION)
        if model_name is None:
            model_name, model_version = file_model_name, file_model_version

        for row in forecasts:
            try:
                row_target_date = date.fromisoformat(str(row["target_date"]))
                flow_avg = Decimal(str(row["flow_avg"]))
            except (KeyError, ValueError, TypeError) as exc:
                raise ValueError(
                    f"输出文件 {path.name} 中预测记录格式错误（需要 target_date/flow_avg）: {row!r}"
                ) from exc
            normalized.append(
                {"station_name": station_name, "target_date": row_target_date, "flow_avg": flow_avg}
            )
        seen_stations.add(station_name)

    missing = [name for name in expected_station_names if name not in seen_stations]
    if missing:
        raise ValueError(f"模型输出缺少以下站点的结果文件: {', '.join(missing)}")

    return model_name, model_version, normalized


def _persist_forecasts(run, model_name, model_version, forecasts):
    with transaction.atomic():
        for row in forecasts:
            station, _ = Station.objects.get_or_create(name=row["station_name"])
            HydrologyForecastDaily.objects.update_or_create(
                station=station,
                target_date=row["target_date"],
                model_name=model_name,
                model_version=model_version,
                defaults={
                    "run": run,
                    "flow_avg": row["flow_avg"],
                },
            )


# -----------------------------------------------------------------------------
# 主入口
# -----------------------------------------------------------------------------

def _execute_pipeline(run, target_date):
    """单次尝试：导出输入 -> 运行容器 -> 解析输出 -> 入库。"""
    docker_bin = _resolve_docker_bin()
    _ensure_model_image(docker_bin)

    run_io_dir = Path(settings.HYDROLOGY_IO_DIR) / run.run_id
    if run_io_dir.exists():
        shutil.rmtree(run_io_dir, ignore_errors=True)  # 重试前清理旧产物

    station_names = _export_inputs(run, target_date, run_io_dir)
    _run_model_container(docker_bin, run_io_dir)
    model_name, model_version, forecasts = _collect_outputs(run_io_dir, station_names)
    _persist_forecasts(run, model_name, model_version, forecasts)
    return model_name, model_version, forecasts


def run_hydrology_forecast(*, target_date, triggered_by=None, source="scheduler", run_id=None):
    retry_limit = settings.HYDROLOGY_RETRY_ATTEMPTS
    retry_delay = settings.HYDROLOGY_RETRY_DELAY_SECONDS

    run = HydrologyForecastRun.objects.create(
        run_id=run_id or _generate_run_id(),
        target_date=target_date,
        source=source,
        status=HydrologyForecastRun.Status.RUNNING,
        triggered_by=triggered_by,
    )

    last_exception = None
    for attempt in range(1, retry_limit + 1):
        try:
            model_name, model_version, forecasts = _execute_pipeline(run, target_date)

            run.model_name = model_name
            run.model_version = model_version
            run.record_count = len(forecasts)
            run.status = HydrologyForecastRun.Status.SUCCESS
            run.retry_count = attempt - 1
            run.error_message = ""
            run.finished_at = timezone.now()
            run.save(
                update_fields=[
                    "model_name",
                    "model_version",
                    "record_count",
                    "status",
                    "retry_count",
                    "error_message",
                    "finished_at",
                    "updated_at",
                ]
            )
            return run
        except Exception as exc:
            last_exception = exc
            if attempt < retry_limit:
                time.sleep(retry_delay)

    run.status = HydrologyForecastRun.Status.FAILED
    run.retry_count = retry_limit - 1
    run.error_message = str(last_exception)[:2000]
    run.finished_at = timezone.now()
    run.save(update_fields=["status", "retry_count", "error_message", "finished_at", "updated_at"])
    return run
