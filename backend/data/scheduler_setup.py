# djangotutorial/data/scheduler_setup.py
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events
from apscheduler.jobstores.base import JobLookupError
from django.conf import settings
from .tasks import hydrology_forecast_job, import_data_job

def start():
    # 动态读取 settings 中的 Asia/Shanghai
    tz = pytz.timezone(settings.TIME_ZONE)
    
    # 确保调度器实例感知到新时区
    scheduler = BackgroundScheduler(timezone=tz)
    
    try:
        scheduler.add_jobstore(DjangoJobStore(), "default")
        
        weather_job_id = "weather_v4_stable"
        hydrology_job_id = "hydrology_daily_v1"

        # 先尝试删除（防止 ID 冲突）
        try:
            scheduler.remove_job(weather_job_id, jobstore='default')
        except JobLookupError:
            pass
        try:
            scheduler.remove_job(hydrology_job_id, jobstore='default')
        except JobLookupError:
            pass

        scheduler.add_job(
            import_data_job,
            trigger='interval',
            minutes=30,
            id=weather_job_id,
            name='气象数据自动导入',
            replace_existing=True,
            max_instances=1
        )
        scheduler.add_job(
            hydrology_forecast_job,
            trigger="cron",
            hour=settings.HYDROLOGY_DAILY_RUN_HOUR,
            minute=settings.HYDROLOGY_DAILY_RUN_MINUTE,
            id=hydrology_job_id,
            name="水文日均预测任务",
            replace_existing=True,
            max_instances=1,
        )

        register_events(scheduler)
        scheduler.start()
        print(f"[Scheduler] Started successfully. Jobs: {weather_job_id}, {hydrology_job_id}")
    except Exception as e:
        print(f"[Scheduler] Failed to start: {e}")
