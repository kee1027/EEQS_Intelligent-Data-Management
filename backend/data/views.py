from django.db import IntegrityError
from django.utils import timezone
from celery.result import AsyncResult
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.response import Response

from .filters import (
    HydrologyForecastDailyFilter,
    WeatherDailyAggFilter,
    WeatherHourlyAggFilter,
)
from .hydrology_service import run_hydrology_forecast
from .models import (
    HydrologyForecastDaily,
    HydrologyForecastRun,
    ManualDataRecord,
    Station,
    WeatherData,
    WeatherDailyAgg,
    WeatherHourlyAgg,
)
from .serializers import (
    HydrologyForecastDailySerializer,
    HydrologyForecastRunSerializer,
    HydrologyForecastRunTriggerSerializer,
    ManualDataRecordSerializer,
    StationSerializer,
    WeatherDataSerializer,
    WeatherDailyAggSerializer,
    WeatherHourlyAggSerializer,
)


class OptimizedPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000


class StationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows stations to be viewed.
    """
    queryset = Station.objects.all()
    serializer_class = StationSerializer

class WeatherDataViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows weather data to be viewed.
    Provides filtering by station name and timestamp.
    
    Performance optimizations:
    - Limited field serialization (避免序列化 90+ 个字段)
    - Automatic pagination (reduce memory footprint)
    - Only fetches related station data when needed
    
    Examples:
    /api/weatherdata/?station__name=HXC&page=1&page_size=100
    /api/weatherdata/?timestamp=2026-02-08T21:30:00Z&page=1
    """
    queryset = WeatherData.objects.select_related('station').all().order_by('-timestamp')
    serializer_class = WeatherDataSerializer
    filterset_fields = ['station__name', 'timestamp']
    pagination_class = OptimizedPagination


class ConflictError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "该操作人员在该数据时间已有记录，不允许重复。"
    default_code = "conflict"


class AlreadyVoidedError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "该记录已作废，无需重复作废。"
    default_code = "already_voided"


class ManualDataRecordViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    API endpoint that allows manual data to be created.
    """

    queryset = ManualDataRecord.objects.select_related("operator").all()
    serializer_class = ManualDataRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_create(serializer)
        except IntegrityError as exc:
            raise ConflictError() from exc
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=["post"], url_path="void")
    def void(self, request, *args, **kwargs):
        record = self.get_object()
        if record.operator_id != request.user.id and not request.user.is_staff:
            raise PermissionDenied("仅创建该记录的用户或管理员可作废。")
        if record.is_void:
            raise AlreadyVoidedError()

        record.is_void = True
        record.voided_at = timezone.now()
        record.voided_by = request.user
        record.save(update_fields=["is_void", "voided_at", "voided_by", "updated_at"])

        serializer = self.get_serializer(record)
        return Response(serializer.data, status=status.HTTP_200_OK)


class HydrologyForecastRunViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = HydrologyForecastRun.objects.select_related("triggered_by").all()
    serializer_class = HydrologyForecastRunSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["target_date", "status", "model_name", "model_version", "source"]

    def get_serializer_class(self):
        if self.action == "create":
            return HydrologyForecastRunTriggerSerializer
        return HydrologyForecastRunSerializer

    def create(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied("仅管理员可手动补跑预测任务。")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        run = run_hydrology_forecast(
            target_date=serializer.validated_data["target_date"],
            triggered_by=request.user,
            source="manual_api",
        )
        data = HydrologyForecastRunSerializer(instance=run).data
        return Response(data, status=status.HTTP_201_CREATED)


class HydrologyForecastDailyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    预测结果查询。

    - 列表支持过滤: station__name / target_date / target_date__gte / target_date__lte /
      model_name / model_version / run__run_id
    - GET /api/hydrology-forecast-daily/latest/ 返回最近一次成功运行
      每个站点的未来 7 天预测序列，便于前端直接画图。
    """
    queryset = HydrologyForecastDaily.objects.select_related("station", "run").all()
    serializer_class = HydrologyForecastDailySerializer
    filterset_class = HydrologyForecastDailyFilter

    @action(detail=False, methods=["get"])
    def latest(self, request):
        run = (
            HydrologyForecastRun.objects.filter(
                status=HydrologyForecastRun.Status.SUCCESS, record_count__gt=0
            )
            .order_by("-finished_at", "-created_at")
            .first()
        )
        if run is None:
            return Response(
                {"run_id": None, "target_date": None, "model_name": None,
                 "model_version": None, "stations": []},
                status=status.HTTP_200_OK,
            )

        qs = (
            HydrologyForecastDaily.objects.filter(run=run)
            .select_related("station")
            .order_by("station__name", "target_date")
        )
        stations = {}
        for row in qs:
            entry = stations.setdefault(row.station.name, [])
            entry.append(
                {"target_date": row.target_date.isoformat(), "flow_avg": str(row.flow_avg)}
            )

        payload = {
            "run_id": run.run_id,
            "target_date": run.target_date.isoformat(),
            "model_name": run.model_name,
            "model_version": run.model_version,
            "stations": [
                {"station": name, "forecasts": forecasts}
                for name, forecasts in stations.items()
            ],
        }
        return Response(payload, status=status.HTTP_200_OK)


class WeatherDailyAggViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WeatherDailyAgg.objects.select_related("station").all()
    serializer_class = WeatherDailyAggSerializer
    filterset_class = WeatherDailyAggFilter
    pagination_class = None


class WeatherHourlyAggViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WeatherHourlyAgg.objects.select_related("station").all()
    serializer_class = WeatherHourlyAggSerializer
    filterset_class = WeatherHourlyAggFilter
    pagination_class = None


@api_view(["GET"])
def task_status_view(request, task_id):
    task = AsyncResult(task_id)
    payload = {
        "task_id": task_id,
        "status": task.status,
        "ready": task.ready(),
        "successful": task.successful() if task.ready() else False,
    }
    if task.ready():
        if task.successful():
            payload["result"] = task.result
        else:
            payload["error"] = str(task.result)
    return Response(payload, status=status.HTTP_200_OK)
