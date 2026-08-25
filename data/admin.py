from django.contrib import admin
from .models import (
    HydrologyForecastDaily,
    HydrologyForecastRun,
    ManualDataRecord,
    Station,
    WeatherData,
)

@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    """
    站点模型的管理界面配置
    """
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(WeatherData)
class WeatherDataAdmin(admin.ModelAdmin):
    """
    气象数据模型的管理界面配置
    """
    # 在列表页显示的字段
    list_display = ('station', 'timestamp', 'ta', 'rh', 'snow_depth', 'rainsnow', 'pressure')
    
    # 添加过滤器，方便按站点和时间筛选
    list_filter = ('station', 'timestamp')
    
    # 添加搜索功能
    search_fields = ('station__name',)
    
    # 默认按时间倒序排列
    ordering = ('-timestamp',)


@admin.register(ManualDataRecord)
class ManualDataRecordAdmin(admin.ModelAdmin):
    """
    人工录入数据模型的管理界面配置
    """

    list_display = ("operator", "data_at", "value", "is_void", "voided_by", "voided_at", "created_at")
    list_filter = ("operator", "is_void", "data_at", "operated_at")
    search_fields = ("operator__username",)
    ordering = ("-data_at",)


@admin.register(HydrologyForecastRun)
class HydrologyForecastRunAdmin(admin.ModelAdmin):
    list_display = ("run_id", "target_date", "model_name", "model_version", "status", "retry_count", "record_count", "created_at")
    list_filter = ("status", "target_date", "model_name", "model_version", "source")
    search_fields = ("run_id", "error_message")
    ordering = ("-created_at",)


@admin.register(HydrologyForecastDaily)
class HydrologyForecastDailyAdmin(admin.ModelAdmin):
    list_display = ("station", "target_date", "flow_avg", "model_name", "model_version", "run")
    list_filter = ("target_date", "model_name", "model_version")
    search_fields = ("station__name", "run__run_id")
    ordering = ("-target_date", "station__name")
