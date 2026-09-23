"""HTML title, visible text, same-site links, images."""

from __future__ import annotations

import re
import urllib.parse
from html.parser import HTMLParser

SKIP_TAGS = {"script", "style", "noscript", "template"}
IMAGE_META = {"og:image", "twitter:image", "twitter:image:src"}


def srcset_urls(value: str) -> list[str]:
    out: list[str] = []
    for part in value.split(","):
        token = part.strip().split()
        if token:
            out.append(token[0])
    return out


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self.links: list[str] = []
        self.images: list[str] = []
        self._title = False
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        name = tag.lower()
        values = {str(k).lower(): str(v or "") for k, v in attrs}
        if name in SKIP_TAGS:
            self._skip += 1
        if name == "title":
            self._title = True
        if name == "a" and values.get("href"):
            self.links.append(values["href"])
        if name == "img":
            for key in ("src", "data-src", "data-lazy-src", "data-original"):
                if values.get(key):
                    self.images.append(values[key])
                    break
            if values.get("srcset"):
                self.images.extend(srcset_urls(values["srcset"]))
        if name == "source" and values.get("srcset"):
            self.images.extend(srcset_urls(values["srcset"]))
        if name == "meta" and values.get("content"):
            marker = (values.get("property") or values.get("name") or "").lower()
            if marker in IMAGE_META:
                self.images.append(values["content"])

    def handle_endtag(self, tag: str) -> None:
        name = tag.lower()
        if name in SKIP_TAGS and self._skip:
            self._skip -= 1
        if name == "title":
            self._title = False

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        text = re.sub(r"\s+", " ", data).strip()
        if not text:
            return
        if self._title:
            self.title_parts.append(text)
        else:
            self.text_parts.append(text)


def parse_html(html: str, base_url: str) -> dict[str, object]:
    parser = PageParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        pass
    title = " ".join(parser.title_parts).strip()
    text = " ".join(parser.text_parts).strip()
    links = _absolutize(base_url, parser.links)
    images = _absolutize(base_url, parser.images)
    return {"title": title, "text": text, "links": links, "images": images}


def _absolutize(base: str, values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in values:
        try:
            abs_url = urllib.parse.urljoin(base, raw.strip())
        except ValueError:
            continue
        if abs_url in seen:
            continue
        seen.add(abs_url)
        out.append(abs_url)
    return out


def same_site(first: str, second: str) -> bool:
    try:
        a = urllib.parse.urlsplit(first)
        b = urllib.parse.urlsplit(second)
    except ValueError:
        return False
    return a.scheme == b.scheme and a.hostname == b.hostname
