"""
编排层：HTTP 视图 与 LangChain Agent 之间的胶水。

职责：
1. 用户消息落库（AiChatMessage）
2. 驱动 Agent 流式执行，把 LangGraph 的消息流翻译成稳定的业务事件
   （token / tool_start / tool_end / final / error），视图层只管 SSE 格式化
3. AI 最终回答落库

事件协议（SSE data 字段的 JSON 结构）：
  {"type": "meta",       "session_id": "...", "title": "..."}
  {"type": "token",      "content": "..."}            # AI 逐 token 输出
  {"type": "tool_start", "tool": "query_database"}
  {"type": "tool_end",   "tool": "query_database", "preview": "前 200 字..."}
  {"type": "final",      "content": "完整回答"}
  {"type": "error",      "message": "..."}
"""

import json

from langchain_core.messages import AIMessageChunk, ToolMessage

from .agent.graph import build_agent, thread_id_for
from .models import AiChatMessage, AiChatSession


def get_or_create_session(*, user, session_id=None) -> AiChatSession:
    if session_id:
        session = AiChatSession.objects.filter(id=session_id, user=user).first()
        if session is not None:
            return session
    return AiChatSession.objects.create(user=user)


def stream_chat(*, user, session: AiChatSession, message: str):
    """生成器：执行一轮问答，逐事件 yield dict。"""
    AiChatMessage.objects.create(
        session=session, role=AiChatMessage.Role.USER, content=message
    )
    if not session.title:
        session.title = message[:50]
        session.save(update_fields=["title", "updated_at"])

    yield {"type": "meta", "session_id": str(session.id), "title": session.title}

    agent = build_agent(user=user, session=session)
    config = {"configurable": {"thread_id": thread_id_for(user=user, session=session)}}

    final_text_parts: list[str] = []
    try:
        for chunk, _metadata in agent.stream(
            {"messages": [{"role": "user", "content": message}]},
            config=config,
            stream_mode="messages",
        ):
            if isinstance(chunk, AIMessageChunk):
                # 先判工具调用：携带 tool_call_chunks 的 AIMessageChunk 其 content
                # 通常也是 str 类型（空串），若先判 token 分支会把工具事件吞掉
                for tc in chunk.tool_call_chunks or []:
                    if tc.get("name"):
                        yield {"type": "tool_start", "tool": tc["name"]}
                if isinstance(chunk.content, str) and chunk.content:
                    final_text_parts.append(chunk.content)
                    yield {"type": "token", "content": chunk.content}
            elif isinstance(chunk, ToolMessage):
                preview = chunk.content[:200] if isinstance(chunk.content, str) else ""
                yield {"type": "tool_end", "tool": chunk.name or "", "preview": preview}
    except Exception as exc:
        yield {"type": "error", "message": f"AI 服务暂时不可用：{exc}"}
        return

    final_text = "".join(final_text_parts).strip()
    if final_text:
        AiChatMessage.objects.create(
            session=session, role=AiChatMessage.Role.ASSISTANT, content=final_text
        )
    yield {"type": "final", "content": final_text}


def format_sse(event: dict) -> str:
    """把事件 dict 格式化为一条 SSE 帧。"""
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
