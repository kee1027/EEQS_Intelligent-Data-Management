# EEQS 智能问答系统 — 前后端分离项目

```
my-weather-system/
├── backend/     ← Django REST API（电脑 A 主要工作区）
└── frontend/    ← 前端应用（电脑 B 主要工作区）
```

## 快速启动

### 后端（backend/）

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py load_static_data   # 注入静态数据
python manage.py runserver
```

API 文档：`http://localhost:8000/api/schema/swagger-ui/`

### 前端（frontend/）

待补充……
