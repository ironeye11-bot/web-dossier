"""Write dossier.md + assets to a folder."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from web_dossier.crawl import crawl, download_images


def asset_name(url: str, extension: str, index: int) -> str:
    try:
        from urllib.parse import urlsplit

        stem = Path(urlsplit(url).path).stem
    except ValueError:
        stem = "image"
    stem = re.sub(r"[^A-Za-z0-9_-]+", "-", stem).strip("-")[:48] or "image"
    digest = hashlib.sha1(url.encode("utf-8", errors="replace")).hexdigest()[:8]
    ext = extension if re.fullmatch(r"\.[A-Za-z0-9]{2,5}", extension or "") else ".jpg"
    return f"{index:02d}-{stem}-{digest}{ext.lower()}"


def render_markdown(crawl_result: dict[str, Any], assets: list[dict[str, str]], max_chars: int = 14_000) -> str:
    parts = [f"# Dossier", "", f"Source: {crawl_result.get('root_url', '')}", ""]
    for index, page in enumerate(crawl_result.get("pages") or [], start=1):
        title = str(page.get("title") or "Untitled").strip()
        text = re.sub(r"\s+", " ", str(page.get("text") or "")).strip()[:1200]
        parts.append(f"## {index}. {title}")
        parts.append(f"<{page.get('url', '')}>")
        parts.append("")
        parts.append(text)
        parts.append("")
    if assets:
        parts.append("## Local images")
        parts.append("")
        for item in assets:
            parts.append(f"- `{item['path']}` ← {item['url']}")
        parts.append("")
    body = "\n".join(parts)
    return body[:max_chars]


def build_dossier(
    url: str,
    out_dir: Path,
    *,
    max_pages: int = 8,
    max_depth: int = 2,
    max_images: int = 12,
    timeout: int = 20,
    opener: Any = None,
) -> dict[str, Any]:
    out_dir = out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    result = crawl(url, max_pages=max_pages, max_depth=max_depth, timeout=timeout, opener=opener)
    if not result.get("ok"):
        return {"ok": False, "reason": result.get("reason") or "crawl_failed", "out": str(out_dir)}
    images = download_images(list(result.get("images") or []), limit=max_images, timeout=timeout, opener=opener)
    asset_dir = out_dir / "assets"
    asset_dir.mkdir(exist_ok=True)
    saved_meta: list[dict[str, str]] = []
    for index, image in enumerate(images, start=1):
        name = asset_name(str(image["url"]), str(image.get("extension") or ".jpg"), index)
        path = asset_dir / name
        path.write_bytes(image["data"])
        rel = f"assets/{name}"
        saved_meta.append({"path": rel, "url": str(image["url"])})
    markdown = render_markdown(result, saved_meta)
    (out_dir / "dossier.md").write_text(markdown, encoding="utf-8")
    snapshot = {
        "root_url": result["root_url"],
        "pages": [
            {"url": p["url"], "title": p["title"], "text": p["text"][:2000]}
            for p in result["pages"]
        ],
        "assets": saved_meta,
    }
    (out_dir / "pages.json").write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "ok": True,
        "out": str(out_dir),
        "pages": len(result["pages"]),
        "images": len(saved_meta),
        "root_url": result["root_url"],
        "markdown": str(out_dir / "dossier.md"),
    }
