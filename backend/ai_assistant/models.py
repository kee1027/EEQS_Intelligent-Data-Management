"""
ai_assistant 数据模型。

三张表各司其职：
- AiChatSession：一次对话会话（对应前端一个聊天窗口）
- AiChatMessage：会话内的单条消息（用户提问 / AI 回答），用于历史回放
- AiAuditLog：AI 行为的审计日志（谁、问了什么、生成了什么 SQL、查了哪些表、
  耗时多少）。与消息分开存——消息是给用户看的，日志是给运维/安全看的，
  两者保留周期和访问权限通常不同。
"""

import uuid

from django.conf import settings
from django.db import models


class AiChatSession(models.Model):
    """对话会话。thread_id 与 LangGraph checkpoint 的 thread_id 对应。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_chat_sessions",
        verbose_name="所属用户",
    )
    title = models.CharField(max_length=200, blank=True, verbose_name="会话标题")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="最后活跃时间")

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user} · {self.title or self.id}"


class AiChatMessage(models.Model):
    """单条聊天消息。"""

    class Role(models.TextChoices):
        USER = "user", "用户"
        ASSISTANT = "assistant", "AI 助手"

    session = models.ForeignKey(
        AiChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="所属会话",
    )
    role = models.CharField(max_length=16, choices=Role.choices, verbose_name="角色")
    content = models.TextField(verbose_name="内容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.role}] {self.content[:30]}"


class AiAuditLog(models.Model):
    """
    AI 行为审计日志。

    每一次工具调用（Text2SQL / 知识库检索 / 统计外推）都落一条：
    出了问题能回放「AI 到底干了什么」，这是 LLM 应用上线的硬性要求。
    """

    class Status(models.TextChoices):
        SUCCESS = "success", "成功"
        BLOCKED = "blocked", "被安全策略拦截"
        ERROR = "error", "执行出错"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_audit_logs",
        verbose_name="操作人",
    )
    session = models.ForeignKey(
        AiChatSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name="所属会话",
    )
    tool_name = models.CharField(max_length=50, verbose_name="工具名称")
    question = models.TextField(verbose_name="用户问题")
    generated_sql = models.TextField(blank=True, verbose_name="生成的 SQL")
    tables_used = models.JSONField(default=list, blank=True, verbose_name="涉及的表")
    row_count = models.IntegerField(null=True, blank=True, verbose_name="返回行数")
    duration_ms = models.IntegerField(null=True, blank=True, verbose_name="耗时(毫秒)")
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.SUCCESS, verbose_name="状态"
    )
    detail = models.TextField(blank=True, verbose_name="附加信息/错误原因")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.tool_name} · {self.status} · {self.created_at:%Y-%m-%d %H:%M}"
