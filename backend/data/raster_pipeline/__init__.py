"""Raster pipeline package.

MODIS 栅格数据的「下载 -> 读取 -> 拼接 -> 重投影 -> 裁剪 -> 切瓦片」流水线。
P1 阶段提供 readers / render 两个可用模块，downloader / jobs 为 P2/P3 预留骨架。
"""

__all__ = ["readers", "render"]
