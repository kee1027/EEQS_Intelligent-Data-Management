"""
sql_guard 只读校验器的单元测试。

这些用例就是 Text2SQL 的安全边界：每一个都对应一类真实的攻击或误操作。
改 sql_guard 逻辑前先看这里的预期——测试即规格说明。
"""

from django.test import SimpleTestCase

from ..security.sql_guard import SqlValidationError, extract_tables, validate_readonly_sql


class ValidateReadonlySqlTests(SimpleTestCase):
    """SimpleTestCase：不碰数据库，跑得飞快。"""

    def assert_passes(self, sql):
        return validate_readonly_sql(sql, max_rows=50)

    def assert_blocked(self, sql, keyword=""):
        with self.assertRaises(SqlValidationError) as ctx:
            validate_readonly_sql(sql, max_rows=50)
        if keyword:
            self.assertIn(keyword, str(ctx.exception))

    # ---------- 正常用例 ----------

    def test_plain_select_passes_and_gets_limit(self):
        out = self.assert_passes("SELECT * FROM data_station")
        self.assertIn("LIMIT 50", out.upper())

    def test_join_whitelisted_tables_passes(self):
        sql = (
            "SELECT s.name, d.avg_ta FROM weather_daily_agg d "
            "JOIN data_station s ON d.station_id = s.id WHERE d.day >= '2026-06-01'"
        )
        self.assert_passes(sql)

    def test_existing_limit_is_respected(self):
        out = self.assert_passes("SELECT * FROM data_station LIMIT 5")
        self.assertIn("LIMIT 5", out.upper())

    def test_cte_passes(self):
        self.assert_passes(
            "WITH t AS (SELECT * FROM weather_daily_agg) SELECT * FROM t"
        )

    def test_trailing_semicolon_ok(self):
        self.assert_passes("SELECT * FROM data_station;")

    # ---------- 拦截用例 ----------

    def test_empty_sql_blocked(self):
        self.assert_blocked("   ")

    def test_multi_statement_blocked(self):
        self.assert_blocked(
            "SELECT * FROM data_station; DROP TABLE data_station", "单条"
        )

    def test_delete_blocked(self):
        self.assert_blocked("DELETE FROM data_station WHERE id = 1", "SELECT")

    def test_update_blocked(self):
        self.assert_blocked("UPDATE data_station SET name = 'x'")

    def test_ddl_blocked(self):
        self.assert_blocked("CREATE TABLE evil (id int)")

    def test_non_whitelisted_table_blocked(self):
        self.assert_blocked("SELECT * FROM data_weatherdata LIMIT 1", "不在允许")

    def test_subquery_hiding_bad_table_blocked(self):
        self.assert_blocked(
            "SELECT * FROM data_station WHERE id IN (SELECT station_id FROM data_weatherdata)",
            "不在允许",
        )

    def test_cte_hiding_bad_table_blocked(self):
        self.assert_blocked(
            "WITH t AS (SELECT * FROM data_weatherdata) SELECT * FROM t", "不在允许"
        )

    def test_pg_sleep_blocked(self):
        # sqlglot 把未注册函数解析为 Anonymous，函数名在 .name —— 防回归用例
        self.assert_blocked("SELECT pg_sleep(10)", "pg_sleep")

    def test_set_config_blocked(self):
        self.assert_blocked("SELECT set_config('statement_timeout', '0', false)")

    def test_file_read_function_blocked(self):
        self.assert_blocked("SELECT pg_read_file('/etc/passwd')")

    def test_select_into_blocked(self):
        self.assert_blocked("SELECT * INTO backup_tbl FROM data_station", "INTO")

    def test_for_update_blocked(self):
        # sqlglot 把 FOR UPDATE 存在 args['locks'] —— 防回归用例
        self.assert_blocked("SELECT * FROM data_station FOR UPDATE", "锁")

    def test_for_share_blocked(self):
        self.assert_blocked("SELECT * FROM data_station FOR SHARE", "锁")

    def test_garbage_sql_blocked(self):
        self.assert_blocked("SELEC * FORM data_station")


class ExtractTablesTests(SimpleTestCase):
    def test_extract_from_join(self):
        tables = extract_tables(
            "SELECT s.name FROM weather_daily_agg d JOIN data_station s ON d.station_id = s.id"
        )
        self.assertEqual(tables, ["data_station", "weather_daily_agg"])

    def test_bad_sql_returns_empty(self):
        self.assertEqual(extract_tables("not sql at all :::"), [])
