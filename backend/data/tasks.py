# 导入所需的库
from datetime import date, timedelta

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone

from .hydrology_service import run_hydrology_forecast
from .models import HydrologyForecastRun

User = get_user_model()

# =============================================================================
# APScheduler-compatible synchronous jobs (legacy, will be removed in Phase 4)
# =============================================================================


def import_data_job():
    """定时任务：自动扫描主文件+backup，只插入新记录。"""
    print("=" * 50)
    print("开始执行定时任务：导入气象数据")
    try:
        # 不带 --file 参数 → 自动扫描主文件 + backup
        call_command("import_data")
    except Exception as e:
        print(f"定时任务执行失败：{str(e)}")
    print("=" * 50)


def hydrology_forecast_job():
    target_date = timezone.localdate() + timedelta(days=1)
    print("=" * 50)
    print(f"开始执行定时任务：水文日均预测（目标日期 {target_date}）")
    try:
        call_command("run_hydrology_forecast", date=target_date.isoformat())
    except Exception as e:
        print(f"水文预测任务执行失败：{str(e)}")
    print("=" * 50)


# =============================================================================
# Celery shared tasks (new infrastructure)
# =============================================================================


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    autoretry_for=(Exception,),
)
def import_data_task(self):
    """
    Celery 异步任务：自动扫描主文件+backup，只插入新记录。

    失败时自动重试 3 次，每次间隔 5 分钟。
    此任务由 Celery Beat 调度（Phase 4 后）或手动触发。
    """
    print("[Celery] 开始执行异步任务：导入气象数据")
    try:
        call_command("import_data")
    except Exception as exc:
        print(f"[Celery] 导入任务失败，准备重试：{exc}")
        raise self.retry(exc=exc)
    print("[Celery] 导入任务完成")
    return {"status": "success", "imported_at": timezone.now().isoformat()}


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    time_limit=3600,          # 硬超时 1 小时
    soft_time_limit=3300,     # 软超时 55 分钟
    autoretry_for=(Exception,),
)
def hydrology_forecast_task(self, target_date=None, triggered_by_id=None, source="celery"):
    """
    Celery 异步任务：运行水文日均流量预测。

    Args:
        target_date: 目标日期字符串（YYYY-MM-DD），默认明天
        triggered_by_id: 触发用户 ID（手动触发时传入）
        source: 触发来源标识（如 'celery_beat', 'manual_api'）

    Returns:
        dict: {
            'run_id': str,
            'status': str,
            'record_count': int,
            'model_name': str,
            'model_version': str,
        }
    """
    # 解析 target_date
    if target_date is None:
        target_date = timezone.localdate() + timedelta(days=1)
    elif isinstance(target_date, str):
        target_date = date.fromisoformat(target_date)

    triggered_by = None
    if triggered_by_id is not None:
        triggered_by = User.objects.filter(id=triggered_by_id).first()

    print(f"[Celery] 开始执行水文预测：target_date={target_date}, source={source}")

    try:
        run = run_hydrology_forecast(
            target_date=target_date,
            triggered_by=triggered_by,
            source=source,
        )
    except SoftTimeLimitExceeded:
        # 软超时：尝试更新运行记录为失败状态
        print(f"[Celery] 水文预测软超时：target_date={target_date}")
        raise

    if run.status == HydrologyForecastRun.Status.SUCCESS:
        result = {
            "run_id": run.run_id,
            "status": "success",
            "record_count": run.record_count,
            "model_name": run.model_name,
            "model_version": run.model_version,
        }
        print(f"[Celery] 水文预测成功：{result}")
        return result
    else:
        # 模型执行失败，触发 Celery 重试
        exc = Exception(f"预测失败：{run.error_message}")
        print(f"[Celery] 水文预测失败，准备重试：{exc}")
        raise self.retry(exc=exc)
