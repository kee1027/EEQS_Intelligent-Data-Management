from django.contrib import admin

from .models import AiAuditLog, AiChatMessage, AiChatSession


class AiChatMessageInline(admin.TabularInline):
    model = AiChatMessage
    extra = 0
    readonly_fields = ("role", "content", "created_at")
    can_delete = False


@admin.register(AiChatSession)
class AiChatSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "created_at", "updated_at")
    list_filter = ("user",)
    search_fields = ("title", "user__username")
    inlines = [AiChatMessageInline]
    ordering = ("-updated_at",)


@admin.register(AiAuditLog)
class AiAuditLogAdmin(admin.ModelAdmin):
    """审计日志：只读查看，不允许在 Admin 里改——审计的价值就在于不可篡改。"""

    list_display = ("created_at", "user", "tool_name", "status", "row_count", "duration_ms")
    list_filter = ("tool_name", "status", "created_at")
    search_fields = ("question", "generated_sql", "user__username")
    readonly_fields = [f.name for f in AiAuditLog._meta.fields]
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
