"""MODIS HDF 读取器。

移植自 ned_vision_plan/draw_data2.ipynb（场景 A）：
- 用 pyhdf 读取 NDSI_Snow_Cover 波段
- 从文件名解析 h/v 分幅号，构造 MODIS 正弦投影（sinusoidal）下的物理坐标
- 返回带 CRS 的 xarray.DataArray
"""

from __future__ import annotations

import re

import numpy as np
import rioxarray  # noqa: F401  # 注册 .rio 访问器
import xarray as xr
from pyhdf.SD import SD, SDC

# MODIS 正弦投影（SR-ORG:6974），与 notebook 保持一致
MODIS_SINUSOIDAL_CRS = "+proj=sinu +R=6371007.181 +nadgrids=@null +wktext"

# MODIS 全球分幅网格常量（米）
TILE_SIZE = 1111950.5196666666
GRID_X_MIN = -20015109.354
GRID_Y_MAX = 10007554.677

DEFAULT_BAND = "NDSI_Snow_Cover"
VALID_RANGE = (0.0, 100.0)


def parse_tile_id(file_name: str) -> tuple[int, int]:
    """从 MODIS 文件名解析 (h, v) 分幅号，例如 h24v04 -> (24, 4)。"""
    match = re.search(r"h(\d{2})v(\d{2})", str(file_name))
    if not match:
        raise ValueError(f"无法从文件名解析 h/v 分幅号: {file_name}")
    return int(match.group(1)), int(match.group(2))


def read_modis_hdf_to_xarray(
    file_name: str,
    band: str = DEFAULT_BAND,
    valid_range: tuple[float, float] | None = VALID_RANGE,
) -> xr.DataArray:
    """读取 MODIS HDF4 文件，返回带正弦投影坐标的 xarray.DataArray。

    Parameters
    ----------
    file_name : str
        HDF 文件路径（文件名需包含 hXXvYY 分幅号）。
    band : str
        科学数据集名称，默认 NDSI_Snow_Cover。
    valid_range : tuple | None
        有效值范围（闭区间），范围外的值置为 NaN；传 None 则不过滤。
    """
    hdf = SD(str(file_name), SDC.READ)
    try:
        data = hdf.select(band).get().astype(float)
    finally:
        hdf.end()

    h, v = parse_tile_id(file_name)

    x_min = GRID_X_MIN + h * TILE_SIZE
    x_max = x_min + TILE_SIZE
    y_max = GRID_Y_MAX - v * TILE_SIZE
    y_min = y_max - TILE_SIZE

    rows, cols = data.shape
    x_coords = np.linspace(x_min, x_max, cols)
    y_coords = np.linspace(y_max, y_min, rows)

    da = xr.DataArray(
        data,
        coords=[("y", y_coords), ("x", x_coords)],
        name=band,
    )
    da = da.rio.write_crs(MODIS_SINUSOIDAL_CRS)

    if valid_range is not None:
        lo, hi = valid_range
        da = da.where((da >= lo) & (da <= hi))

    return da
