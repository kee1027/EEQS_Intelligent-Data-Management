"""
Django settings for EEQS-RAG backend.

数据库默认使用 Docker 中的 PostgreSQL（见 backend/docker-compose.yml，
连接参数 eeqs/eeqs_dev_password@localhost:5432/eeqs），可通过环境变量覆盖。
业务数据通过 `python manage.py load_static_data` 从 JSON 静态文件加载。

水文预测采用「文件交换式」流水线：后端导出输入文件 ->
Docker 容器中的模型读取/写回文件 -> 后端解析入库（见 data/hydrology_service.py）。

环境变量（可写在 backend/.env，本文件会自动读取）:
    DJANGO_SECRET_KEY / DJANGO_DEBUG / DJANGO_ALLOWED_HOSTS
    DB_ENGINE / DB_NAME / DB_USER / DB_PASSWORD / DB_HOST / DB_PORT
    HYDROLOGY_MODEL_IMAGE / HYDROLOGY_DOCKER_BIN / HYDROLOGY_IO_DIR
    HYDROLOGY_INPUT_DAYS / HYDROLOGY_DOCKER_TIMEOUT_SECONDS
    HYDROLOGY_DEFAULT_MODEL_NAME / HYDROLOGY_DEFAULT_MODEL_VERSION
    HYDROLOGY_RETRY_ATTEMPTS / HYDROLOGY_RETRY_DELAY_SECONDS
    CELERY_BROKER_URL
    LLM_API_KEY / LLM_BASE_URL / LLM_MODEL（AI 问答，见文件末尾 AI 配置块）
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv(path):
    """极简 .env 加载器：KEY=VALUE 逐行读取，不覆盖已存在的系统环境变量。"""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv(BASE_DIR / ".env")

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
    "ai_assistant",
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

# 数据库 —— 默认指向 Docker 中的 PostgreSQL（backend/docker-compose.yml），
# 全部参数可用环境变量覆盖；如需临时回退 SQLite，设置
# DB_ENGINE=django.db.backends.sqlite3 且 DB_NAME=db.sqlite3 即可。
_default_db_engine = os.environ.get("DB_ENGINE", "django.db.backends.postgresql")
_default_db_name = os.environ.get("DB_NAME", "eeqs")
if _default_db_engine == "django.db.backends.sqlite3" and not os.environ.get("DB_NAME"):
    _default_db_name = BASE_DIR / "db.sqlite3"

DATABASES = {
    "default": {
        "ENGINE": _default_db_engine,
        "NAME": _default_db_name,
        "USER": os.environ.get("DB_USER", "eeqs"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "eeqs_dev_password"),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
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

# Hydrology forecast settings —— 文件交换式 Docker 模型流水线
# 流程：导出输入文件 -> docker run 挂载 IO 目录运行模型容器 -> 解析输出文件入库
HYDROLOGY_MODEL_IMAGE = os.environ.get("HYDROLOGY_MODEL_IMAGE", "eeqs-prediction-model:latest")
# docker 可执行文件；留空时自动探测 PATH，再回退 Docker Desktop 默认安装路径
HYDROLOGY_DOCKER_BIN = os.environ.get("HYDROLOGY_DOCKER_BIN", "")
# 宿主机 IO 根目录（其下按 <run_id>/input、<run_id>/output 组织）
HYDROLOGY_IO_DIR = os.environ.get("HYDROLOGY_IO_DIR", str(BASE_DIR / "prediction_io"))
# 输入序列天数（每个站点取 target_date 之前最近 N 天的日聚合观测）
HYDROLOGY_INPUT_DAYS = int(os.environ.get("HYDROLOGY_INPUT_DAYS", "30"))
# 模型容器运行超时（秒）
HYDROLOGY_DOCKER_TIMEOUT_SECONDS = int(os.environ.get("HYDROLOGY_DOCKER_TIMEOUT_SECONDS", "300"))
HYDROLOGY_DEFAULT_MODEL_NAME = os.environ.get("HYDROLOGY_DEFAULT_MODEL_NAME", "mock-scale-7day")
HYDROLOGY_DEFAULT_MODEL_VERSION = os.environ.get("HYDROLOGY_DEFAULT_MODEL_VERSION", "v1")
HYDROLOGY_RETRY_ATTEMPTS = int(os.environ.get("HYDROLOGY_RETRY_ATTEMPTS", "3"))
HYDROLOGY_RETRY_DELAY_SECONDS = int(os.environ.get("HYDROLOGY_RETRY_DELAY_SECONDS", "300"))
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

# =============================================================================
# AI 智能问答（ai_assistant app）
# =============================================================================
# LLM：任一 OpenAI 兼容协议的服务（DeepSeek / Kimi / 通义等），换厂商只改这里
AI_LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
AI_LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com")
AI_LLM_MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")
AI_LLM_TIMEOUT_SECONDS = int(os.environ.get("LLM_TIMEOUT_SECONDS", "60"))

# Text2SQL 安全阈值
AI_SQL_MAX_ROWS = int(os.environ.get("AI_SQL_MAX_ROWS", "50"))
AI_SQL_TIMEOUT_SECONDS = int(os.environ.get("AI_SQL_TIMEOUT_SECONDS", "10"))

# 统计外推（M3）：置信度低于该阈值时拒绝回答并提示转人工
EXTRAPOLATION_MIN_CONFIDENCE = float(os.environ.get("EXTRAPOLATION_MIN_CONFIDENCE", "0.6"))

# RAG 知识库（M4）：BGE-M3 模型路径（HuggingFace 名或本地目录）与检索条数
BGE_M3_MODEL_PATH = os.environ.get("BGE_M3_MODEL_PATH", "BAAI/bge-m3")
RAG_TOP_K = int(os.environ.get("RAG_TOP_K", "5"))
