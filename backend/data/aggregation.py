"""
气象聚合管线：WeatherData（原始半小时数据）→ WeatherDailyAgg / WeatherHourlyAgg。

设计要点：
- 以数据库聚合（annotate）计算，不落 pandas，大数据量下也稳；
- 幂等：按 (station, day/hour) update_or_create，重复执行结果一致；
- 日累计降水 = 当日累计计数器的 max - min（tipping bucket 计数器语义）；
- 时区显式使用 settings.TIME_ZONE 分桶，day 为当日 00:00（本地时区）。

使用：
    from data.aggregation import aggregate_range
    aggregate_range(start, end)   # start/end 为 aware datetime
"""

from datetime import datetime, time as dt_time
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db.models import Avg, Count, Max, Min
from django.db.models.functions import TruncDay, TruncHour

from .models import Station, WeatherData, WeatherDailyAgg, WeatherHourlyAgg

LOCAL_TZ = ZoneInfo(settings.TIME_ZONE)

# 日聚合字段映射：(目标字段, 聚合函数, 源字段)
_DAILY_AGGS = {
    "avg_ta": Avg("ta"),
    "max_ta": Max("ta"),
    "min_ta": Min("ta"),
    "avg_rh": Avg("rh"),
    "max_rh": Max("rh"),
    "min_rh": Min("rh"),
    "avg_ws": Avg("ws"),
    "max_ws": Max("ws"),
    "avg_pressure": Avg("pressure"),
    "_max_rainsnow": Max("rainsnow"),
    "_min_rainsnow": Min("rainsnow"),
    "max_rainsnow_halfhour": Max("rainsnow_halfhour"),
    "max_snow_depth": Max("snow_depth"),
    "max_snow_depth_sr50a": Max("snow_depth_sr50a"),
    "max_snow_depth_ush": Max("snow_depth_ush"),
    "avg_sw_in": Avg("sw_in"),
    "max_sw_in": Max("sw_in"),
    "avg_vwc_10cm": Avg("vwc_soil_10cm"),
    "avg_vwc_20cm": Avg("vwc_soil_20cm"),
    "avg_vwc_40cm": Avg("vwc_soil_40cm"),
    "avg_vwc_60cm": Avg("vwc_soil_60cm"),
    "avg_vwc_100cm": Avg("vwc_soil_100cm"),
    "avg_tsoil_10cm": Avg("t_soil_10cm"),
    "avg_tsoil_20cm": Avg("t_soil_20cm"),
    "avg_tsoil_40cm": Avg("t_soil_40cm"),
    "avg_tsoil_60cm": Avg("t_soil_60cm"),
    "avg_tsoil_100cm": Avg("t_soil_100cm"),
    "max_swe": Max("swe"),
    "max_swe_ssg": Max("swe_ssg"),
    "record_count": Count("id"),
}

_HOURLY_AGGS = {
    "avg_ta": Avg("ta"),
    "max_ta": Max("ta"),
    "min_ta": Min("ta"),
    "avg_rh": Avg("rh"),
    "avg_ws": Avg("ws"),
    "max_ws": Max("ws"),
    "avg_pressure": Avg("pressure"),
    "max_snow_depth": Max("snow_depth"),
    "avg_sw_in": Avg("sw_in"),
    "record_count": Count("id"),
}


def aggregate_daily(start: datetime, end: datetime) -> int:
    """重算 [start, end] 范围内的日聚合，返回写入行数。"""
    rows = (
        WeatherData.objects.filter(timestamp__gte=start, timestamp__lte=end)
        .annotate(bucket=TruncDay("timestamp", tzinfo=LOCAL_TZ))
        .values("station_id", "bucket")
        .annotate(**_DAILY_AGGS)
    )
    written = 0
    for row in rows:
        defaults = {k: v for k, v in row.items() if k not in ("station_id", "bucket")}
        max_rain = defaults.pop("_max_rainsnow")
        min_rain = defaults.pop("_min_rainsnow")
        # 日累计降水 = 计数器当日增量；全天无有效降水数据则为 None
        defaults["total_rainsnow"] = (
            round(max_rain - min_rain, 3) if max_rain is not None and min_rain is not None else None
        )
        WeatherDailyAgg.objects.update_or_create(
            station_id=row["station_id"], day=row["bucket"], defaults=defaults
        )
        written += 1
    return written


def aggregate_hourly(start: datetime, end: datetime) -> int:
    """重算 [start, end] 范围内的小时聚合，返回写入行数。"""
    rows = (
        WeatherData.objects.filter(timestamp__gte=start, timestamp__lte=end)
        .annotate(bucket=TruncHour("timestamp", tzinfo=LOCAL_TZ))
        .values("station_id", "bucket")
        .annotate(**_HOURLY_AGGS)
    )
    written = 0
    for row in rows:
        defaults = {k: v for k, v in row.items() if k not in ("station_id", "bucket")}
        WeatherHourlyAgg.objects.update_or_create(
            station_id=row["station_id"], hour=row["bucket"], defaults=defaults
        )
        written += 1
    return written


def aggregate_range(start: datetime, end: datetime) -> dict:
    """同时重算日/小时聚合，返回统计。"""
    return {
        "daily_rows": aggregate_daily(start, end),
        "hourly_rows": aggregate_hourly(start, end),
    }


def aggregate_all() -> dict:
    """对 WeatherData 全量时间范围重算（首次建库/补数用）。"""
    extent = WeatherData.objects.aggregate(Min("timestamp"), Max("timestamp"))
    start, end = extent["timestamp__min"], extent["timestamp__max"]
    if start is None:
        return {"daily_rows": 0, "hourly_rows": 0}
    # 扩到整天边界，避免掐头去尾
    start = datetime.combine(start.astimezone(LOCAL_TZ).date(), dt_time.min, tzinfo=LOCAL_TZ)
    return aggregate_range(start, end)
