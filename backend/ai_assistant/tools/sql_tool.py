"""
Text2SQL 工具：自然语言 → SQL → 校验 → 只读执行 → 表格化结果。

架构上采用「两段式 LLM」：
- 外层 Agent（graph.py）负责理解用户意图、决定何时调用本工具；
- 本工具内部再用一次 LLM 专门写 SQL（schema 摘要 + 严格规则的专用 prompt）。

这样 Agent 的上下文里只出现「业务结果」，不出现 SQL 细节，
主对话更干净；SQL 生成的 prompt 也可以独立迭代优化。

安全链路：LLM 写的 SQL → sql_guard.validate_readonly_sql（AST 级只读校验）
→ 失败直接返回错误说明（不执行）→ 通过才执行，且限制行数与超时。
全程写 AiAuditLog 审计日志。
"""

import re
import time

from django.conf import settings
from django.db import connection
from langchain_core.tools import tool

from ..agent.llm import get_chat_model
from ..models import AiAuditLog
from ..security.sql_guard import SqlValidationError, extract_tables, validate_readonly_sql
from .schema_summary import build_schema_summary

_SQL_WRITER_PROMPT = """你是一个 PostgreSQL SQL 编写器。根据用户问题和数据库 schema 生成一条查询 SQL。

硬性规则（违反任何一条都会导致执行被拒绝）：
1. 只输出一条 SELECT 语句，不要输出任何解释、注释或 markdown 代码块标记
2. 只能查询 schema 中列出的表
3. 必须包含 LIMIT（不超过 {max_rows}）
4. 不要使用任何写操作、函数副作用或系统函数

{schema}
"""


def _strip_code_fences(text: str) -> str:
    """LLM 有时不自觉地把 SQL 包在 ```sql ... ``` 里，剥掉。"""
    text = text.strip()
    match = re.match(r"^```(?:sql|SQL)?\s*(.*?)\s*```$", text, re.DOTALL)
    return match.group(1) if match else text


def _generate_sql(question: str) -> str:
    """调 LLM 把自然语言问题翻译成 SQL。"""
    prompt = _SQL_WRITER_PROMPT.format(
        max_rows=settings.AI_SQL_MAX_ROWS,
        schema=build_schema_summary(),
    )
    llm = get_chat_model()
    response = llm.invoke(
        [
            {"role": "system", "content": prompt},
            {"role": "user", "content": question},
        ]
    )
    return _strip_code_fences(response.content)


def _execute_readonly(sql: str) -> tuple[list[str], list[tuple], bool]:
    """
    以只读方式执行 SQL，返回 (列名, 行数据, 是否被截断)。

    PostgreSQL 下设置 statement_timeout 兜底慢查询；
    SQLite（本地开发/测试）不支持该参数则跳过。
    """
    max_rows = settings.AI_SQL_MAX_ROWS
    with connection.cursor() as cursor:
        if connection.vendor == "postgresql":
            cursor.execute(
                "SET statement_timeout = %s",
                [int(settings.AI_SQL_TIMEOUT_SECONDS * 1000)],
            )
        cursor.execute(sql)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchmany(max_rows + 1)
    truncated = len(rows) > max_rows
    return columns, rows[:max_rows], truncated


def _format_markdown_table(columns: list[str], rows: list[tuple]) -> str:
    """把查询结果渲染成 Markdown 表格，方便前端直接展示。"""
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = ["| " + " | ".join("" if v is None else str(v) for v in row) + " |" for row in rows]
    return "\n".join([header, separator, *body])


def make_sql_tool(*, user, session):
    """
    构建绑定当前用户/会话的 query_database 工具。

    为什么用工厂函数而不是全局 @tool：工具需要知道"谁在问"
    （写审计日志），LangChain 工具的第一作者签名又不支持自定义上下文字段，
    闭包是最干净的注入方式。
    """

    @tool("query_database")
    def query_database(question: str) -> str:
        """
        查询平台业务数据库。适用于：站点信息、气象观测（温度/湿度/风速/降水/
        雪深/土壤/雪水当量等的日聚合与小时聚合）、水文流量预测结果与预测运行记录。

        参数 question：用完整自然语言描述要查什么（含站点名、时间范围、指标名），
        例如「HXC 站 2026 年 6 月的日均温度和日累计降水」。
        返回：Markdown 表格形式的数据，以及行数/截断说明。
        """
        started = time.perf_counter()
        audit = AiAuditLog(
            user=user, session=session, tool_name="query_database", question=question
        )
        try:
            sql = _generate_sql(question)
            audit.generated_sql = sql

            safe_sql = validate_readonly_sql(sql, max_rows=settings.AI_SQL_MAX_ROWS)
            audit.tables_used = extract_tables(safe_sql)

            columns, rows, truncated = _execute_readonly(safe_sql)
            audit.row_count = len(rows)
            audit.status = AiAuditLog.Status.SUCCESS

            if not rows:
                result = "查询执行成功，但没有符合条件的数据行。"
            else:
                result = _format_markdown_table(columns, rows)
                if truncated:
                    result += f"\n\n（结果超过 {settings.AI_SQL_MAX_ROWS} 行，已截断，请缩小查询范围）"
            return result

        except SqlValidationError as exc:
            # 安全拦截：明确告知，不算系统错误
            audit.status = AiAuditLog.Status.BLOCKED
            audit.detail = str(exc)
            return f"生成的 SQL 未通过安全校验，已拒绝执行：{exc}"
        except Exception as exc:  # LLM 调用失败 / SQL 执行失败 等
            audit.status = AiAuditLog.Status.ERROR
            audit.detail = str(exc)[:2000]
            return f"查询失败：{exc}"
        finally:
            audit.duration_ms = int((time.perf_counter() - started) * 1000)
            audit.save()

    return query_database
