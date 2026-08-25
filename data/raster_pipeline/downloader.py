"""MODIS 数据下载器（TODO 骨架，P2 阶段实现）。

计划基于 earthaccess（NASA Earthdata Login）实现自动检索与下载，
落盘结构约定：data/raster_data/raw/<产品>/<YYYY-MM-DD>/<文件名>.hdf
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence


def download_modis(
    product: str,
    date: str,
    tiles: Sequence[str],
    out_dir: str | Path,
) -> list[Path]:
    """下载指定产品 / 日期 / 分幅的 MODIS 数据到本地 raw 目录。

    Parameters
    ----------
    product : str
        产品短名，例如 "MOD10A1"（Terra）或 "MYD10A1"（Aqua）。
    date : str
        观测日期，"YYYY-MM-DD"。
    tiles : Sequence[str]
        分幅号列表，例如 ["h23v04", "h24v04"]。
    out_dir : str | Path
        raw 根目录（通常是 data/raster_data/raw），函数内部会拼接
        <product>/<date>/ 子目录。

    Returns
    -------
    list[Path]
        下载成功的文件路径列表。

    Notes
    -----
    TODO(P2):
    - earthaccess.login()（优先读取 ~/.netrc 或环境变量 EARTHDATA_USER/PASS）
    - earthaccess.search_data(short_name=product, temporal=(date, date),
      granule_name=f"*.{tile}.*" for tile in tiles)
    - earthaccess.download(...) -> 移动到 out_dir/<product>/<date>/
    - 失败重试与断点续传；已存在文件跳过（按文件名 + 大小校验）
    """
    raise NotImplementedError("P2 阶段实现：基于 earthaccess 的 Earthdata 下载")
