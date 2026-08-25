from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from data.hydrology_service import run_hydrology_forecast
from data.models import HydrologyForecastRun


class Command(BaseCommand):
    help = "运行水文日均流量预测并写入数据库。"

    def add_arguments(self, parser):
        parser.add_argument("--date", type=str, help="目标预测日期，格式 YYYY-MM-DD。默认明天。")
        parser.add_argument("--manual", action="store_true", help="标记为手动触发。")
        parser.add_argument("--run-id", type=str, help="可选：指定运行编号。")

    def handle(self, *args, **options):
        date_str = options["date"]
        if date_str:
            try:
                target_date = timezone.datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError as exc:
                raise CommandError("参数 --date 格式必须为 YYYY-MM-DD。") from exc
        else:
            target_date = timezone.localdate() + timedelta(days=1)

        source = "manual_command" if options["manual"] else "scheduler"
        run = run_hydrology_forecast(
            target_date=target_date,
            source=source,
            run_id=options.get("run_id"),
        )

        if run.status != HydrologyForecastRun.Status.SUCCESS:
            raise CommandError(
                f"预测失败: run_id={run.run_id}, retry_count={run.retry_count}, error={run.error_message}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"预测完成: run_id={run.run_id}, target_date={run.target_date}, records={run.record_count}"
            )
        )
