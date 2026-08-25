# 04 · 数据查询（Text2SQL）与权限控制

> 目标：让智能体安全地把自然语言变成 SQL 查 EEQS 业务库——**生成得准、执行得稳、越权不可能**。

---

## 1. 先想清楚：三层防线

```
第一层（生成层）  好的 schema 描述 + few-shot → 提高 SQL 正确率
第二层（校验层）  sqlglot AST 白名单校验      → 恶意/错误 SQL 到不了数据库
第三层（数据库层）只读账号 + 行级安全          → 即使前两层全破，损失也可控
```
> 任何"靠提示词让模型别写 DELETE"的方案都不算防线。

---

## 2. Schema 管理：Text2SQL 准确率的地基

模型生成错误 SQL 的首要原因是**看不懂你的表**。给每张表维护一份元数据（放 YAML 或数据库表里）：

```yaml
# app/db/schema_meta.yaml
- table: monitoring_data
  comment: 监测数据主表，每行是某站点某指标某时刻的一条监测值
  columns:
    - {name: id,         type: bigint,    comment: 主键}
    - {name: station_id, type: varchar,   comment: 站点编号，关联 station.id}
    - {name: indicator,  type: varchar,   comment: 指标代码，如 COD/NH3N/PM25}
    - {name: value,      type: numeric,   comment: 监测值}
    - {name: measured_at,type: timestamp, comment: 监测时间（UTC+8）}
  sample_questions:
    - q: 上个月 A 站点的 COD 平均值
      sql: SELECT AVG(value) FROM monitoring_data WHERE station_id='A' AND indicator='COD' AND measured_at >= date_trunc('month', now() - interval '1 month') ...
  permission: {min_role: viewer, row_filter_column: station_id}
```

**表太多塞不进 prompt？用 RAG 选表**：把所有表的元数据文本向量化，用户提问时先检索 top-5 相关表，只把这几张表的 schema 塞进生成 prompt。这招叫 schema linking，是工业界标配（06 篇的向量库可直接复用）。

---

## 3. SQL 生成工具（含校验）

```python
# app/security/sql_guard.py
import sqlglot
from sqlglot import exp

ALLOWED_TABLES = {"monitoring_data", "station", "indicator_dict"}  # 白名单
MAX_LIMIT = 500

class SqlRejected(Exception): pass

def validate_readonly(sql: str, dialect: str = "postgres") -> str:
    """AST 级校验；通过则返回改写后的安全 SQL，否则抛 SqlRejected。"""
    try:
        statements = sqlglot.parse(sql, read=dialect)
    except sqlglot.errors.ParseError as e:
        raise SqlRejected(f"SQL 无法解析: {e}")

    if len(statements) != 1:
        raise SqlRejected("只允许单条语句")   # 拦 "SELECT 1; DROP TABLE x"
    tree = statements[0]

    if not isinstance(tree, exp.Select):
        raise SqlRejected("只允许 SELECT 查询")  # INSERT/UPDATE/DELETE/DDL 全拒

    # 白名单表 + 禁止危险函数
    for table in tree.find_all(exp.Table):
        if table.name not in ALLOWED_TABLES:
            raise SqlRejected(f"表 {table.name} 不在允许范围")
    for func in tree.find_all(exp.Func):
        if func.sql_name().lower() in {"pg_sleep", "set_config", "lo_export"}:
            raise SqlRejected("包含危险函数")

    # 自动补 LIMIT（防爆量）
    if tree.args.get("limit") is None:
        tree = tree.limit(MAX_LIMIT)
    return tree.sql(dialect=dialect)
```

```python
# app/tools/sql_tool.py
from sqlalchemy import create_engine, text
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langchain.chat_models import init_chat_model

from app.core.config import settings
from app.security.sql_guard import validate_readonly, SqlRejected
from app.db.schema import pick_relevant_schema   # RAG 选表，返回 schema 文本
from app.security.rbac import check_table_permission, row_filter_for

engine_ro = create_engine(settings.database_url_ro, pool_size=5)
sql_writer_model = init_chat_model(f"{settings.llm_provider}:{settings.llm_model}",
                                   api_key=settings.deepseek_api_key, temperature=0)

GEN_PROMPT = """你是 PostgreSQL 专家。根据 schema 和用户问题生成一条 SELECT。
规则：只输出 SQL；时间字段是 measured_at；数值统计要 ROUND(x,2)。
{few_shots}
Schema:
{schema}
问题：{question}"""

@tool
def query_database(question: str, config: RunnableConfig) -> str:
    """用自然语言查询 EEQS 监测数据库。输入：用户的查询问题（自然语言）。
    返回：查询结果的表格文本。只能查询，不能修改数据。"""
    roles = (config.get("metadata") or {}).get("roles", [])

    schema, tables = pick_relevant_schema(question)          # ① RAG 选表
    check_table_permission(roles, tables)                    # ② 表级 RBAC

    raw = sql_writer_model.invoke(GEN_PROMPT.format(
        schema=schema, question=question, few_shots=load_few_shots(question)
    )).content.strip().removeprefix("```sql").removesuffix("```")

    try:
        safe_sql = validate_readonly(raw)                    # ③ AST 校验
    except SqlRejected as e:
        return f"查询被安全策略拒绝：{e}"

    safe_sql = row_filter_for(roles, safe_sql)               # ④ 行级权限注入 WHERE

    with engine_ro.connect() as conn:                        # ⑤ 只读账号执行
        conn.exec_driver_sql("SET statement_timeout = '10s'")  # 会话级超时
        result = [dict(r._mapping)
                  for r in conn.execute(text(safe_sql)).fetchmany(50)]

    audit_log(user=config, question=question, sql=safe_sql, rows=len(result))  # ⑥ 审计
    if not result:
        return "查询成功但没有匹配数据。可以建议用户检查时间范围或站点名。"
    return to_markdown_table(result)
```

要点：
- **模型只生成，代码做裁判**：生成错 SQL 是常态，校验 + 友好报错 + 让模型重试一轮（可加 self-correction 循环）比追求一次生成完美 SQL 更现实。
- `statement_timeout` 防止慢查询拖垮库；`fetchmany(50)` 防超长结果塞爆上下文。
- 审计日志必须记 SQL 原文——出了事能复盘，也是 05 篇注入检测的数据源。

---

## 4. 提高 SQL 准确率的三板斧

1. **Few-shot 示例**：在 `sample_questions` 里积累"问题→标准 SQL"对，按问题相似度检索 2~3 条塞进 prompt。这是性价比最高的优化。
2. **自我修正循环**：执行报错时把错误信息回给模型重生成（最多 2 次），能修掉大部分语法/列名错误。
3. **歧义主动澄清**：用户说"最近的数据"，宁可反问"最近 7 天还是 30 天？"也不要猜——在工具返回里写"请向用户澄清 X"，模型会照做。

---

## 5. 权限体系（RBAC + 行级）

```python
# app/security/rbac.py
TABLE_ACL = {
    "monitoring_data": {"viewer", "analyst", "admin"},
    "station":         {"viewer", "analyst", "admin"},
    "user_account":    {"admin"},                       # 敏感表只有 admin
}
ROW_SCOPE = {  # 行级：普通用户只能看自己辖区的站点
    "analyst": lambda uid: f"station_id IN (SELECT station_id FROM user_station WHERE user_id = '{uid}')"
}

class Forbidden(Exception): pass

def check_table_permission(roles: list[str], tables: list[str]):
    for t in tables:
        allowed = TABLE_ACL.get(t, set())
        if not allowed.intersection(roles):
            raise Forbidden(f"无权访问表 {t}")

def row_filter_for(roles, sql, user_id) -> str:
    if "admin" in roles: return sql
    filt = ROW_SCOPE.get(max(roles, default="viewer"), lambda u: None)(user_id)
    return inject_where(sql, filt) if filt else sql   # 用 sqlglot 改写 AST 注入条件
```

数据库层兜底（PostgreSQL 行级安全示例，双保险）：
```sql
CREATE ROLE eeqs_readonly LOGIN PASSWORD '...';
GRANT CONNECT ON DATABASE eeqs TO eeqs_readonly;
GRANT SELECT ON monitoring_data, station, indicator_dict TO eeqs_readonly;
ALTER TABLE monitoring_data ENABLE ROW LEVEL SECURITY;
CREATE POLICY p_station ON monitoring_data
  USING (station_id = current_setting('app.station_scope', true));
```

---

## 6. 增删改：为什么坚决不走 SQL

| 直连执行 DML | 调主后端 API |
|---|---|
| 绕过主后端的参数校验、状态机、事务 | 全部复用 |
| 审计断链 | 主后端日志天然完整 |
| AI 服务需要写账号（攻击面↑） | AI 服务只带内部 token 调 API |

流程：**模型解析参数 → `interrupt` 给用户复述确认 → 确认后调主后端 API → 返回结果**（代码见 03 篇 §6）。再叠加两条规则：
- 写操作工具单独设角色门槛（如仅 `admin`/`operator` 角色出现在工具列表里——**按角色动态裁剪 tools**，这是最简单有效的权限手段）：

```python
def tools_for(roles: list[str]):
    base = [query_database, search_knowledge, forecast_indicator]
    if {"admin", "operator"} & set(roles):
        base += [create_record, update_record, delete_record]
    return base
# 普通用户的 Agent 根本"看不见"删除工具，注入也无从谈起
```

---

## 7. 评估：SQL 准确率怎么量

建一个 50~100 条的评测集（自然语言问题 + 标准 SQL），离线跑：
```bash
uv run python -m app.eval.text2sql_eval --dataset eval/text2sql.jsonl
```
指标：可执行率（语法对）、结果匹配率（执行结果与标准 SQL 一致）。每次改 prompt/换模型都跑一遍，防止"越改越烂"（回归）。

---

## ✅ 本篇动手清单
- [ ] 给 EEQS 核心表写 `schema_meta.yaml`（至少 3 张表，含注释和 5 条示例 QA）
- [ ] 实现 `validate_readonly` 并用「`DELETE FROM ...`、`SELECT 1; DROP TABLE`、`pg_sleep(10)`」三个恶意用例自测拦截
- [ ] 申请只读账号并用它连库，验证 `GRANT` 之外的操作全部报权限错误
- [ ] 攒 20 条真实业务问题作为评测集 v1
