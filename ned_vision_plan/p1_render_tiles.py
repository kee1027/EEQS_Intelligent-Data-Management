"""P1 演示：MODIS MOD10A1 HDF4 全流程渲染管线。

读取 -> 拼接 -> 重投影(EPSG:3857) -> 裁剪(阿勒泰) -> 离散配色 -> 切 XYZ 瓦片

运行（项目根目录）：
    venv/Scripts/python.exe ned_vision_plan/p1_render_tiles.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from data.raster_pipeline.readers import read_modis_hdf_to_xarray
from data.raster_pipeline.render import render_to_geotiff, tile_geotiff

RAW_DIR = PROJECT_ROOT / "data" / "raster_data" / "raw" / "MOD10A1" / "2026-01-05"
TMP_DIR = PROJECT_ROOT / "data" / "raster_data" / "tmp"
TILE_ROOT = PROJECT_ROOT / "data" / "tiles_modis_snow"

# 阿勒泰区域裁剪框（经纬度）
CLIP_BOUNDS_LONLAT = (85.5, 45.0, 91.1, 49.2)
MIN_ZOOM, MAX_ZOOM = 6, 11


def main() -> None:
    hdf_files = sorted(RAW_DIR.glob("*.hdf"))
    if not hdf_files:
        raise SystemExit(f"未找到 HDF 文件: {RAW_DIR}")
    print(f"[1/4] 读取 {len(hdf_files)} 个 HDF 文件 ...")
    arrays = [read_modis_hdf_to_xarray(str(p)) for p in hdf_files]
    for p in hdf_files:
        print(f"      - {p.name}")

    tif_path = TMP_DIR / "modis_snow_2026-01-05_altay_3857.tif"
    print(f"[2/4] 合并 + 重投影(EPSG:3857) + 裁剪 {CLIP_BOUNDS_LONLAT} -> {tif_path.name}")
    render_to_geotiff(arrays, tif_path, clip_bounds_lonlat=CLIP_BOUNDS_LONLAT)

    print(f"[3/4] 切 XYZ 瓦片 z{MIN_ZOOM}-z{MAX_ZOOM} -> {TILE_ROOT}")
    written = tile_geotiff(tif_path, TILE_ROOT, MIN_ZOOM, MAX_ZOOM)

    print(f"[4/4] 完成，共生成 {len(written)} 张瓦片")
    per_zoom: dict[int, int] = {}
    for p in written:
        z = int(p.relative_to(TILE_ROOT).parts[0])
        per_zoom[z] = per_zoom.get(z, 0) + 1
    for z in sorted(per_zoom):
        print(f"      z{z}: {per_zoom[z]} 张")


if __name__ == "__main__":
    main()
