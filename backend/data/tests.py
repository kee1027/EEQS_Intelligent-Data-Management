from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status

from .models import HydrologyForecastRun, ManualDataRecord


class TileEndpointTests(TestCase):
    def setUp(self):
        self.tmpdir = TemporaryDirectory()
        self.dataset_root = Path(self.tmpdir.name)
        tile_dir = self.dataset_root / "1" / "1"
        tile_dir.mkdir(parents=True, exist_ok=True)
        self.tile_file = tile_dir / "1.png"
        self.tile_file.write_bytes(b"png-mock-bytes")

    def tearDown(self):
        self.tmpdir.cleanup()

    @override_settings(
        TILE_DATASETS={},
    )
    def test_unknown_dataset_returns_400(self):
        response = self.client.get("/api/tiles/demo/1/1/1.png")
        self.assertEqual(response.status_code, 400)

    @override_settings(
        TILE_DATASETS={"demo": ""},
    )
    def test_bad_dataset_config_returns_400(self):
        response = self.client.get("/api/tiles/demo/1/1/1.png")
        self.assertEqual(response.status_code, 400)

    @override_settings(
        TILE_DATASETS={"demo": ""},
    )
    def test_invalid_extension_returns_400(self):
        response = self.client.get("/api/tiles/demo/1/1/1.exe")
        self.assertEqual(response.status_code, 400)

    @override_settings(
        TILE_DATASETS={"demo": ""},
    )
    def test_invalid_xyz_range_returns_400(self):
        response = self.client.get("/api/tiles/demo/1/2/1.png")
        self.assertEqual(response.status_code, 400)

    @override_settings(
        TILE_DATASETS={"demo": ""},
    )
    def test_invalid_y_ext_returns_400(self):
        response = self.client.get("/api/tiles/demo/1/1/not-valid")
        self.assertEqual(response.status_code, 400)

    def _settings_with_demo_dataset(self):
        return override_settings(
            TILE_DATASETS={"demo": str(self.dataset_root)},
            TILE_CACHE_CONTROL="public, max-age=120",
            TILE_MIN_ZOOM=0,
            TILE_MAX_ZOOM=22,
            TILE_ALLOWED_EXTENSIONS=["png", "jpg", "jpeg", "webp", "pbf"],
        )

    def test_tile_found_returns_200_and_headers(self):
        with self._settings_with_demo_dataset():
            response = self.client.get("/api/tiles/demo/1/1/1.png")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "image/png")
            self.assertIn("ETag", response)
            self.assertIn("Last-Modified", response)
            self.assertEqual(response["Cache-Control"], "public, max-age=120")

    def test_tile_missing_returns_404(self):
        with self._settings_with_demo_dataset():
            response = self.client.get("/api/tiles/demo/1/1/0.png")
            self.assertEqual(response.status_code, 404)

    def test_if_none_match_returns_304(self):
        with self._settings_with_demo_dataset():
            first = self.client.get("/api/tiles/demo/1/1/1.png")
            etag = first["ETag"]
            second = self.client.get(
                "/api/tiles/demo/1/1/1.png",
                HTTP_IF_NONE_MATCH=etag,
            )
            self.assertEqual(second.status_code, 304)


class ManualDataRecordApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="operator_a", password="test-pass-123")
        self.other_user = get_user_model().objects.create_user(username="operator_b", password="test-pass-123")
        self.url = "/api/manual-data/"
        self.payload = {
            "data_at": "2026-04-22T19:00:00+08:00",
            "value": "12.340000",
        }

    def test_requires_login(self):
        response = self.client.post(self.url, data=self.payload, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_record_uses_logged_in_operator_and_auto_operated_at(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data=self.payload, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ManualDataRecord.objects.count(), 1)

        record = ManualDataRecord.objects.get()
        self.assertEqual(record.operator, self.user)
        self.assertTrue(timezone.is_aware(record.operated_at))
        self.assertEqual(str(record.value), "12.340000")

    def test_duplicate_operator_and_data_at_returns_409(self):
        self.client.force_login(self.user)
        self.client.post(self.url, data=self.payload, content_type="application/json")
        second_response = self.client.post(self.url, data=self.payload, content_type="application/json")

        self.assertEqual(second_response.status_code, status.HTTP_409_CONFLICT)

    def test_void_record_success(self):
        self.client.force_login(self.user)
        create_resp = self.client.post(self.url, data=self.payload, content_type="application/json")
        record_id = create_resp.json()["id"]

        void_resp = self.client.post(f"/api/manual-data/{record_id}/void/")
        self.assertEqual(void_resp.status_code, status.HTTP_200_OK)

        record = ManualDataRecord.objects.get(id=record_id)
        self.assertTrue(record.is_void)
        self.assertEqual(record.voided_by, self.user)
        self.assertIsNotNone(record.voided_at)

    def test_void_requires_record_owner_or_admin(self):
        self.client.force_login(self.user)
        create_resp = self.client.post(self.url, data=self.payload, content_type="application/json")
        record_id = create_resp.json()["id"]

        self.client.force_login(self.other_user)
        void_resp = self.client.post(f"/api/manual-data/{record_id}/void/")
        self.assertEqual(void_resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_void_then_resubmit_same_data_at_succeeds(self):
        self.client.force_login(self.user)
        create_resp = self.client.post(self.url, data=self.payload, content_type="application/json")
        record_id = create_resp.json()["id"]
        self.client.post(f"/api/manual-data/{record_id}/void/")

        second_create = self.client.post(self.url, data=self.payload, content_type="application/json")
        self.assertEqual(second_create.status_code, status.HTTP_201_CREATED)


class HydrologyRunApiTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin_user",
            password="test-pass-123",
            is_staff=True,
        )
        self.normal_user = get_user_model().objects.create_user(
            username="normal_user",
            password="test-pass-123",
        )
        self.url = "/api/hydrology-runs/"
        self.payload = {"target_date": "2026-04-24"}

    def test_manual_run_requires_admin(self):
        self.client.force_login(self.normal_user)
        response = self.client.post(self.url, data=self.payload, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("data.views.run_hydrology_forecast")
    def test_manual_run_success_for_admin(self, mock_run_hydrology_forecast):
        run = HydrologyForecastRun.objects.create(
            run_id="hydro-20260423-001",
            target_date=timezone.datetime.strptime("2026-04-24", "%Y-%m-%d").date(),
            source="manual_api",
            status=HydrologyForecastRun.Status.SUCCESS,
            model_name="lstm",
            model_version="v1",
            retry_count=0,
            record_count=3,
            triggered_by=self.admin_user,
            finished_at=timezone.now(),
        )
        mock_run_hydrology_forecast.return_value = run

        self.client.force_login(self.admin_user)
        response = self.client.post(self.url, data=self.payload, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["run_id"], "hydro-20260423-001")
