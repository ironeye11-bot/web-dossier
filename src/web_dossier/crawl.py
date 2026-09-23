"""Same-site crawl with hard caps. Never follows off-site or unsafe URLs."""

from __future__ import annotations

from collections import deque
from typing import Any

from web_dossier.fetch import fetch_image, fetch_page
from web_dossier.parse import parse_html, same_site
from web_dossier.safety import try_safe_url

SKIP_EXT = {
    ".7z", ".avi", ".bmp", ".css", ".csv", ".doc", ".docx", ".gif", ".gz",
    ".ico", ".jpeg", ".jpg", ".js", ".json", ".m4a", ".mov", ".mp3", ".mp4",
    ".mpeg", ".pdf", ".png", ".rar", ".svg", ".tar", ".tgz", ".txt",
    ".wav", ".webm", ".webp", ".xml", ".zip",
}


def _looks_like_page(url: str) -> bool:
    path = url.split("?", 1)[0].lower()
    for ext in SKIP_EXT:
        if path.endswith(ext):
            return False
    return True


def crawl(
    root: str,
    *,
    max_pages: int = 8,
    max_depth: int = 2,
    timeout: int = 20,
    opener: Any = None,
) -> dict[str, Any]:
    start = try_safe_url(root)
    if not start:
        return {"ok": False, "reason": "blocked_url", "root_url": root, "pages": []}
    seen: set[str] = set()
    queue: deque[tuple[str, int]] = deque([(start, 0)])
    pages: list[dict[str, Any]] = []
    images: list[str] = []
    while queue and len(pages) < max_pages:
        url, depth = queue.popleft()
        if url in seen:
            continue
        seen.add(url)
        result = fetch_page(url, timeout=timeout, opener=opener)
        if not result.get("ok"):
            continue
        parsed = parse_html(str(result["text"]), str(result["url"]))
        pages.append(
            {
                "url": result["url"],
                "title": parsed["title"],
                "text": parsed["text"],
                "images": parsed["images"],
            }
        )
        for img in parsed["images"]:
            if img not in images:
                images.append(img)
        if depth >= max_depth:
            continue
        for link in parsed["links"]:
            safe = try_safe_url(str(link))
            if not safe or safe in seen:
                continue
            if not same_site(start, safe):
                continue
            if not _looks_like_page(safe):
                continue
            queue.append((safe, depth + 1))
    return {
        "ok": bool(pages),
        "root_url": start,
        "pages": pages,
        "images": images,
        "reason": None if pages else "no_pages",
    }


def download_images(
    urls: list[str],
    *,
    limit: int = 12,
    timeout: int = 20,
    opener: Any = None,
) -> list[dict[str, Any]]:
    saved: list[dict[str, Any]] = []
    for url in urls:
        if len(saved) >= limit:
            break
        safe = try_safe_url(url)
        if not safe:
            continue
        result = fetch_image(safe, timeout=timeout, opener=opener)
        if result.get("ok"):
            saved.append(result)
    return saved
