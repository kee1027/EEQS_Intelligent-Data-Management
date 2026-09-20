"""
DRF 权限类。

安全边界全部在服务端：前端隐藏按钮只是体验优化，
越权请求一律在这里被 403 拦截。
"""

from rest_framework.permissions import BasePermission

from .roles import ROLE_ADMIN, ROLE_OPERATOR, user_role


class IsOperatorOrAdmin(BasePermission):
    """操作员或管理员：数据录入、手动重跑预测等写操作。"""

    message = "需要操作员或管理员权限。"

    def has_permission(self, request, view):
        return user_role(request.user) in (ROLE_ADMIN, ROLE_OPERATOR)


class IsAdmin(BasePermission):
    """仅管理员。"""

    message = "需要管理员权限。"

    def has_permission(self, request, view):
        return user_role(request.user) == ROLE_ADMIN
