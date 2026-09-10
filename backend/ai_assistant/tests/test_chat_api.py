"""
/api/ai/chat/ 接口与编排层的测试。

Agent 用假的替身（FakeAgent）模拟 LangGraph 的 stream_mode="messages" 输出，
从而离线验证：SSE 事件序列、消息落库、会话归属。
"""

import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from langchain_core.messages import AIMessageChunk, ToolMessage

from ..models import AiChatMessage, AiChatSession
from ..services import stream_chat


class _FakeAgent:
    """模拟一次「调工具 → 回答」的完整消息流。"""

    def stream(self, _input, config=None, stream_mode=None):
        yield AIMessageChunk(content="", tool_call_chunks=[{"name": "query_database"}]), {}
        yield ToolMessage(
            content="| name |\n| --- |\n| HXC |", name="query_database", tool_call_id="call-1"
        ), {}
        for text in ["HXC 站", "最近的温度", "如下表所示。"]:
            yield AIMessageChunk(content=text), {}


class _BrokenAgent:
    def stream(self, _input, config=None, stream_mode=None):
        raise RuntimeError("LLM API 连接超时")
        yield  # pragma: no cover


class StreamChatTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="chatter", password="test-pass-123"
        )

    @patch("ai_assistant.services.build_agent", return_value=_FakeAgent())
    def test_full_event_sequence_and_persistence(self, _mock):
        session = AiChatSession.objects.create(user=self.user)
        events = list(
            stream_chat(user=self.user, session=session, message="HXC 站最近温度如何？")
        )

        types = [e["type"] for e in events]
        self.assertEqual(types[0], "meta")
        self.assertEqual(types[-1], "final")
        self.assertIn("tool_start", types)
        self.assertIn("tool_end", types)

        final = events[-1]["content"]
        self.assertEqual(final, "HXC 站最近的温度如下表所示。")

        # 一问一答都已落库，会话标题取首条消息
        msgs = list(session.messages.order_by("created_at"))
        self.assertEqual([m.role for m in msgs], ["user", "assistant"])
        self.assertEqual(msgs[1].content, final)
        session.refresh_from_db()
        self.assertEqual(session.title, "HXC 站最近温度如何？")

    @patch("ai_assistant.services.build_agent", return_value=_BrokenAgent())
    def test_agent_failure_yields_error_event(self, _mock):
        session = AiChatSession.objects.create(user=self.user)
        events = list(stream_chat(user=self.user, session=session, message="你好"))
        self.assertEqual(events[-1]["type"], "error")
        self.assertIn("暂时不可用", events[-1]["message"])
        # 失败时只有用户消息落库，不留下半吊子的 AI 回答
        self.assertEqual(session.messages.filter(role="assistant").count(), 0)


class ChatApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="api_user", password="test-pass-123"
        )
        self.url = "/api/ai/chat/"

    def test_requires_authentication(self):
        response = self.client.post(self.url, {"message": "你好"})
        self.assertIn(response.status_code, (401, 403))

    def test_empty_message_returns_400(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {"message": "  "})
        self.assertEqual(response.status_code, 400)

    @patch("ai_assistant.services.build_agent", return_value=_FakeAgent())
    def test_sse_stream_response(self, _mock):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {"message": "HXC 站最近温度如何？"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/event-stream")
        self.assertEqual(response["X-Accel-Buffering"], "no")

        body = b"".join(response.streaming_content).decode("utf-8")
        frames = [
            json.loads(line[5:])
            for line in body.splitlines()
            if line.startswith("data: ")
        ]
        types = [f["type"] for f in frames]
        self.assertEqual(types[0], "meta")
        self.assertEqual(types[-1], "final")
        self.assertIn("session_id", frames[0])

    @patch("ai_assistant.services.build_agent", return_value=_FakeAgent())
    def test_existing_session_is_reused(self, _mock):
        self.client.force_login(self.user)
        session = AiChatSession.objects.create(user=self.user, title="旧会话")
        response = self.client.post(
            self.url, {"message": "继续聊", "session_id": str(session.id)}
        )
        b"".join(response.streaming_content)
        self.assertEqual(AiChatSession.objects.count(), 1)

    @patch("ai_assistant.services.build_agent", return_value=_FakeAgent())
    def test_cannot_use_others_session(self, _mock):
        other = get_user_model().objects.create_user(username="other", password="x")
        others_session = AiChatSession.objects.create(user=other, title="别人的")
        self.client.force_login(self.user)
        response = self.client.post(
            self.url, {"message": "hi", "session_id": str(others_session.id)}
        )
        b"".join(response.streaming_content)
        # 拿不到别人的会话 → 新建一个属于自己的
        my_sessions = AiChatSession.objects.filter(user=self.user)
        self.assertEqual(my_sessions.count(), 1)
        self.assertNotEqual(my_sessions.first().id, others_session.id)

    def test_session_history_endpoint(self):
        self.client.force_login(self.user)
        session = AiChatSession.objects.create(user=self.user, title="历史")
        AiChatMessage.objects.create(session=session, role="user", content="问题1")
        AiChatMessage.objects.create(session=session, role="assistant", content="回答1")

        response = self.client.get(f"/api/ai/sessions/{session.id}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["messages"]), 2)

        # 别人的会话不可见
        other = get_user_model().objects.create_user(username="other2", password="x")
        others = AiChatSession.objects.create(user=other)
        response = self.client.get(f"/api/ai/sessions/{others.id}/")
        self.assertEqual(response.status_code, 404)
