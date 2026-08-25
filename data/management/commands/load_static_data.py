"""
将 scripts/export_static_data.py 导出的 JSON 静态数据加载到 Django 的 SQLite 数据库中。

用法:
    python manage.py load_static_data

前置条件:
    python manage.py migrate
"""

import json
from datetime import datetime
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from data.models import (
    HydrologyForecastDaily,
    HydrologyForecastRun,
    Station,
    WeatherDailyAgg,
    WeatherData,
    WeatherHourlyAgg,
)

STATIC_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "static_data"


def parse_dt(value):
    """解析多种日期时间格式"""
    if not value:
        return None
    if isinstance(value, str):
        value = value.replace(' ', 'T').replace('+00:00', '')
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return value


class Command(BaseCommand):
    help = "Load static JSON data into SQLite database"

    def handle(self, *args, **options):
        self.stdout.write("Loading static data from: %s" % STATIC_DATA_DIR)

        # 1. Load users
        self.load_users()

        # 2. Load stations
        self.load_stations()

        # 3. Load weather data
        self.load_weather_data()

        # 4. Load hydrology forecast runs
        self.load_hydrology_runs()

        # 5. Load hydrology forecast daily
        self.load_hydrology_daily()

        # 6. Load daily aggregates
        self.load_daily_agg()

        # 7. Load hourly aggregates
        self.load_hourly_agg()

        self.stdout.write(self.style.SUCCESS("Static data loaded successfully."))

    def load_json(self, name):
        path = STATIC_DATA_DIR / f"{name}.json"
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"  File not found: {path}"))
            return []
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_users(self):
        self.stdout.write("Loading users...")
        rows = self.load_json("auth_users")
        for row in rows:
            User.objects.get_or_create(
                id=row["id"],
                defaults={
                    "username": row["username"],
                    "first_name": row.get("first_name", ""),
                    "last_name": row.get("last_name", ""),
                    "email": row.get("email", ""),
                    "is_staff": row.get("is_staff", False),
                    "is_superuser": row.get("is_superuser", False),
                },
            )
        self.stdout.write(f"  Loaded {len(rows)} users")

    def load_stations(self):
        self.stdout.write("Loading stations...")
        rows = self.load_json("stations")
        for row in rows:
            Station.objects.get_or_create(
                id=row["id"],
                defaults={"name": row["name"]},
            )
        self.stdout.write(f"  Loaded {len(rows)} stations")

    def load_weather_data(self):
        self.stdout.write("Loading weather data...")
        rows = self.load_json("weather_data")
        batch = []
        for row in rows:
            batch.append(WeatherData(
                id=row["id"],
                station_id=row["station_id"],
                timestamp=parse_dt(row["timestamp"]),
                record=row.get("record"),
                batt_volt=row.get("batt_volt"),
                ptemp=row.get("ptemp"),
                ws=row.get("ws"),
                wd=row.get("wd"),
                wd_std=row.get("wd_std"),
                ta=row.get("ta"),
                rh=row.get("rh"),
                pvapor=row.get("pvapor"),
                pressure=row.get("pressure"),
                sw_in=row.get("sw_in"),
                vwc_soil_10cm=row.get("vwc_soil_10cm"),
                vwc_soil_20cm=row.get("vwc_soil_20cm"),
                vwc_soil_40cm=row.get("vwc_soil_40cm"),
                vwc_soil_60cm=row.get("vwc_soil_60cm"),
                vwc_soil_100cm=row.get("vwc_soil_100cm"),
                t_soil_10cm=row.get("t_soil_10cm"),
                t_soil_20cm=row.get("t_soil_20cm"),
                t_soil_40cm=row.get("t_soil_40cm"),
                t_soil_60cm=row.get("t_soil_60cm"),
                t_soil_100cm=row.get("t_soil_100cm"),
                rainsnow=row.get("rainsnow"),
                rainsnow_halfhour=row.get("rainsnow_halfhour"),
                snow_depth=row.get("snow_depth"),
                swe=row.get("swe"),
                snow_density=row.get("snow_density"),
                snow_depth_sr50a=row.get("snow_depth_sr50a"),
                snow_depth_ush=row.get("snow_depth_ush"),
                ice_content_slape=row.get("ice_content_slape"),
                water_content_slape=row.get("water_content_slape"),
                density_slape=row.get("density_slape"),
                swe_slape=row.get("swe_slape"),
                ice_content_horizontal=row.get("ice_content_horizontal"),
                water_content_horizontal=row.get("water_content_horizontal"),
                density_horizontal=row.get("density_horizontal"),
                swe_horizontal=row.get("swe_horizontal"),
                flux_min_100cm=row.get("flux_min_100cm"),
                flux_avg_100cm=row.get("flux_avg_100cm"),
                flux_max_100cm=row.get("flux_max_100cm"),
                flux_std_100cm=row.get("flux_std_100cm"),
                flux_cum_100cm=row.get("flux_cum_100cm"),
                wind_min_100cm=row.get("wind_min_100cm"),
                wind_avg_100cm=row.get("wind_avg_100cm"),
                wind_max_100cm=row.get("wind_max_100cm"),
                flux_min_200cm=row.get("flux_min_200cm"),
                flux_avg_200cm=row.get("flux_avg_200cm"),
                flux_max_200cm=row.get("flux_max_200cm"),
                flux_std_200cm=row.get("flux_std_200cm"),
                flux_cum_200cm=row.get("flux_cum_200cm"),
                wind_min_200cm=row.get("wind_min_200cm"),
                wind_avg_200cm=row.get("wind_avg_200cm"),
                wind_max_200cm=row.get("wind_max_200cm"),
                swe_ssg=row.get("swe_ssg"),
                snow_density_ssg=row.get("snow_density_ssg"),
            ))
        WeatherData.objects.bulk_create(batch, batch_size=500, ignore_conflicts=True)
        self.stdout.write(f"  Loaded {len(batch)} weather records")

    def load_hydrology_runs(self):
        self.stdout.write("Loading hydrology forecast runs...")
        rows = self.load_json("hydrology_forecast_runs")
        for row in rows:
            HydrologyForecastRun.objects.get_or_create(
                id=row["id"],
                defaults={
                    "run_id": row["run_id"],
                    "target_date": row.get("target_date"),
                    "model_name": row.get("model_name", ""),
                    "model_version": row.get("model_version", ""),
                    "source": row.get("source", "scheduler"),
                    "status": row.get("status", "success"),
                    "retry_count": row.get("retry_count", 0),
                    "record_count": row.get("record_count", 0),
                    "error_message": row.get("error_message", ""),
                    "started_at": parse_dt(row.get("started_at")),
                    "finished_at": parse_dt(row.get("finished_at")),
                    "created_at": parse_dt(row.get("created_at")),
                    "updated_at": parse_dt(row.get("updated_at")),
                },
            )
        self.stdout.write(f"  Loaded {len(rows)} forecast runs")

    def load_hydrology_daily(self):
        self.stdout.write("Loading hydrology forecast daily...")
        rows = self.load_json("hydrology_forecast_daily")
        batch = []
        for row in rows:
            batch.append(HydrologyForecastDaily(
                id=row["id"],
                run_id=row.get("run_id"),
                station_id=row.get("station_id"),
                target_date=row.get("target_date"),
                flow_avg=row.get("flow_avg"),
                model_name=row.get("model_name", ""),
                model_version=row.get("model_version", ""),
                created_at=parse_dt(row.get("created_at")),
            ))
        if batch:
            HydrologyForecastDaily.objects.bulk_create(batch, batch_size=500, ignore_conflicts=True)
        self.stdout.write(f"  Loaded {len(batch)} forecast daily records")

    def load_daily_agg(self):
        self.stdout.write("Loading daily aggregates...")
        rows = self.load_json("weather_daily_agg")
        batch = []
        for row in rows:
            batch.append(WeatherDailyAgg(
                day=parse_dt(row["day"]),
                station_id=row.get("station_id"),
                avg_ta=row.get("avg_ta"),
                max_ta=row.get("max_ta"),
                min_ta=row.get("min_ta"),
                avg_rh=row.get("avg_rh"),
                max_rh=row.get("max_rh"),
                min_rh=row.get("min_rh"),
                avg_ws=row.get("avg_ws"),
                max_ws=row.get("max_ws"),
                avg_pressure=row.get("avg_pressure"),
                total_rainsnow=row.get("total_rainsnow"),
                max_rainsnow_halfhour=row.get("max_rainsnow_halfhour"),
                max_snow_depth=row.get("max_snow_depth"),
                max_snow_depth_sr50a=row.get("max_snow_depth_sr50a"),
                max_snow_depth_ush=row.get("max_snow_depth_ush"),
                avg_sw_in=row.get("avg_sw_in"),
                max_sw_in=row.get("max_sw_in"),
                avg_vwc_10cm=row.get("avg_vwc_10cm"),
                avg_vwc_20cm=row.get("avg_vwc_20cm"),
                avg_vwc_40cm=row.get("avg_vwc_40cm"),
                avg_vwc_60cm=row.get("avg_vwc_60cm"),
                avg_vwc_100cm=row.get("avg_vwc_100cm"),
                avg_tsoil_10cm=row.get("avg_tsoil_10cm"),
                avg_tsoil_20cm=row.get("avg_tsoil_20cm"),
                avg_tsoil_40cm=row.get("avg_tsoil_40cm"),
                avg_tsoil_60cm=row.get("avg_tsoil_60cm"),
                avg_tsoil_100cm=row.get("avg_tsoil_100cm"),
                max_swe=row.get("max_swe"),
                max_swe_ssg=row.get("max_swe_ssg"),
                record_count=row.get("record_count", 0),
            ))
        WeatherDailyAgg.objects.bulk_create(batch, batch_size=200, ignore_conflicts=True)
        self.stdout.write(f"  Loaded {len(batch)} daily aggregates")

    def load_hourly_agg(self):
        self.stdout.write("Loading hourly aggregates...")
        rows = self.load_json("weather_hourly_agg")
        batch = []
        for row in rows:
            batch.append(WeatherHourlyAgg(
                hour=parse_dt(row["hour"]),
                station_id=row.get("station_id"),
                avg_ta=row.get("avg_ta"),
                max_ta=row.get("max_ta"),
                min_ta=row.get("min_ta"),
                avg_rh=row.get("avg_rh"),
                avg_ws=row.get("avg_ws"),
                max_ws=row.get("max_ws"),
                avg_pressure=row.get("avg_pressure"),
                max_snow_depth=row.get("max_snow_depth"),
                avg_sw_in=row.get("avg_sw_in"),
                record_count=row.get("record_count", 0),
            ))
        WeatherHourlyAgg.objects.bulk_create(batch, batch_size=500, ignore_conflicts=True)
        self.stdout.write(f"  Loaded {len(batch)} hourly aggregates")
