from django.conf import settings
from django.db import models
from django.utils import timezone
from django.db.models import Q

class Station(models.Model):
    """站点模型"""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class WeatherData(models.Model):
    """气象数据模型"""
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='weather_data')
    timestamp = models.DateTimeField(verbose_name="数据存储时间")
    record = models.IntegerField(verbose_name="记录号", null=True, blank=True)
    
    # 气象数据
    batt_volt = models.FloatField(verbose_name="数采电池电压", null=True, blank=True)
    ptemp = models.FloatField(verbose_name="数采面板温度", null=True, blank=True)
    ws = models.FloatField(verbose_name="风速", null=True, blank=True)
    wd = models.FloatField(verbose_name="风向", null=True, blank=True)
    wd_std = models.FloatField(verbose_name="风向标准差", null=True, blank=True)
    ta = models.FloatField(verbose_name="空气温度", null=True, blank=True)
    rh = models.FloatField(verbose_name="空气相对湿度", null=True, blank=True)
    pvapor = models.FloatField(verbose_name="水汽压", null=True, blank=True)
    pressure = models.FloatField(verbose_name="大气压", null=True, blank=True)
    sw_in = models.FloatField(verbose_name="总辐射", null=True, blank=True)
    
    # 土壤数据
    vwc_soil_10cm = models.FloatField(verbose_name="土壤含水量1(10cm)", null=True, blank=True)
    vwc_soil_20cm = models.FloatField(verbose_name="土壤含水量2(20cm)", null=True, blank=True)
    vwc_soil_40cm = models.FloatField(verbose_name="土壤含水量3(40cm)", null=True, blank=True)
    vwc_soil_60cm = models.FloatField(verbose_name="土壤含水量4(60cm)", null=True, blank=True)
    vwc_soil_100cm = models.FloatField(verbose_name="土壤含水量5(100cm)", null=True, blank=True)
    t_soil_10cm = models.FloatField(verbose_name="土壤温度1(10cm)", null=True, blank=True)
    t_soil_20cm = models.FloatField(verbose_name="土壤温度2(20cm)", null=True, blank=True)
    t_soil_40cm = models.FloatField(verbose_name="土壤温度3(40cm)", null=True, blank=True)
    t_soil_60cm = models.FloatField(verbose_name="土壤温度4(60cm)", null=True, blank=True)
    t_soil_100cm = models.FloatField(verbose_name="土壤温度5(100cm)", null=True, blank=True)
    
    # 降水和雪深
    rainsnow = models.FloatField(verbose_name="降水累计值", null=True, blank=True)
    rainsnow_halfhour = models.FloatField(verbose_name="半小时降水", null=True, blank=True)
    snow_depth = models.FloatField(verbose_name="雪深", null=True, blank=True)
    swe = models.FloatField(verbose_name="雪水当量", null=True, blank=True, help_text="单位：mm")
    snow_density = models.FloatField(verbose_name="雪密度", null=True, blank=True, help_text="单位：kg/m³")
    
    # ==================== KKSLS站点特有字段 ====================
    # 雪深传感器扩展（KKSLS站点有两个雪深传感器）
    snow_depth_sr50a = models.FloatField(verbose_name="SR50A雪深", null=True, blank=True)
    snow_depth_ush = models.FloatField(verbose_name="USH-9雪深", null=True, blank=True)
    
    # 斜向观测带数据
    ice_content_slape = models.FloatField(verbose_name="斜向观测带冰含量", null=True, blank=True)
    water_content_slape = models.FloatField(verbose_name="斜向观测带水含量", null=True, blank=True)
    density_slape = models.FloatField(verbose_name="斜向观测带雪密度", null=True, blank=True)
    swe_slape = models.FloatField(verbose_name="斜向观测带雪水当量", null=True, blank=True)
    
    # 水平观测带数据
    ice_content_horizontal = models.FloatField(verbose_name="水平观测带冰含量", null=True, blank=True)
    water_content_horizontal = models.FloatField(verbose_name="水平观测带水含量", null=True, blank=True)
    density_horizontal = models.FloatField(verbose_name="水平观测带雪密度", null=True, blank=True)
    swe_horizontal = models.FloatField(verbose_name="水平观测带雪水当量", null=True, blank=True)
    
    # 100cm风吹雪通量数据
    flux_min_100cm = models.FloatField(verbose_name="100cm风吹雪最小通量", null=True, blank=True)
    flux_avg_100cm = models.FloatField(verbose_name="100cm风吹雪平均通量", null=True, blank=True)
    flux_max_100cm = models.FloatField(verbose_name="100cm风吹雪最大通量", null=True, blank=True)
    flux_std_100cm = models.FloatField(verbose_name="100cm风吹雪通量标准差", null=True, blank=True)
    flux_cum_100cm = models.FloatField(verbose_name="100cm风吹雪通量总量", null=True, blank=True)
    
    # 100cm风速数据
    wind_min_100cm = models.FloatField(verbose_name="100cm最小风速", null=True, blank=True)
    wind_avg_100cm = models.FloatField(verbose_name="100cm平均风速", null=True, blank=True)
    wind_max_100cm = models.FloatField(verbose_name="100cm最大风速", null=True, blank=True)
    
    # 200cm风吹雪通量数据
    flux_min_200cm = models.FloatField(verbose_name="200cm风吹雪最小通量", null=True, blank=True)
    flux_avg_200cm = models.FloatField(verbose_name="200cm风吹雪平均通量", null=True, blank=True)
    flux_max_200cm = models.FloatField(verbose_name="200cm风吹雪最大通量", null=True, blank=True)
    flux_std_200cm = models.FloatField(verbose_name="200cm风吹雪通量标准差", null=True, blank=True)
    flux_cum_200cm = models.FloatField(verbose_name="200cm风吹雪通量总量", null=True, blank=True)
    
    # 200cm风速数据
    wind_min_200cm = models.FloatField(verbose_name="200cm最小风速", null=True, blank=True)
    wind_avg_200cm = models.FloatField(verbose_name="200cm平均风速", null=True, blank=True)
    wind_max_200cm = models.FloatField(verbose_name="200cm最大风速", null=True, blank=True)
    
    # SSG雪水当量和密度
    swe_ssg = models.FloatField(verbose_name="SSG雪水当量", null=True, blank=True)
    snow_density_ssg = models.FloatField(verbose_name="SSG雪密度", null=True, blank=True)
    # ==================== 水文站点特有字段 ====================

    class Meta:
        # 确保每个站点在同一时间戳只有一条记录
        unique_together = ('station', 'timestamp')
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.station.name} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class ManualDataRecord(models.Model):
    """人工录入数据模型"""

    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="manual_data_records",
        verbose_name="操作人员",
    )
    operated_at = models.DateTimeField(default=timezone.now, editable=False, verbose_name="操作时间")
    data_at = models.DateTimeField(verbose_name="数据时间")
    value = models.DecimalField(max_digits=20, decimal_places=6, verbose_name="数据值")
    is_void = models.BooleanField(default=False, verbose_name="是否作废")
    voided_at = models.DateTimeField(null=True, blank=True, verbose_name="作废时间")
    voided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="voided_manual_data_records",
        null=True,
        blank=True,
        verbose_name="作废操作人",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["operator", "data_at"],
                name="uniq_manual_data_operator_data_at",
                condition=Q(is_void=False),
            )
        ]
        ordering = ["-data_at"]

    def __str__(self):
        return f"{self.operator} at {self.data_at:%Y-%m-%d %H:%M:%S}"


class HydrologyForecastRun(models.Model):
    class Status(models.TextChoices):
        RUNNING = "running", "运行中"
        SUCCESS = "success", "成功"
        FAILED = "failed", "失败"

    run_id = models.CharField(max_length=64, unique=True, verbose_name="运行编号")
    target_date = models.DateField(verbose_name="预测日期")
    model_name = models.CharField(max_length=100, blank=True, verbose_name="模型名称")
    model_version = models.CharField(max_length=100, blank=True, verbose_name="模型版本")
    source = models.CharField(max_length=30, default="scheduler", verbose_name="触发来源")
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.RUNNING,
        verbose_name="运行状态",
    )
    retry_count = models.PositiveSmallIntegerField(default=0, verbose_name="重试次数")
    record_count = models.PositiveIntegerField(default=0, verbose_name="结果条数")
    error_message = models.TextField(blank=True, verbose_name="错误信息")
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="hydrology_forecast_runs",
        null=True,
        blank=True,
        verbose_name="触发人",
    )
    started_at = models.DateTimeField(default=timezone.now, verbose_name="开始时间")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="结束时间")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["target_date", "status"])]

    def __str__(self):
        return self.run_id


class HydrologyForecastDaily(models.Model):
    run = models.ForeignKey(
        HydrologyForecastRun,
        on_delete=models.CASCADE,
        related_name="forecasts",
        verbose_name="所属运行",
    )
    station = models.ForeignKey(
        Station,
        on_delete=models.PROTECT,
        related_name="hydrology_daily_forecasts",
        verbose_name="站点",
    )
    target_date = models.DateField(verbose_name="预测日期")
    flow_avg = models.DecimalField(max_digits=12, decimal_places=3, verbose_name="日均流量")
    model_name = models.CharField(max_length=100, verbose_name="模型名称")
    model_version = models.CharField(max_length=100, verbose_name="模型版本")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        ordering = ["-target_date", "station__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["station", "target_date", "model_name", "model_version"],
                name="uniq_hydro_daily_station_date_model_version",
            )
        ]
        indexes = [models.Index(fields=["target_date", "model_name", "model_version"])]

    def __str__(self):
        return f"{self.station.name} {self.target_date} {self.model_name}:{self.model_version}"


# =============================================================================
# Static aggregate data models (computed from raw weather data, read-only)
# =============================================================================

class WeatherDailyAgg(models.Model):
    """
    日级连续聚合数据（静态数据，由原始气象数据计算生成）
    """
    id = models.AutoField(primary_key=True)
    day = models.DateTimeField(verbose_name="日期")
    station = models.ForeignKey(
        Station,
        on_delete=models.DO_NOTHING,
        db_column="station_id",
        related_name="daily_aggregates",
        verbose_name="站点",
    )

    # 温度
    avg_ta = models.FloatField(null=True, verbose_name="日均温度")
    max_ta = models.FloatField(null=True, verbose_name="日最高温度")
    min_ta = models.FloatField(null=True, verbose_name="日最低温度")

    # 湿度
    avg_rh = models.FloatField(null=True, verbose_name="日均湿度")
    max_rh = models.FloatField(null=True, verbose_name="日最大湿度")
    min_rh = models.FloatField(null=True, verbose_name="日最小湿度")

    # 风速
    avg_ws = models.FloatField(null=True, verbose_name="日均风速")
    max_ws = models.FloatField(null=True, verbose_name="日最大风速")

    # 气压
    avg_pressure = models.FloatField(null=True, verbose_name="日均气压")

    # 降水
    total_rainsnow = models.FloatField(null=True, verbose_name="日累计降水")
    max_rainsnow_halfhour = models.FloatField(null=True, verbose_name="日最大半时降水")

    # 雪深
    max_snow_depth = models.FloatField(null=True, verbose_name="日最大雪深")
    max_snow_depth_sr50a = models.FloatField(null=True, verbose_name="日最大SR50A雪深")
    max_snow_depth_ush = models.FloatField(null=True, verbose_name="日最大USH雪深")

    # 辐射
    avg_sw_in = models.FloatField(null=True, verbose_name="日均总辐射")
    max_sw_in = models.FloatField(null=True, verbose_name="日最大总辐射")

    # 土壤含水量
    avg_vwc_10cm = models.FloatField(null=True, verbose_name="日均土壤含水量10cm")
    avg_vwc_20cm = models.FloatField(null=True, verbose_name="日均土壤含水量20cm")
    avg_vwc_40cm = models.FloatField(null=True, verbose_name="日均土壤含水量40cm")
    avg_vwc_60cm = models.FloatField(null=True, verbose_name="日均土壤含水量60cm")
    avg_vwc_100cm = models.FloatField(null=True, verbose_name="日均土壤含水量100cm")

    # 土壤温度
    avg_tsoil_10cm = models.FloatField(null=True, verbose_name="日均土壤温度10cm")
    avg_tsoil_20cm = models.FloatField(null=True, verbose_name="日均土壤温度20cm")
    avg_tsoil_40cm = models.FloatField(null=True, verbose_name="日均土壤温度40cm")
    avg_tsoil_60cm = models.FloatField(null=True, verbose_name="日均土壤温度60cm")
    avg_tsoil_100cm = models.FloatField(null=True, verbose_name="日均土壤温度100cm")

    # 雪水当量
    max_swe = models.FloatField(null=True, verbose_name="日最大雪水当量")
    max_swe_ssg = models.FloatField(null=True, verbose_name="日最大SSG雪水当量")

    # 数据计数
    record_count = models.BigIntegerField(verbose_name="原始记录数")

    class Meta:
        managed = True
        db_table = "weather_daily_agg"
        unique_together = ("day", "station")
        ordering = ["-day", "station_id"]

    def __str__(self):
        return f"{self.station.name} {self.day:%Y-%m-%d}"


class WeatherHourlyAgg(models.Model):
    """
    小时级连续聚合数据（静态数据，由原始气象数据计算生成）
    """
    id = models.AutoField(primary_key=True)
    hour = models.DateTimeField(verbose_name="小时")
    station = models.ForeignKey(
        Station,
        on_delete=models.DO_NOTHING,
        db_column="station_id",
        related_name="hourly_aggregates",
        verbose_name="站点",
    )

    # 温度
    avg_ta = models.FloatField(null=True, verbose_name="小时均温度")
    max_ta = models.FloatField(null=True, verbose_name="小时最高温度")
    min_ta = models.FloatField(null=True, verbose_name="小时最低温度")

    # 湿度
    avg_rh = models.FloatField(null=True, verbose_name="小时均湿度")

    # 风速
    avg_ws = models.FloatField(null=True, verbose_name="小时均风速")
    max_ws = models.FloatField(null=True, verbose_name="小时最大风速")

    # 气压
    avg_pressure = models.FloatField(null=True, verbose_name="小时均气压")

    # 雪深
    max_snow_depth = models.FloatField(null=True, verbose_name="小时最大雪深")

    # 辐射
    avg_sw_in = models.FloatField(null=True, verbose_name="小时均总辐射")

    # 数据计数
    record_count = models.BigIntegerField(verbose_name="原始记录数")

    class Meta:
        managed = True
        db_table = "weather_hourly_agg"
        unique_together = ("hour", "station")
        ordering = ["-hour", "station_id"]

    def __str__(self):
        return f"{self.station.name} {self.hour:%Y-%m-%d %H:00}"
