"""P1 端到端验证：用 Django test Client 请求 modis-snow 瓦片 URL。

运行（项目根目录）：
    venv/Scripts/python.exe ned_vision_plan/p1_verify_tile_url.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

import django

django.setup()

from django.test import Client

TILE_ROOT = PROJECT_ROOT / "data" / "tiles_modis_snow"


def pick_tile() -> Path:
    """挑一个实际生成的瓦片（优先 z8）。"""
    for z in (8, 9, 7, 10, 6, 11):
        for p in sorted((TILE_ROOT / str(z)).rglob("*.png")) if (TILE_ROOT / str(z)).exists() else []:
            return p
    raise SystemExit("tiles_modis_snow 下没有瓦片")


def main() -> None:
    tile = pick_tile()
    rel = tile.relative_to(TILE_ROOT)
    z, x, y_png = rel.parts
    url = f"/api/tiles/modis-snow/{z}/{x}/{y_png}"
    print(f"请求瓦片: {url}")

    client = Client()
    resp = client.get(url)

    assert resp.status_code == 200, f"状态码异常: {resp.status_code}"
    content_type = resp.headers.get("Content-Type", "")
    assert content_type == "image/png", f"Content-Type 异常: {content_type}"
    body = b"".join(resp.streaming_content) if resp.streaming else resp.content
    assert len(body) > 0, "响应体为空"

    print(f"  status      = {resp.status_code}")
    print(f"  content-type= {content_type}")
    print(f"  bytes       = {len(body)}")
    print("PASS: 瓦片 URL 端到端验证通过")


if __name__ == "__main__":
    main()
