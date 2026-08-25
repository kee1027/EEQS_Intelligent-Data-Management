from django.utils import timezone
from rest_framework import serializers
from .models import (
    HydrologyForecastDaily,
    HydrologyForecastRun,
    ManualDataRecord,
    Station,
    WeatherData,
    WeatherDailyAgg,
    WeatherHourlyAgg,
)

class WeatherDataSerializer(serializers.ModelSerializer):
    """
    序列化 WeatherData 模型
    """
    # 使用 StringRelatedField 来直接显示外键关联对象的 __str__ 方法的返回值（即站名）
    station = serializers.StringRelatedField()

    class Meta:
        model = WeatherData
        fields = '__all__'  # 包含所有字段

class StationSerializer(serializers.ModelSerializer):
    """
    序列化 Station 模型
    """
    class Meta:
        model = Station
        fields = ['id', 'name']


class ManualDataRecordSerializer(serializers.ModelSerializer):
    """
    序列化 ManualDataRecord 模型
    """

    operator = serializers.StringRelatedField(read_only=True)
    operated_at = serializers.DateTimeField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    is_void = serializers.BooleanField(read_only=True)
    voided_at = serializers.DateTimeField(read_only=True)
    voided_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ManualDataRecord
        fields = [
            "id",
            "operator",
            "operated_at",
            "data_at",
            "value",
            "is_void",
            "voided_at",
            "voided_by",
            "created_at",
            "updated_at",
        ]

    def validate_data_at(self, value):
        if timezone.is_naive(value):
            return timezone.make_aware(value, timezone.get_current_timezone())
        return value

    def create(self, validated_data):
        validated_data["operator"] = self.context["request"].user
        return super().create(validated_data)


class HydrologyForecastRunSerializer(serializers.ModelSerializer):
    triggered_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = HydrologyForecastRun
        fields = [
            "id",
            "run_id",
            "target_date",
            "model_name",
            "model_version",
            "source",
            "status",
            "retry_count",
            "record_count",
            "error_message",
            "triggered_by",
            "started_at",
            "finished_at",
            "created_at",
            "updated_at",
        ]


class HydrologyForecastDailySerializer(serializers.ModelSerializer):
    station = serializers.StringRelatedField()
    run_id = serializers.CharField(source="run.run_id", read_only=True)

    class Meta:
        model = HydrologyForecastDaily
        fields = [
            "id",
            "station",
            "target_date",
            "flow_avg",
            "model_name",
            "model_version",
            "run_id",
            "created_at",
        ]


class HydrologyForecastRunTriggerSerializer(serializers.Serializer):
    target_date = serializers.DateField()


class WeatherDailyAggSerializer(serializers.ModelSerializer):
    station = serializers.StringRelatedField()

    class Meta:
        model = WeatherDailyAgg
        fields = "__all__"


class WeatherHourlyAggSerializer(serializers.ModelSerializer):
    station = serializers.StringRelatedField()

    class Meta:
        model = WeatherHourlyAgg
        fields = "__all__"
