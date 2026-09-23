"""HTTP fetch with redirect checks and size caps."""

from __future__ import annotations

import mimetypes
import urllib.error
import urllib.request
from typing import Any, Callable

from web_dossier.safety import UnsafeUrl, safe_public_url, try_safe_url

USER_AGENT = "web-dossier/1.0 (+https://github.com/ironeye11-bot/web-dossier)"
IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/svg+xml": ".svg",
}

UrlOpen = Callable[..., Any]


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Any:
        import urllib.parse

        safe = try_safe_url(urllib.parse.urljoin(req.full_url, newurl))
        if not safe:
            raise urllib.error.URLError("blocked_redirect")
        return super().redirect_request(req, fp, code, msg, headers, safe)


def default_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(SafeRedirectHandler)


def _request(url: str) -> urllib.request.Request:
    return urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})


def fetch_page(
    url: str,
    *,
    timeout: int = 20,
    max_bytes: int = 2_000_000,
    opener: urllib.request.OpenerDirector | None = None,
) -> dict[str, Any]:
    target = safe_public_url(url)
    handle = opener or default_opener()
    try:
        with handle.open(_request(target), timeout=timeout) as response:
            final = try_safe_url(response.geturl())
            if not final:
                return {"ok": False, "reason": "blocked_redirect"}
            raw_type = response.headers.get_content_type() if hasattr(response.headers, "get_content_type") else ""
            content_type = str(raw_type or "").lower()
            data = response.read(max_bytes + 1)
    except UnsafeUrl:
        return {"ok": False, "reason": "blocked_url"}
    except Exception as exc:
        return {"ok": False, "reason": "fetch_failed", "error": type(exc).__name__}
    if not data:
        return {"ok": False, "reason": "empty"}
    if len(data) > max_bytes:
        return {"ok": False, "reason": "too_large"}
    text = data.decode("utf-8", errors="replace")
    return {"ok": True, "url": final, "content_type": content_type, "text": text, "bytes": len(data)}


def fetch_image(
    url: str,
    *,
    timeout: int = 20,
    max_bytes: int = 8 * 1024 * 1024,
    opener: urllib.request.OpenerDirector | None = None,
) -> dict[str, Any]:
    target = safe_public_url(url)
    handle = opener or default_opener()
    try:
        with handle.open(_request(target), timeout=timeout) as response:
            final = try_safe_url(response.geturl())
            if not final:
                return {"ok": False, "reason": "blocked_redirect"}
            raw_type = response.headers.get_content_type() if hasattr(response.headers, "get_content_type") else ""
            content_type = str(raw_type or "").lower()
            if content_type not in IMAGE_TYPES:
                return {"ok": False, "reason": "not_image", "content_type": content_type}
            data = response.read(max_bytes + 1)
    except UnsafeUrl:
        return {"ok": False, "reason": "blocked_url"}
    except Exception as exc:
        return {"ok": False, "reason": "download_failed", "error": type(exc).__name__}
    if not data:
        return {"ok": False, "reason": "empty_image"}
    if len(data) > max_bytes:
        return {"ok": False, "reason": "image_too_large"}
    extension = IMAGE_TYPES.get(content_type) or mimetypes.guess_extension(content_type) or ".jpg"
    return {
        "ok": True,
        "url": final,
        "content_type": content_type,
        "extension": extension,
        "data": data,
    }
