import django_filters
from .models import HydrologyForecastDaily, HydrologyForecastRun, WeatherData, WeatherDailyAgg, WeatherHourlyAgg


class WeatherDataFilter(django_filters.FilterSet):
    """
    WeatherData 过滤类，支持时间范围查询。

    可用过滤参数:
    - station__name: 站点名称 (精确匹配)
    - timestamp: 精确时间戳
    - timestamp__gte: 大于等于该时间
    - timestamp__lte: 小于等于该时间
    - timestamp__gt: 大于该时间
    - timestamp__lt: 小于该时间
    - timestamp_after: 范围起始时间 (同 timestamp__gte)
    - timestamp_before: 范围结束时间 (同 timestamp__lte)
    - timestamp_range: 时间范围 (from-to)
    """

    timestamp__gte = django_filters.DateTimeFilter(field_name="timestamp", lookup_expr="gte")
    timestamp__lte = django_filters.DateTimeFilter(field_name="timestamp", lookup_expr="lte")
    timestamp__gt = django_filters.DateTimeFilter(field_name="timestamp", lookup_expr="gt")
    timestamp__lt = django_filters.DateTimeFilter(field_name="timestamp", lookup_expr="lt")
    timestamp_range = django_filters.DateTimeFromToRangeFilter(field_name="timestamp")

    # 兼容前端常用别名
    timestamp_after = django_filters.DateTimeFilter(field_name="timestamp", lookup_expr="gte")
    timestamp_before = django_filters.DateTimeFilter(field_name="timestamp", lookup_expr="lte")

    class Meta:
        model = WeatherData
        fields = ["station__name", "timestamp"]


class HydrologyForecastDailyFilter(django_filters.FilterSet):
    """
    HydrologyForecastDaily 过滤类，支持日期范围查询。

    可用过滤参数:
    - station__name: 站点名称 (精确匹配)
    - target_date: 精确日期
    - target_date__gte: 大于等于该日期
    - target_date__lte: 小于等于该日期
    - target_date__gt: 大于该日期
    - target_date__lt: 小于该日期
    - target_date_after: 范围起始日期 (同 gte)
    - target_date_before: 范围结束日期 (同 lte)
    - model_name: 模型名称
    - model_version: 模型版本
    - run__run_id: 运行编号
    """

    target_date__gte = django_filters.DateFilter(field_name="target_date", lookup_expr="gte")
    target_date__lte = django_filters.DateFilter(field_name="target_date", lookup_expr="lte")
    target_date__gt = django_filters.DateFilter(field_name="target_date", lookup_expr="gt")
    target_date__lt = django_filters.DateFilter(field_name="target_date", lookup_expr="lt")
    target_date_range = django_filters.DateFromToRangeFilter(field_name="target_date")

    class Meta:
        model = HydrologyForecastDaily
        fields = ["station__name", "target_date", "model_name", "model_version", "run__run_id"]


class HydrologyForecastRunFilter(django_filters.FilterSet):
    """
    HydrologyForecastRun 过滤类，支持时间范围查询。

    可用过滤参数:
    - target_date: 精确预测日期
    - target_date__gte / target_date__lte: 预测日期范围
    - status: 运行状态
    - model_name: 模型名称
    - model_version: 模型版本
    - source: 触发来源
    - started_at__gte / started_at__lte: 开始时间范围
    - finished_at__gte / finished_at__lte: 结束时间范围
    - created_at__gte / created_at__lte: 创建时间范围
    """

    target_date__gte = django_filters.DateFilter(field_name="target_date", lookup_expr="gte")
    target_date__lte = django_filters.DateFilter(field_name="target_date", lookup_expr="lte")
    target_date_range = django_filters.DateFromToRangeFilter(field_name="target_date")

    started_at__gte = django_filters.DateTimeFilter(field_name="started_at", lookup_expr="gte")
    started_at__lte = django_filters.DateTimeFilter(field_name="started_at", lookup_expr="lte")
    started_at_range = django_filters.DateTimeFromToRangeFilter(field_name="started_at")

    finished_at__gte = django_filters.DateTimeFilter(field_name="finished_at", lookup_expr="gte")
    finished_at__lte = django_filters.DateTimeFilter(field_name="finished_at", lookup_expr="lte")
    finished_at_range = django_filters.DateTimeFromToRangeFilter(field_name="finished_at")

    created_at__gte = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_at__lte = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")
    created_at_range = django_filters.DateTimeFromToRangeFilter(field_name="created_at")

    class Meta:
        model = HydrologyForecastRun
        fields = ["target_date", "status", "model_name", "model_version", "source"]


# =============================================================================
# TimescaleDB Continuous Aggregate Filters
# =============================================================================

class WeatherDailyAggFilter(django_filters.FilterSet):
    """
    WeatherDailyAgg 日级聚合过滤类。

    可用过滤参数:
    - station__name: 站点名称 (精确匹配)
    - day: 精确日期
    - day__gte: 大于等于该日期
    - day__lte: 小于等于该日期
    - day__gt: 大于该日期
    - day__lt: 小于该日期
    - day_after / day_before: 范围查询
    """

    day__gte = django_filters.DateFilter(field_name="day", lookup_expr="gte")
    day__lte = django_filters.DateFilter(field_name="day", lookup_expr="lte")
    day__gt = django_filters.DateFilter(field_name="day", lookup_expr="gt")
    day__lt = django_filters.DateFilter(field_name="day", lookup_expr="lt")
    day_range = django_filters.DateFromToRangeFilter(field_name="day")

    class Meta:
        model = WeatherDailyAgg
        fields = ["station__name", "day"]


class WeatherHourlyAggFilter(django_filters.FilterSet):
    """
    WeatherHourlyAgg 小时级聚合过滤类。

    可用过滤参数:
    - station__name: 站点名称 (精确匹配)
    - hour: 精确时间
    - hour__gte: 大于等于该时间
    - hour__lte: 小于等于该时间
    - hour__gt: 大于该时间
    - hour__lt: 小于该时间
    - hour_after / hour_before: 范围查询
    """

    hour__gte = django_filters.DateTimeFilter(field_name="hour", lookup_expr="gte")
    hour__lte = django_filters.DateTimeFilter(field_name="hour", lookup_expr="lte")
    hour__gt = django_filters.DateTimeFilter(field_name="hour", lookup_expr="gt")
    hour__lt = django_filters.DateTimeFilter(field_name="hour", lookup_expr="lt")
    hour_range = django_filters.DateTimeFromToRangeFilter(field_name="hour")

    class Meta:
        model = WeatherHourlyAgg
        fields = ["station__name", "hour"]
