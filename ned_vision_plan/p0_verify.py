"""P0 依赖验证脚本：逐个导入地理库并实际读取一次 HDF4 文件。

运行方式（在项目根目录）：
    venv/Scripts/python.exe ned_vision_plan/p0_verify.py
"""
import sys

FAILURES = []


def check(name, fn):
    try:
        version = fn()
        print(f"[OK]   {name:<12} {version}")
    except Exception as exc:  # noqa: BLE001
        FAILURES.append((name, exc))
        print(f"[FAIL] {name:<12} {type(exc).__name__}: {exc}")


def _numpy():
    import numpy
    return numpy.__version__


def _xarray():
    import xarray
    return xarray.__version__


def _rioxarray():
    import rioxarray
    return rioxarray.__version__


def _rasterio():
    import rasterio
    return rasterio.__version__


def _netcdf4():
    import netCDF4
    return netCDF4.__version__


def _pyhdf():
    from pyhdf.SD import SD, SDC  # noqa: F401
    return "import OK"


def _matplotlib():
    import matplotlib
    matplotlib.use("Agg")  # 无显示环境下出图
    return matplotlib.__version__


def _pyproj():
    import pyproj
    return pyproj.__version__


def _read_hdf4():
    """关键兼容性测试：pyhdf + numpy 2.x 实际读取示例 MOD10A1。"""
    import numpy as np
    from pyhdf.SD import SD, SDC

    path = "ned_vision_plan/sample_data/MOD10A1.A2026005.h24v04.061.2026008012430.hdf"
    hdf = SD(path, SDC.READ)
    data = hdf.select("NDSI_Snow_Cover").get().astype(float)
    hdf.end()
    valid = data[(data >= 0) & (data <= 100)]
    return f"shape={data.shape}, valid_pixels={valid.size}, ndsi_mean={valid.mean():.2f}"


def main():
    print("=== P0: 依赖导入验证 ===")
    check("numpy", _numpy)
    check("xarray", _xarray)
    check("rioxarray", _rioxarray)
    check("rasterio", _rasterio)
    check("netCDF4", _netcdf4)
    check("pyhdf", _pyhdf)
    check("matplotlib", _matplotlib)
    check("pyproj", _pyproj)

    print("\n=== P0: pyhdf 实际读取示例 HDF4 ===")
    check("read_hdf4", _read_hdf4)

    if FAILURES:
        print(f"\n>>> {len(FAILURES)} 项失败：{[n for n, _ in FAILURES]}")
        sys.exit(1)
    print("\n>>> P0 全部通过")


if __name__ == "__main__":
    main()
