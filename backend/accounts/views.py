"""
登录鉴权 API。

- POST /api/auth/login/   用户名+密码登录，建立 Session（匿名访问，无需 CSRF）
- POST /api/auth/logout/  注销当前 Session
- GET  /api/auth/me/      当前用户信息（用户名/角色/组），前端据此控制按钮显隐
- GET  /api/auth/csrf/    仅用于下发 csrftoken Cookie（Session 认证的写请求需要
                          X-CSRFToken 请求头，前端启动时先调一次本接口）

认证体系：SessionAuthentication（前端 SPA）+ BasicAuthentication（curl/脚本调试），
不提供注册接口——账号只能由管理员在 Django 后台创建。
"""

from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .roles import user_role


def _user_payload(user) -> dict:
    return {
        "username": user.username,
        "role": user_role(user),
        "groups": sorted(user.groups.values_list("name", flat=True)),
        "is_superuser": user.is_superuser,
    }


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    username = str(request.data.get("username") or "").strip()
    password = str(request.data.get("password") or "")
    if not username or not password:
        return Response(
            {"detail": "用户名和密码不能为空"}, status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response(
            {"detail": "用户名或密码错误"}, status=status.HTTP_401_UNAUTHORIZED
        )
    if not user.is_active:
        return Response(
            {"detail": "账户已被停用，请联系管理员"}, status=status.HTTP_403_FORBIDDEN
        )

    login(request, user)
    return Response(_user_payload(user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({"detail": "已注销"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    return Response(_user_payload(request.user))


@ensure_csrf_cookie
@api_view(["GET"])
@permission_classes([AllowAny])
def csrf_view(request):
    return Response({"detail": "CSRF cookie 已下发"})
