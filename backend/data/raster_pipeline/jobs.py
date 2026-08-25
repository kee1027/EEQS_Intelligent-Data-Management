"""栅格任务编排（TODO 骨架，P3 阶段实现）。

「自动下载 -> 出图」任务的状态机编排入口。
"""

from __future__ import annotations


def run_raster_job(job_id: str) -> dict:
    """执行一个栅格处理任务，返回最终状态。

    TODO(P3) 状态机草案：

    1. PENDING    从数据库 / 任务表加载 job 参数
                   （product, date, tiles, clip_bounds, zoom 范围）
    2. DOWNLOADING
       - 调用 downloader.download_modis(product, date, tiles, RAW_ROOT)
       - 已存在的 granule 跳过
    3. RENDERING
       - readers.read_modis_hdf_to_xarray 读取当天所有 granule
       - render.render_to_geotiff 合并/重投影/裁剪 -> tmp/<job_id>.tif
    4. TILING
       - render.tile_geotiff -> data/tiles_<dataset>/<z>/<x>/<y>.png
    5. REGISTERING
       - 若产生新 dataset，确保 mysite/settings.py 的 TILE_DATASETS 已注册
       - 记录瓦片清单与数据日期，供前端选择时间轴
    6. DONE / FAILED
       - 清理 tmp 中间文件（可配置保留）
       - 写回任务状态、耗时、瓦片数量、错误信息

    错误处理约定：
    - DOWNLOADING 失败可重试 N 次（指数退避）
    - 任何阶段异常 -> FAILED，保留现场日志，不删除 raw 数据
    """
    raise NotImplementedError("P3 阶段实现：任务状态机编排")
