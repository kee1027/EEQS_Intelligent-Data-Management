# EEQS-RAG 水文预测 API 文档（前端用）

> 基础地址：`http://<host>:8000`
> 认证：**HTTP Basic Auth**（或 Django Session 登录）。所有接口都需要认证，未认证返回 `401`。
> 交互式文档（Swagger UI）：`http://<host>:8000/api/schema/swagger-ui/`

## 目录

- [1. 查询预测结果（列表）](#1-查询预测结果列表)
- [2. 查询最新预测（画图推荐）](#2-查询最新预测画图推荐)
- [3. 查询 / 触发预测运行](#3-查询--触发预测运行)
- [4. 错误码](#4-错误码)
- [附录 A. 预测流水线与文件 Schema](#附录-a-预测流水线与文件-schema)

---

## 1. 查询预测结果（列表）

`GET /api/hydrology-forecast-daily/`

返回数组（**不分页**），默认按 `target_date` 倒序。

### 过滤参数

| 参数 | 说明 | 示例 |
|---|---|---|
| `station__name` | 站点名（精确匹配） | `station__name=HXC` |
| `target_date` | 精确日期 | `target_date=2026-06-28` |
| `target_date__gte` / `target_date__lte` | 日期范围（含边界） | `target_date__gte=2026-06-27&target_date__lte=2026-07-03` |
| `target_date__gt` / `target_date__lt` | 日期范围（不含边界） | — |
| `target_date_range_after` / `target_date_range_before` | 范围另一种写法 | — |
| `model_name` / `model_version` | 模型名称 / 版本 | `model_name=mock-scale-7day` |
| `run__run_id` | 运行编号 | `run__run_id=hydro-20260909-001` |

### 响应示例

`GET /api/hydrology-forecast-daily/?station__name=HXC&target_date__gte=2026-06-28&target_date__lte=2026-06-29`

```json
[
  {
    "id": 3,
    "station": "HXC",
    "target_date": "2026-06-29",
    "flow_avg": "23724.168",
    "model_name": "mock-scale-7day",
    "model_version": "v1",
    "run_id": "hydro-20260909-001",
    "created_at": "2026-09-09T16:55:26.438078+08:00"
  },
  {
    "id": 2,
    "station": "HXC",
    "target_date": "2026-06-28",
    "flow_avg": "21088.149",
    "model_name": "mock-scale-7day",
    "model_version": "v1",
    "run_id": "hydro-20260909-001",
    "created_at": "2026-09-09T16:55:26.432419+08:00"
  }
]
```

> 注意：`flow_avg` 是十进制字符串。同一 `station + target_date + model_name + model_version`
> 组合只会保留最新一次运行的结果（后跑的运行会覆盖先跑的同一预测日记录）。

---

## 2. 查询最新预测（画图推荐）

`GET /api/hydrology-forecast-daily/latest/`

返回**最近一次成功运行**产生的、按站点分组的未来 7 天预测序列，前端可直接用来画折线图。

### 响应示例（真实数据截断）

```json
{
  "run_id": "hydro-20260909-002",
  "target_date": "2026-06-20",
  "model_name": "mock-scale-7day",
  "model_version": "v1",
  "stations": [
    {
      "station": "AKSL",
      "forecasts": [
        { "target_date": "2026-06-21", "flow_avg": "10566.789" },
        { "target_date": "2026-06-22", "flow_avg": "12076.331" },
        { "target_date": "2026-06-23", "flow_avg": "13585.872" },
        { "target_date": "2026-06-24", "flow_avg": "15095.413" },
        { "target_date": "2026-06-25", "flow_avg": "16604.955" },
        { "target_date": "2026-06-26", "flow_avg": "18114.496" },
        { "target_date": "2026-06-27", "flow_avg": "19624.037" }
      ]
    },
    { "station": "HXC", "forecasts": [ "... 同样 7 条 ..." ] }
  ]
}
```

- `target_date`（顶层）= 本次预测的基准日 D，`forecasts` 里是 D+1 ~ D+7。
- 尚未有任何成功运行时返回 `200` + `{"run_id": null, ..., "stations": []}`。

---

## 3. 查询 / 触发预测运行

### 3.1 运行列表

`GET /api/hydrology-runs/`

过滤参数：`target_date`、`status`（`running` / `success` / `failed`）、`model_name`、`model_version`、`source`。

```json
[
  {
    "id": 2,
    "run_id": "hydro-20260909-002",
    "target_date": "2026-06-20",
    "model_name": "mock-scale-7day",
    "model_version": "v1",
    "source": "manual_api",
    "status": "success",
    "retry_count": 0,
    "record_count": 56,
    "error_message": "",
    "triggered_by": "shy",
    "started_at": "2026-09-09T16:57:50.674786+08:00",
    "finished_at": "2026-09-09T16:57:52.332417+08:00"
  }
]
```

`status=failed` 时看 `error_message` 获取可读错误（如「模型镜像不存在」「docker 不可用」「输出文件格式错误」）。

### 3.2 手动触发一次预测（仅管理员）

`POST /api/hydrology-runs/`，**要求 `is_staff` 用户**，否则 `403`。

请求体：

```json
{ "target_date": "2026-06-26" }
```

同步执行（导出输入 → 跑模型容器 → 入库），完成后返回 `201` 与运行记录（结构同上）。
当前为模拟模型，一次运行约 2~5 秒；真实模型替换后耗时取决于模型本身。

---

## 4. 错误码

| 状态码 | 场景 |
|---|---|
| `200` | 查询成功 |
| `201` | 触发预测成功（响应即运行记录，内含 `status`/`record_count`） |
| `400` | 请求参数非法（如 `target_date` 格式不是 `YYYY-MM-DD`） |
| `401` | 未认证或认证失败 |
| `403` | 非管理员调用 POST 触发接口 |
| `404` | 路由或对象不存在 |

---

## 附录 A. 预测流水线与文件 Schema

### 工作方式（文件交换式）

```
后端导出输入文件 ──> docker run -v <宿主目录>:/io eeqs-prediction-model ──> 后端解析输出文件入库
backend/prediction_io/<run_id>/input/    （容器内 /io/input/）
backend/prediction_io/<run_id>/output/   （容器内 /io/output/）
```

### 输入文件（后端 → 模型）

- `_meta.json`：运行元信息

```json
{ "run_id": "hydro-20260909-001", "target_date": "2026-06-26", "input_days": 30, "generated_at": "..." }
```

- `station_<station_id>.json`：每个站点一个文件。`series` 为该站点在基准日
  `target_date` 之前最近 `input_days` 天（默认 30，可由 `HYDROLOGY_INPUT_DAYS` 配置）
  的日聚合观测，**时间正序**：

```json
{
  "station_id": 2,
  "station_name": "HXC",
  "series": [
    {
      "day": "2026-05-27",
      "avg_ta": 5.811,
      "total_rainsnow": 25353.353,
      "max_snow_depth": 90.389,
      "max_swe": 382.8,
      "avg_sw_in": 374.036,
      "avg_vwc_10cm": 0.146
    }
  ]
}
```

### 输出文件（模型 → 后端）

- `station_<station_id>.json`：与输入文件同名，每站一个：

```json
{
  "station": "HXC",
  "station_id": 2,
  "model_name": "mock-scale-7day",
  "model_version": "v1",
  "base_date": "2026-06-26",
  "baseline": 26360.186,
  "forecasts": [
    { "target_date": "2026-06-27", "flow_avg": 18452.13, "scale_factor": 0.7 }
  ]
}
```

- 模型出错时写 `_error.json`（`{"error": ..., "traceback": ...}`）并以非零码退出，
  后端会把错误记录到运行的 `error_message`。

### 当前模拟模型的语义

- 基准值 `baseline` = 输入序列**最后 7 天** `total_rainsnow`（日累计降水）的均值；
  全缺失时退化为全部可用天数均值，再退化为 `0`。
- 未来 D+1 ~ D+7 的 `flow_avg = baseline × scale_factor`，
  系数依次为 `0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3`。
- 入库唯一键：`station + target_date + model_name + model_version`（重复运行覆盖更新）。

### 运维速查

```bash
cd backend
docker-compose up -d                                   # 起 PostgreSQL（eeqs/eeqs_dev_password@localhost:5432/eeqs）
python manage.py migrate && python manage.py load_static_data
docker build -t eeqs-prediction-model:latest prediction_model/
python manage.py run_hydrology_forecast --date 2026-06-26 --manual
```
