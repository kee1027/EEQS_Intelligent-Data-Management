from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .tile_views import TileView

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'stations', views.StationViewSet, basename='station')
router.register(r'weatherdata', views.WeatherDataViewSet, basename='weatherdata')
router.register(r'weather-daily-agg', views.WeatherDailyAggViewSet, basename='weather-daily-agg')
router.register(r'weather-hourly-agg', views.WeatherHourlyAggViewSet, basename='weather-hourly-agg')
router.register(r'manual-data', views.ManualDataRecordViewSet, basename='manual-data')
router.register(r'hydrology-runs', views.HydrologyForecastRunViewSet, basename='hydrology-runs')
router.register(r'hydrology-forecast-daily', views.HydrologyForecastDailyViewSet, basename='hydrology-forecast-daily')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("tiles/<str:dataset>/<int:z>/<int:x>/<str:y_ext>", TileView.as_view(), name="tile"),
    path("tasks/<str:task_id>/", views.task_status_view, name="task-status"),
    path("", include(router.urls)),
]
