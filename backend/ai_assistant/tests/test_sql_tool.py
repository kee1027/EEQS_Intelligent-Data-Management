"""
query_database 工具的单元测试。

关键工程实践：**测试不依赖外部付费服务**。
LLM 用一个假的替身（FakeLlm）返回预设 SQL，从而可以离线、确定性地
测试「生成 → 校验 → 执行 → 格式化 → 审计」的完整链路。
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.test import TestCase

from data.models import (
    HydrologyForecastDaily,
    HydrologyForecastRun,
    Station,
    WeatherDailyAgg,
)

from ..models import AiAuditLog, AiChatSession
from ..tools.sql_tool import make_sql_tool

SH = ZoneInfo("Asia/Shanghai")


class _FakeResponse:
    def __init__(self, content):
        self.content = content


class _FakeLlm:
    """模拟 LLM：按预设队列依次返回 SQL，忽略 prompt 内容。"""

    def __init__(self, outputs):
        self._outputs = list(outputs)

    def invoke(self, _messages):
        return _FakeResponse(self._outputs.pop(0))


class QueryDatabaseToolTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester", password="test-pass-123"
        )
        self.session = AiChatSession.objects.create(user=self.user, title="测试会话")

        self.station = Station.objects.create(name="HXC")
        for day in (1, 2, 3):
            WeatherDailyAgg.objects.create(
                day=datetime(2026, 6, day, tzinfo=SH),
                station=self.station,
                avg_ta=10.0 + day,
                total_rainsnow=100.0 * day,
                record_count=48,
            )
        run = HydrologyForecastRun.objects.create(
            run_id="hydro-test-001",
            target_date=datetime(2026, 6, 3, tzinfo=SH).date(),
            status=HydrologyForecastRun.Status.SUCCESS,
            model_name="mock-scale-7day",
            model_version="v1",
            record_count=7,
        )
        HydrologyForecastDaily.objects.create(
            run=run,
            station=self.station,
            target_date=datetime(2026, 6, 4, tzinfo=SH).date(),
            flow_avg=Decimal("1234.567"),
            model_name="mock-scale-7day",
            model_version="v1",
        )

    def _make_tool(self, fake_llm):
        return make_sql_tool(user=self.user, session=self.session)

    @patch("ai_assistant.tools.sql_tool.get_chat_model")
    def test_valid_sql_returns_markdown_table(self, mock_get_model):
        mock_get_model.return_value = _FakeLlm(
            ["SELECT day, avg_ta FROM weather_daily_agg ORDER BY day"]
        )
        result = self._make_tool(mock_get_model).invoke({"question": "HXC 6 月初温度"})

        self.assertIn("| day | avg_ta |", result)
        self.assertIn("11.0", result)
        # 审计日志：成功、记录了 SQL 和涉及的表
        audit = AiAuditLog.objects.get()
        self.assertEqual(audit.status, AiAuditLog.Status.SUCCESS)
        self.assertEqual(audit.tables_used, ["weather_daily_agg"])
        self.assertEqual(audit.row_count, 3)
        self.assertEqual(audit.user, self.user)

    @patch("ai_assistant.tools.sql_tool.get_chat_model")
    def test_dangerous_sql_is_blocked_not_executed(self, mock_get_model):
        mock_get_model.return_value = _FakeLlm(["DELETE FROM data_station"])
        result = self._make_tool(mock_get_model).invoke({"question": "删掉所有站点"})

        self.assertIn("未通过安全校验", result)
        self.assertEqual(Station.objects.count(), 1)  # 数据安然无恙
        self.assertEqual(AiAuditLog.objects.get().status, AiAuditLog.Status.BLOCKED)

    @patch("ai_assistant.tools.sql_tool.get_chat_model")
    def test_sql_wrapped_in_code_fence_is_unwrapped(self, mock_get_model):
        mock_get_model.return_value = _FakeLlm(
            ["```sql\nSELECT name FROM data_station\n```"]
        )
        result = self._make_tool(mock_get_model).invoke({"question": "有哪些站点"})
        self.assertIn("HXC", result)

    @patch("ai_assistant.tools.sql_tool.get_chat_model")
    def test_sql_error_returns_readable_message(self, mock_get_model):
        mock_get_model.return_value = _FakeLlm(
            ["SELECT no_such_column FROM data_station"]
        )
        result = self._make_tool(mock_get_model).invoke({"question": "随便查"})
        self.assertIn("查询失败", result)
        self.assertEqual(AiAuditLog.objects.get().status, AiAuditLog.Status.ERROR)

    @patch("ai_assistant.tools.sql_tool.get_chat_model")
    def test_empty_result_explained(self, mock_get_model):
        mock_get_model.return_value = _FakeLlm(
            ["SELECT * FROM weather_daily_agg WHERE day >= '2030-01-01'"]
        )
        result = self._make_tool(mock_get_model).invoke({"question": "2030 年的数据"})
        self.assertIn("没有符合条件的数据行", result)

    @patch("ai_assistant.tools.sql_tool.get_chat_model")
    def test_forecast_table_query(self, mock_get_model):
        mock_get_model.return_value = _FakeLlm(
            [
                "SELECT target_date, flow_avg FROM data_hydrologyforecastdaily "
                "WHERE model_name = 'mock-scale-7day'"
            ]
        )
        result = self._make_tool(mock_get_model).invoke({"question": "HXC 的预测流量"})
        self.assertIn("1234.567", result)
