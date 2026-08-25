"""栅格渲染：合并 / 重投影 / 裁剪成 GeoTIFF，以及 GeoTIFF 切 XYZ 瓦片。

- render_to_geotiff: 多个 MODIS HDF -> 单个 Web Mercator (EPSG:3857) GeoTIFF
- tile_geotiff: GeoTIFF -> XYZ 瓦片金字塔（离散 NDSI 配色，无数据区透明）
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np
import xarray as xr
import rioxarray  # noqa: F401
from rioxarray.merge import merge_arrays
from rasterio.warp import transform_bounds

# ---------------------------------------------------------------------------
# 离散配色（与 ned_vision_plan/draw_data2.ipynb 保持一致）
# ---------------------------------------------------------------------------
NDSI_BOUNDS = [0, 20, 40, 60, 80, 100]
NDSI_COLORS = [
    "#e0f3f8",  # 0-20%
    "#74add1",  # 20-40%
    "#fee090",  # 40-60%
    "#fdae61",  # 60-80%
    "#f46d43",  # 80-100%
]


def _hex_to_rgba(hex_color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    hex_color = hex_color.lstrip("#")
    return (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
        alpha,
    )


NDSI_RGBA = [_hex_to_rgba(c) for c in NDSI_COLORS]

WEB_MERCATOR = "EPSG:3857"


def render_to_geotiff(
    arrays: Sequence[xr.DataArray],
    out_path: str | Path,
    clip_bounds_lonlat: tuple[float, float, float, float] | None = None,
    dst_crs: str = WEB_MERCATOR,
) -> Path:
    """合并多个 DataArray，重投影并裁剪后写出 GeoTIFF。

    Parameters
    ----------
    arrays : Sequence[xr.DataArray]
        readers.read_modis_hdf_to_xarray 的返回值列表。
    out_path : str | Path
        输出 GeoTIFF 路径（父目录自动创建）。
    clip_bounds_lonlat : tuple | None
        (min_lon, min_lat, max_lon, max_lat)，经纬度裁剪框；
        内部会转换到目标 CRS 后 clip。None 则不裁剪。
    dst_crs : str
        目标 CRS，默认 EPSG:3857（Web Mercator，配合 XYZ 瓦片）。
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    arrays = list(arrays)
    merged = arrays[0] if len(arrays) == 1 else merge_arrays(arrays)

    reproj = merged.rio.reproject(dst_crs)

    if clip_bounds_lonlat is not None:
        minx, miny, maxx, maxy = transform_bounds(
            "EPSG:4326", dst_crs, *clip_bounds_lonlat
        )
        reproj = reproj.rio.clip_box(minx=minx, miny=miny, maxx=maxx, maxy=maxy)

    reproj = reproj.astype("float32").rio.write_nodata(np.nan)
    reproj.rio.to_raster(str(out_path), driver="GTiff")
    return out_path


def _classify_to_rgba(data: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """把单波段数值按 NDSI_BOUNDS/NDSI_RGBA 离散分级成 RGBA uint8 图像。

    无效值（mask 或 NaN 或越界）alpha=0 完全透明。
    """
    h, w = data.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)

    valid = (~mask) & np.isfinite(data) & (data >= NDSI_BOUNDS[0]) & (data <= NDSI_BOUNDS[-1])
    for i in range(len(NDSI_BOUNDS) - 1):
        lo, hi = NDSI_BOUNDS[i], NDSI_BOUNDS[i + 1]
        if i < len(NDSI_BOUNDS) - 2:
            in_bin = valid & (data >= lo) & (data < hi)
        else:  # 最后一档闭区间，包含 100
            in_bin = valid & (data >= lo) & (data <= hi)
        rgba[in_bin] = NDSI_RGBA[i]
    return rgba


def tile_geotiff(
    tif_path: str | Path,
    out_root: str | Path,
    min_zoom: int,
    max_zoom: int,
    tilesize: int = 256,
) -> list[Path]:
    """把 GeoTIFF 切成 Web Mercator XYZ 瓦片（PNG）。

    输出结构：{out_root}/{z}/{x}/{y}.png，无数据区透明。
    返回生成的瓦片路径列表。
    """
    import morecantile
    from PIL import Image
    from rio_tiler.io import Reader

    tif_path = Path(tif_path)
    out_root = Path(out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    tms = morecantile.tms.get("WebMercatorQuad")
    written: list[Path] = []

    with Reader(str(tif_path), tms=tms) as src:
        # 数据范围（经纬度）-> 各 zoom 的瓦片覆盖范围
        west, south, east, north = transform_bounds(
            src.crs, "EPSG:4326", *src.bounds, densify_pts=21
        )
        west, south = max(west, -180.0), max(south, -85.051129)
        east, north = min(east, 180.0), min(north, 85.051129)

        for z in range(min_zoom, max_zoom + 1):
            for tile in tms.tiles(west, south, east, north, [z]):
                img = src.tile(tile.x, tile.y, z, tilesize=tilesize)
                band = np.ma.filled(img.data[0], np.nan).astype("float64")
                mask = np.ma.getmaskarray(img.data[0]) | ~np.isfinite(band)
                rgba = _classify_to_rgba(band, mask)

                # 完全透明的瓦片不写出（节省空间，前端 404 即无底图叠加层）
                if rgba[..., 3].max() == 0:
                    continue

                tile_path = out_root / str(z) / str(tile.x) / f"{tile.y}.png"
                tile_path.parent.mkdir(parents=True, exist_ok=True)
                Image.fromarray(rgba, mode="RGBA").save(str(tile_path), "PNG")
                written.append(tile_path)

    return written
