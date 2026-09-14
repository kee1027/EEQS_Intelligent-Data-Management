"""
AI 问答 API 视图。

- POST /api/ai/chat/           发起问答，SSE 流式返回（复用平台 BasicAuth/Session 认证）
- GET  /api/ai/sessions/       当前用户的会话列表
- GET  /api/ai/sessions/<id>/  某会话的消息历史

SSE（Server-Sent Events）说明：响应 Content-Type 为 text/event-stream，
每帧格式 `data: {json}\\n\\n`，事件结构见 services.py 顶部注释。
curl 测试：curl -N -u user:pass -X POST ... -d '{"message":"..."}'
"""

from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import AiChatSession
from .serializers import AiChatSessionDetailSerializer, AiChatSessionSerializer
from .services import format_sse, get_or_create_session, stream_chat


@api_view(["POST"])
def chat_view(request):
    message = str(request.data.get("message") or "").strip()
    if not message:
        return Response({"detail": "message 不能为空"}, status=status.HTTP_400_BAD_REQUEST)
    if len(message) > 2000:
        return Response(
            {"detail": "message 超过 2000 字上限"}, status=status.HTTP_400_BAD_REQUEST
        )

    session = get_or_create_session(user=request.user, session_id=request.data.get("session_id"))

    def event_stream():
        for event in stream_chat(user=request.user, session=session, message=message):
            yield format_sse(event)

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    # 禁用反向代理缓冲（nginx 默认会缓冲整个响应，流式就失效了）
    response["X-Accel-Buffering"] = "no"
    return response


@api_view(["GET"])
def session_list_view(request):
    sessions = AiChatSession.objects.filter(user=request.user)
    return Response(AiChatSessionSerializer(sessions, many=True).data)


@api_view(["GET"])
def session_detail_view(request, session_id):
    session = AiChatSession.objects.filter(id=session_id, user=request.user).first()
    if session is None:
        return Response({"detail": "会话不存在"}, status=status.HTTP_404_NOT_FOUND)
    return Response(AiChatSessionDetailSerializer(session).data)
