"""重算气象日/小时聚合表。

用法：
    python manage.py aggregate_weather                  # 全量重算
    python manage.py aggregate_weather --days 7         # 最近 7 天
    python manage.py aggregate_weather --date 2026-09-15  # 指定日期（当天）
"""

from datetime import datetime, time as dt_time, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from data.aggregation import aggregate_all, aggregate_range

LOCAL_TZ = ZoneInfo(settings.TIME_ZONE)


class Command(BaseCommand):
    help = "从 WeatherData 原始数据重算 WeatherDailyAgg / WeatherHourlyAgg 聚合表。"

    def add_arguments(self, parser):
        parser.add_argument("--date", type=str, help="只重算指定日期（YYYY-MM-DD）")
        parser.add_argument("--days", type=int, help="重算最近 N 天（含今天）")

    def handle(self, *args, **options):
        if options["date"] and options["days"]:
            raise CommandError("--date 与 --days 只能二选一")

        if options["date"]:
            try:
                day = datetime.strptime(options["date"], "%Y-%m-%d").date()
            except ValueError as exc:
                raise CommandError("--date 格式必须为 YYYY-MM-DD") from exc
            start = datetime.combine(day, dt_time.min, tzinfo=LOCAL_TZ)
            end = datetime.combine(day, dt_time.max, tzinfo=LOCAL_TZ)
            stats = aggregate_range(start, end)
        elif options["days"]:
            end = timezone.now()
            start = datetime.combine(
                (end.astimezone(LOCAL_TZ) - timedelta(days=options["days"] - 1)).date(),
                dt_time.min,
                tzinfo=LOCAL_TZ,
            )
            stats = aggregate_range(start, end)
        else:
            self.stdout.write("[Aggregate] 全量重算...")
            stats = aggregate_all()

        self.stdout.write(
            self.style.SUCCESS(
                f"聚合完成: 日聚合 {stats['daily_rows']} 行, 小时聚合 {stats['hourly_rows']} 行"
            )
        )
