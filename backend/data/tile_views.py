import hashlib
from email.utils import parsedate_to_datetime

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.utils.http import http_date
from django.views import View

from .tile_service import get_content_type, parse_y_ext, resolve_tile_path, validate_xyz


class TileView(View):
    def get(self, request, dataset: str, z: int, x: int, y_ext: str):
        try:
            y, ext = parse_y_ext(y_ext)
            validate_xyz(z=z, x=x, y=y)
            tile_path = resolve_tile_path(dataset=dataset, z=z, x=x, y=y, ext=ext)
        except ValueError as exc:
            return HttpResponseBadRequest(str(exc))

        if not tile_path.exists() or not tile_path.is_file():
            return HttpResponseNotFound("tile not found")

        stat_info = tile_path.stat()
        etag = hashlib.md5(
            f"{tile_path}:{stat_info.st_size}:{stat_info.st_mtime_ns}".encode("utf-8")
        ).hexdigest()
        last_modified_header = http_date(stat_info.st_mtime)

        req_etag = request.headers.get("If-None-Match", "").strip('"')
        if req_etag and req_etag == etag:
            response = HttpResponse(status=304)
            response["ETag"] = f'"{etag}"'
            response["Last-Modified"] = last_modified_header
            return response

        req_modified = request.headers.get("If-Modified-Since")
        if req_modified:
            try:
                req_modified_dt = parsedate_to_datetime(req_modified)
                if req_modified_dt and req_modified_dt.timestamp() >= int(stat_info.st_mtime):
                    response = HttpResponse(status=304)
                    response["ETag"] = f'"{etag}"'
                    response["Last-Modified"] = last_modified_header
                    return response
            except (TypeError, ValueError, OverflowError):
                pass

        # 读入内存而非 FileResponse 流式返回：瓦片只有几十 KB，
        # 且 Windows 上流式句柄不随响应关闭，会导致临时目录无法清理（WinError 32）。
        response = HttpResponse(tile_path.read_bytes(), content_type=get_content_type(ext))
        response["ETag"] = f'"{etag}"'
        response["Last-Modified"] = last_modified_header
        response["Cache-Control"] = getattr(
            settings, "TILE_CACHE_CONTROL", "public, max-age=3600"
        )
        return response
