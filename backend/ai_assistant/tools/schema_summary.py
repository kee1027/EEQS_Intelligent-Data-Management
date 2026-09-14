"""
Text2SQL 的 schema 摘要构建器。

把表白名单内每张表的「列名 + 类型 + 中文注释」整理成纯文本，喂给写 SQL 的 LLM。
中文注释直接来自 data/models.py 里每个字段的 verbose_name——
这是 Text2SQL 准确率最重要的单点优化：模型只有知道 avg_ta 是「日均温度」，
才能把用户说的「温度」映射到正确的列。

表级说明（表是干什么的、时间粒度、注意事项）在 TABLE_DESCRIPTIONS 里手工维护，
因为这类信息（如「预测表同一日期可能有多版本模型结果」）无法从代码推断。
"""

from data.models import (
    HydrologyForecastDaily,
    HydrologyForecastRun,
    Station,
    WeatherDailyAgg,
    WeatherHourlyAgg,
)

# 白名单模型 + 表级业务说明（写 SQL 的 LLM 需要知道的"坑"都写在这里）
WHITELIST_MODELS = [
    (
        Station,
        "站点表。所有业务数据都通过 station_id 关联到这里。站点名如 'HXC'、'KKSLS'、'AKSL'。",
    ),
    (
        WeatherDailyAgg,
        "气象观测日聚合表（推荐优先使用）。每站每天一行，day 为当日 00:00 的时间戳。"
        "含温度/湿度/风速/气压/降水/雪深/辐射/土壤含水量/土壤温度/雪水当量的日统计量。",
    ),
    (
        WeatherHourlyAgg,
        "气象观测小时聚合表。每站每小时一行，适合查询日内变化过程。",
    ),
    (
        HydrologyForecastRun,
        "预测运行记录表。一次运行(run)对多个站点产出未来 7 天预测；"
        "status 为 success 的才是有效结果，failed 的看 error_message。",
    ),
    (
        HydrologyForecastDaily,
        "水文预测结果表。每站每预测日一行日均流量 flow_avg（单位见业务约定）。"
        "注意：同一 station+target_date 可能有多个 model_name/model_version 的结果，"
        "查询时应优先取最新一次成功运行（可按 created_at 或 run_id 排序取最新）。",
    ),
]

# 只暴露给 LLM 的列（排除 id 等无业务含义的列）
_EXCLUDE_FIELDS = {"id"}


def _model_table_summary(model, table_description: str) -> str:
    table_name = model._meta.db_table
    lines = [f"表 {table_name} —— {table_description}"]
    for field in model._meta.fields:
        if field.name in _EXCLUDE_FIELDS:
            continue
        column = field.column
        comment = str(field.verbose_name) if field.verbose_name else ""
        fk_hint = ""
        if field.is_relation:
            fk_hint = f"（外键 → {field.related_model._meta.db_table}.id）"
        lines.append(f"  {column} {field.get_internal_type()} -- {comment}{fk_hint}")
    return "\n".join(lines)


def build_schema_summary() -> str:
    """生成完整 schema 摘要文本。"""
    parts = [
        "可用数据表（只允许查询这些表，均为 PostgreSQL 表）：",
        "",
    ]
    for model, description in WHITELIST_MODELS:
        parts.append(_model_table_summary(model, description))
        parts.append("")
    parts.append(
        "补充约定：\n"
        "- 站点关联：各业务表都有 station_id 外键；按站名过滤请 JOIN data_station 或子查询。\n"
        "- 时间过滤：weather_daily_agg.day 与 weather_hourly_agg.hour 是 timestamp，"
        "  按天过滤建议用 day >= 'YYYY-MM-DD' AND day < 'YYYY-MM-DD' 半开区间。\n"
        "- 预测表日期 target_date 是 date 类型，直接等值或范围比较即可。"
    )
    return "\n".join(parts)
