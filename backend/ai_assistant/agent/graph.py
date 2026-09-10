"""
Agent 组装：LLM + 工具集 + 会话记忆。

- create_agent 是 LangChain 1.x 的官方推荐入口（旧的 AgentExecutor 已弃用）；
- checkpointer 负责会话记忆：同一 thread_id 的历史消息自动带入。
  当前用 InMemorySaver（进程内存）——重启即丢失，开发期够用；
  如需持久化可换 PostgresSaver（langgraph-checkpoint-postgres），
  代码不变，只改这一个对象的构造。
"""

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from .llm import get_chat_model
from .prompts import SYSTEM_PROMPT

# 全局共享的内存 checkpointer：thread_id 维度隔离会话
_checkpointer = InMemorySaver()


def thread_id_for(*, user, session) -> str:
    """统一 thread_id 生成规则：用户+会话双维度，避免串话。"""
    return f"u{user.pk}-s{session.pk}"


def build_agent(*, user, session):
    """
    按请求构建 Agent。

    每次请求重建的开销很小（只是对象组装），换来的是
    工具闭包能绑定当前 user/session（审计归属正确）。
    """
    from ..tools.sql_tool import make_sql_tool  # 延迟导入，避免循环依赖

    tools = [make_sql_tool(user=user, session=session)]
    return create_agent(
        model=get_chat_model(),
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=_checkpointer,
    )
