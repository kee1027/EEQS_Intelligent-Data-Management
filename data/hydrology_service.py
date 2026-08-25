import importlib.util
import inspect
import time
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import HydrologyForecastDaily, HydrologyForecastRun, Station


def _generate_run_id():
    today = timezone.localdate()
    prefix = f"hydro-{today:%Y%m%d}"
    current_count = HydrologyForecastRun.objects.filter(run_id__startswith=prefix).count()
    return f"{prefix}-{current_count + 1:03d}"


def _load_model_callable():
    script_path = Path(settings.HYDROLOGY_MODEL_SCRIPT_PATH)
    if not script_path.exists():
        raise FileNotFoundError(f"模型脚本不存在: {script_path}")

    module_name = f"hydrology_model_{script_path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载模型脚本: {script_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    func_name = settings.HYDROLOGY_MODEL_ENTRYPOINT
    func = getattr(module, func_name, None)
    if not callable(func):
        raise AttributeError(f"模型脚本未找到可调用入口函数: {func_name}")
    return func


def _invoke_model(target_date):
    model_func = _load_model_callable()
    signature = inspect.signature(model_func)
    kwargs = {}
    if "target_date" in signature.parameters:
        kwargs["target_date"] = target_date
    elif "predict_date" in signature.parameters:
        kwargs["predict_date"] = target_date
    elif "date" in signature.parameters:
        kwargs["date"] = target_date
    return model_func(**kwargs)


def _normalize_result(raw_result, target_date):
    if isinstance(raw_result, dict):
        model_name = str(raw_result.get("model_name") or settings.HYDROLOGY_DEFAULT_MODEL_NAME)
        model_version = str(raw_result.get("model_version") or settings.HYDROLOGY_DEFAULT_MODEL_VERSION)
        forecasts = raw_result.get("forecasts", [])
    else:
        model_name = settings.HYDROLOGY_DEFAULT_MODEL_NAME
        model_version = settings.HYDROLOGY_DEFAULT_MODEL_VERSION
        forecasts = raw_result

    if not isinstance(forecasts, (list, tuple)):
        raise ValueError("模型返回结果无效：forecasts 必须是列表。")

    normalized = []
    for row in forecasts:
        if not isinstance(row, dict):
            raise ValueError("模型返回结果无效：每条预测结果必须为字典。")
        station_name = (row.get("station") or row.get("station_name") or "").strip()
        if not station_name:
            raise ValueError("模型返回结果无效：缺少 station 字段。")
        flow_value = row.get("flow_avg")
        if flow_value is None:
            raise ValueError("模型返回结果无效：缺少 flow_avg 字段。")

        row_target_date = row.get("target_date", target_date)
        if isinstance(row_target_date, str):
            row_target_date = date.fromisoformat(row_target_date)
        if not isinstance(row_target_date, date):
            raise ValueError("模型返回结果无效：target_date 必须是日期或 ISO 字符串。")

        normalized.append(
            {
                "station_name": station_name,
                "target_date": row_target_date,
                "flow_avg": Decimal(str(flow_value)),
            }
        )

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
            raw_result = _invoke_model(target_date)
            model_name, model_version, forecasts = _normalize_result(raw_result, target_date)
            _persist_forecasts(run, model_name, model_version, forecasts)

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
