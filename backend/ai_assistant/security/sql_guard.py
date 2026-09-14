"""
SQL 只读校验器（Text2SQL 安全链路的核心）。

设计原则：**权限判断发生在代码里，不在提示词里。**
LLM 生成的 SQL 一律视为不可信输入，逐条过以下检查：

1. 必须恰好是一条语句（拒绝多语句堆叠，如 `SELECT 1; DROP TABLE x`）
2. 必须是纯 SELECT（拒绝 INSERT/UPDATE/DELETE/DDL/COPY/CALL 等一切写操作）
3. 不允许 SELECT ... INTO（会建表）和 SELECT ... FOR UPDATE（会加行锁）
4. 引用的每张表都必须在表白名单内（含子查询、JOIN、CTE 里出现的表）
5. 不允许调用高危函数（pg_sleep、set_config、dblink、文件读写等）
6. 没有 LIMIT 时自动补上（防止全表扫描打爆内存）

为什么不直接用正则：SQL 语法太自由（注释、大小写、引号、嵌套子查询），
正则一定有绕过方式；AST 级解析（sqlglot）才能结构化地理解语句。
"""

import sqlglot
from sqlglot import exp


class SqlValidationError(ValueError):
    """SQL 未通过只读校验。message 面向用户可读，会写进审计日志。"""


# Text2SQL 允许查询的真实数据库表名（Django 默认表名或自定义 db_table）。
# 刻意不包含 data_weatherdata（90+ 列原始表）：列太多 LLM 容易选错，
# 行太多查询慢；业务查询走聚合表即可覆盖。
ALLOWED_TABLES = frozenset(
    {
        "data_station",
        "weather_daily_agg",
        "weather_hourly_agg",
        "data_hydrologyforecastrun",
        "data_hydrologyforecastdaily",
    }
)

# PostgreSQL 高危函数黑名单（信息收集 / 文件读写 / 延时攻击 / 配置篡改）
DENIED_FUNCTIONS = frozenset(
    {
        "pg_sleep",
        "set_config",
        "current_setting",
        "dblink",
        "dblink_exec",
        "lo_import",
        "lo_export",
        "lo_get",
        "lo_put",
        "pg_read_file",
        "pg_read_binary_file",
        "pg_ls_dir",
        "pg_stat_file",
        "pg_reload_conf",
        "pg_terminate_backend",
        "pg_cancel_backend",
        "pg_notify",
        "txid_current",
        "query_to_xml",
    }
)


def validate_readonly_sql(sql: str, *, max_rows: int) -> str:
    """
    校验 SQL 是否满足只读约束。

    通过则返回（可能被改写的）SQL——比如自动补了 LIMIT；
    不通过抛 SqlValidationError，消息可直接展示/落日志。
    """
    if not sql or not sql.strip():
        raise SqlValidationError("SQL 为空")

    try:
        statements = [s for s in sqlglot.parse(sql, read="postgres") if s is not None]
    except sqlglot.errors.ParseError as exc:
        raise SqlValidationError(f"SQL 语法无法解析: {exc}") from exc

    # 检查 1：单语句
    if len(statements) == 0:
        raise SqlValidationError("SQL 为空")
    if len(statements) > 1:
        raise SqlValidationError("只允许执行单条 SQL 语句")

    ast = statements[0]

    # 检查 2：纯 SELECT（WITH ... SELECT 也是 Select 节点）
    if not isinstance(ast, exp.Select):
        raise SqlValidationError(
            f"只允许 SELECT 查询，检测到 {ast.key.upper()} 类型语句"
        )

    # 检查 3：禁 INTO / FOR UPDATE 等副作用子句
    if ast.args.get("into") is not None:
        raise SqlValidationError("不允许 SELECT ... INTO（会在库中建表）")
    if ast.args.get("locks"):
        raise SqlValidationError("不允许 SELECT ... FOR UPDATE / FOR SHARE（会加锁）")

    # 检查 4：表白名单（find_all 会覆盖子查询、JOIN、CTE 内的所有表引用；
    # 但 WITH 定义的 CTE 名只是临时别名，不是真实表，需排除）
    cte_names = {cte.alias_or_name.lower() for cte in ast.find_all(exp.CTE)}
    for table in ast.find_all(exp.Table):
        table_name = table.name.lower()
        if table_name in cte_names:
            continue
        if table_name not in ALLOWED_TABLES:
            raise SqlValidationError(
                f"表 {table.name!r} 不在允许查询的范围内"
            )

    # 检查 5：函数黑名单
    # 注意：sqlglot 对未注册的函数会解析成 exp.Anonymous，
    # 此时 sql_name() 返回类名 "ANONYMOUS"，真实函数名在 .name 里，两个都要查。
    for func in ast.find_all(exp.Func):
        candidates = {func.sql_name().lower()}
        if isinstance(func, exp.Anonymous) and func.name:
            candidates.add(func.name.lower())
        if candidates & DENIED_FUNCTIONS:
            raise SqlValidationError(f"不允许调用函数 {sorted(candidates & DENIED_FUNCTIONS)[0]}()")

    # 检查 6：自动补 LIMIT
    if ast.args.get("limit") is None:
        ast.set("limit", exp.Limit(expression=exp.Literal.number(str(max_rows))))

    return ast.sql(dialect="postgres")


def extract_tables(sql: str) -> list[str]:
    """从（已通过校验的）SQL 中提取实际访问的表名，用于审计日志。"""
    try:
        statements = [s for s in sqlglot.parse(sql, read="postgres") if s is not None]
    except sqlglot.errors.ParseError:
        return []
    if not statements:
        return []
    return sorted({t.name.lower() for t in statements[0].find_all(exp.Table)})
