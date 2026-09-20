"""
三级角色模型。

角色判定规则（优先级从高到低）：
1. 超级管理员 admin    —— is_superuser 的账户（Django 后台管理、管用户与组）
2. 操作员    operator —— 属于 operator 组（数据录入、手动重跑模型预测）
3. 用户      viewer   —— 其余已登录账户（只读查阅）

账号只能由管理员在 Django 后台创建并分配组，系统不提供注册入口。
"""

OPERATOR_GROUP = "operator"
VIEWER_GROUP = "viewer"

ROLE_ADMIN = "admin"
ROLE_OPERATOR = "operator"
ROLE_VIEWER = "viewer"
ROLE_ANONYMOUS = "anonymous"


def user_role(user) -> str:
    """返回用户角色标识：admin / operator / viewer / anonymous。"""
    if not user or not user.is_authenticated:
        return ROLE_ANONYMOUS
    if user.is_superuser:
        return ROLE_ADMIN
    if user.groups.filter(name=OPERATOR_GROUP).exists():
        return ROLE_OPERATOR
    return ROLE_VIEWER
