from pathlib import Path
from typing import Tuple

from django.conf import settings


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "pbf"}
CONTENT_TYPES = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "pbf": "application/x-protobuf",
}


def parse_y_ext(y_ext: str) -> Tuple[int, str]:
    if "." not in y_ext:
        raise ValueError("tile y and extension format must be '<y>.<ext>'")

    y_text, ext = y_ext.rsplit(".", 1)
    if not y_text.isdigit():
        raise ValueError("tile y must be a non-negative integer")

    y = int(y_text)
    if y < 0:
        raise ValueError("tile y must be a non-negative integer")

    ext = ext.lower()
    allowed_ext = set(getattr(settings, "TILE_ALLOWED_EXTENSIONS", ALLOWED_EXTENSIONS))
    if ext not in allowed_ext:
        raise ValueError("tile extension is not allowed")

    return y, ext


def validate_xyz(z: int, x: int, y: int) -> None:
    min_zoom = int(getattr(settings, "TILE_MIN_ZOOM", 0))
    max_zoom = int(getattr(settings, "TILE_MAX_ZOOM", 22))

    if z < min_zoom or z > max_zoom:
        raise ValueError("tile z is out of supported zoom range")
    if x < 0 or y < 0:
        raise ValueError("tile x/y must be non-negative")

    max_index = 1 << z
    if x >= max_index or y >= max_index:
        raise ValueError("tile x/y exceeds xyz bounds for this zoom")


def resolve_tile_path(dataset: str, z: int, x: int, y: int, ext: str) -> Path:
    datasets = getattr(settings, "TILE_DATASETS", {})
    dataset_root = datasets.get(dataset)
    if not dataset_root:
        raise ValueError("unknown tile dataset")

    root = Path(dataset_root).resolve()
    tile_path = (root / str(z) / str(x) / f"{y}.{ext}").resolve()

    if root not in tile_path.parents and tile_path != root:
        raise ValueError("resolved tile path escapes dataset root")

    return tile_path


def get_content_type(ext: str) -> str:
    return CONTENT_TYPES.get(ext, "application/octet-stream")
