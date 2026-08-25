"""
Django settings for EEQS-RAG static-data mode.

此配置使用 SQLite 作为数据库（无需运行 PostgreSQL 服务），
所有业务数据通过 `python manage.py load_static_data` 从 JSON 静态文件加载。

环境变量（.env）:
    DJANGO_SECRET_KEY
    DJANGO_DEBUG
    DJANGO_ALLOWED_HOSTS
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-gi#w-gvw)ox)i1au4z8x_#j556nl-$9xue#rfux%($fh%jq7+r",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "data.apps.DataConfig",
    "rest_framework",
    "django_filters",
    'django_apscheduler',
    "drf_spectacular",
    "django_celery_results",
]

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "mysite.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "mysite.wsgi.application"

# SQLite — 无需额外服务，数据通过 load_static_data 注入
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = ["http://*", "https://*"]

# Tile distribution settings (dev defaults)
TILE_DATASETS = {
    "default": BASE_DIR / "data" / "tiles",
    "modis-snow": BASE_DIR / "data" / "tiles_modis_snow",
}
TILE_ALLOWED_EXTENSIONS = ["png", "jpg", "jpeg", "webp", "pbf"]
TILE_MIN_ZOOM = 0
TILE_MAX_ZOOM = 22
TILE_CACHE_CONTROL = "public, max-age=3600"

# Hydrology forecast settings (model script path)
HYDROLOGY_MODEL_SCRIPT_PATH = os.environ.get(
    "HYDROLOGY_MODEL_SCRIPT_PATH",
    r"F:\模型脚本\lstm\lstm_enkf_online_meteorology.py",
)
HYDROLOGY_MODEL_ENTRYPOINT = "run_forecast"
HYDROLOGY_DEFAULT_MODEL_NAME = "lstm"
HYDROLOGY_DEFAULT_MODEL_VERSION = "v1"
HYDROLOGY_RETRY_ATTEMPTS = 3
HYDROLOGY_RETRY_DELAY_SECONDS = 300
HYDROLOGY_DAILY_RUN_HOUR = 1
HYDROLOGY_DAILY_RUN_MINUTE = 0

# drf-spectacular settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'EEQS-RAG API',
    'DESCRIPTION': 'API documentation for EEQS static data backend',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': r'/api/',
}

# =============================================================================
# Celery Configuration (optional — Redis not required in static-data mode)
# =============================================================================
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "")
CELERY_RESULT_BACKEND = "django-db"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = False
CELERY_TASK_TIME_LIMIT = 3600
CELERY_TASK_SOFT_TIME_LIMIT = 3300
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_TASK_ALWAYS_EAGER = False

# Celery Beat schedule (disabled when no broker)
if CELERY_BROKER_URL:
    CELERY_BEAT_SCHEDULE = {
        "import-weather-data": {
            "task": "data.tasks.import_data_task",
            "schedule": 1800.0,
        },
        "daily-hydrology-forecast": {
            "task": "data.tasks.hydrology_forecast_task",
            "schedule": "crontab(hour=1, minute=0)",
            "kwargs": {"triggered_by_id": None, "source": "celery_beat"},
        },
    }
else:
    CELERY_BEAT_SCHEDULE = {}

HYDROLOGY_ASYNC_MODE = False
