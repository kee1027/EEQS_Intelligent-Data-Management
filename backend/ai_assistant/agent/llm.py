"""
LLM 实例工厂。

所有模型配置集中在 settings 的 AI 配置块（环境变量驱动），
这里只做一件事：按配置创建一个 OpenAI 兼容协议的 Chat 模型。

DeepSeek / Kimi / 通义千问等都提供 OpenAI 兼容接口，
因此 langchain-openai 的 ChatOpenAI + base_url 即可通吃，换厂商只改 .env。
"""

from django.conf import settings
from langchain_openai import ChatOpenAI


def get_chat_model(**overrides) -> ChatOpenAI:
    """创建 Chat 模型实例。overrides 可覆盖 temperature 等参数。"""
    params = {
        "model": settings.AI_LLM_MODEL,
        "api_key": settings.AI_LLM_API_KEY,
        "base_url": settings.AI_LLM_BASE_URL,
        "temperature": 0,  # 数据问答场景要确定性，不要创造性
        "timeout": settings.AI_LLM_TIMEOUT_SECONDS,
        "max_retries": 2,
    }
    params.update(overrides)
    return ChatOpenAI(**params)
