"""三级鉴权与权限边界测试。"""

from datetime import datetime
from unittest import mock

import pytz
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.roles import ROLE_ADMIN, ROLE_OPERATOR, ROLE_VIEWER, user_role
from data.models import ManualDataRecord

User = get_user_model()

SHANGHAI = pytz.timezone("Asia/Shanghai")
DATA_AT = SHANGHAI.localize(datetime(2026, 9, 19, 8, 0, 0))


class BaseAuthCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            username="t_admin", password="pass12345", email="a@t.cn"
        )
        cls.operator = User.objects.create_user(username="t_operator", password="pass12345")
        cls.viewer = User.objects.create_user(username="t_viewer", password="pass12345")
        operator_group, _ = Group.objects.get_or_create(name="operator")
        cls.operator.groups.add(operator_group)


class RoleResolutionTests(BaseAuthCase):
    def test_roles(self):
        self.assertEqual(user_role(self.admin), ROLE_ADMIN)
        self.assertEqual(user_role(self.operator), ROLE_OPERATOR)
        self.assertEqual(user_role(self.viewer), ROLE_VIEWER)


class AuthApiTests(BaseAuthCase):
    def test_login_success_returns_role(self):
        resp = self.client.post(
            "/api/auth/login/", {"username": "t_operator", "password": "pass12345"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["role"], "operator")
        self.assertIn("operator", resp.data["groups"])

    def test_login_wrong_password_401(self):
        resp = self.client.post(
            "/api/auth/login/", {"username": "t_operator", "password": "wrong"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_requires_login(self):
        self.assertEqual(self.client.get("/api/auth/me/").status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_after_login(self):
        self.client.post(
            "/api/auth/login/", {"username": "t_viewer", "password": "pass12345"}, format="json"
        )
        resp = self.client.get("/api/auth/me/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["role"], "viewer")

    def test_logout(self):
        self.client.post(
            "/api/auth/login/", {"username": "t_viewer", "password": "pass12345"}, format="json"
        )
        self.assertEqual(self.client.post("/api/auth/logout/").status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, status.HTTP_401_UNAUTHORIZED)

    def test_csrf_endpoint_sets_cookie(self):
        resp = self.client.get("/api/auth/csrf/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("csrftoken", resp.cookies)


class ManualDataPermissionTests(BaseAuthCase):
    url = "/api/manual-data/"

    def _payload(self, value="12.5"):
        return {"data_at": DATA_AT.isoformat(), "value": value}

    def test_anonymous_rejected(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_viewer_can_list_but_cannot_create(self):
        self.client.force_authenticate(self.viewer)
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_200_OK)
        resp = self.client.post(self.url, self._payload(), format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_operator_can_create(self):
        self.client.force_authenticate(self.operator)
        resp = self.client.post(self.url, self._payload(), format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ManualDataRecord.objects.count(), 1)

    def test_resubmit_supersedes_and_keeps_trail(self):
        """再次提交：旧记录作废留痕，新记录生效。"""
        self.client.force_authenticate(self.operator)
        first = self.client.post(self.url, self._payload("12.5"), format="json")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)

        second = self.client.post(self.url, self._payload("99.9"), format="json")
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.data["superseded_id"], first.data["id"])

        old = ManualDataRecord.objects.get(id=first.data["id"])
        self.assertTrue(old.is_void)
        self.assertEqual(old.voided_by, self.operator)
        self.assertEqual(str(old.value), "12.500000")  # 原始错误值仍在库中

        new = ManualDataRecord.objects.get(id=second.data["id"])
        self.assertFalse(new.is_void)
        self.assertEqual(str(new.value), "99.900000")

    def test_no_delete_no_update_endpoints(self):
        self.client.force_authenticate(self.admin)
        record = ManualDataRecord.objects.create(
            operator=self.operator, data_at=DATA_AT, value="1.0"
        )
        self.assertEqual(
            self.client.delete(f"{self.url}{record.id}/").status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(
            self.client.patch(f"{self.url}{record.id}/", {"value": "2"}, format="json").status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_void_permission(self):
        record = ManualDataRecord.objects.create(
            operator=self.operator, data_at=DATA_AT, value="1.0"
        )
        # 其他操作员不能作废别人的记录
        other = User.objects.create_user(username="t_op2", password="pass12345")
        other.groups.add(Group.objects.get(name="operator"))
        self.client.force_authenticate(other)
        self.assertEqual(
            self.client.post(f"{self.url}{record.id}/void/").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        # 创建者可以作废
        self.client.force_authenticate(self.operator)
        self.assertEqual(
            self.client.post(f"{self.url}{record.id}/void/").status_code, status.HTTP_200_OK
        )


class HydrologyTriggerPermissionTests(BaseAuthCase):
    url = "/api/hydrology-runs/"

    def _trigger(self, user):
        self.client.force_authenticate(user)
        with mock.patch("data.views.run_hydrology_forecast") as mock_run:
            mock_run.return_value = mock.Mock()
            with mock.patch(
                "data.views.HydrologyForecastRunSerializer",
            ) as mock_serializer:
                mock_serializer.instance = None
                mock_serializer.return_value.data = {"run_id": "mock"}
                return self.client.post(
                    self.url, {"target_date": "2026-09-20"}, format="json"
                )

    def test_viewer_cannot_trigger(self):
        resp = self._trigger(self.viewer)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_operator_can_trigger(self):
        resp = self._trigger(self.operator)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_admin_can_trigger(self):
        resp = self._trigger(self.admin)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
