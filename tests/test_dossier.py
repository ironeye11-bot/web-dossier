from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from email.message import EmailMessage

from web_dossier.cli import main
from web_dossier.dossier import asset_name, build_dossier, render_markdown


class FakeResponse:
    def __init__(self, url: str, body: bytes, content_type: str = "text/html") -> None:
        self._url = url
        self._body = body
        self.headers = EmailMessage()
        self.headers["Content-Type"] = content_type

    def geturl(self) -> str:
        return self._url

    def read(self, n: int = -1) -> bytes:
        return self._body if n < 0 else self._body[:n]

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None


class FakeOpener:
    def __init__(self, pages: dict[str, tuple[bytes, str]]) -> None:
        self.pages = pages

    def open(self, request: object, timeout: int = 20) -> FakeResponse:
        url = request.full_url if hasattr(request, "full_url") else str(request)
        if url not in self.pages:
            raise OSError("missing")
        body, ctype = self.pages[url]
        return FakeResponse(url, body, ctype)


class DossierTests(unittest.TestCase):
    def test_asset_name_is_stable(self) -> None:
        a = asset_name("https://cdn.example/img/hero_photo.png", ".png", 1)
        b = asset_name("https://cdn.example/img/hero_photo.png", ".png", 1)
        self.assertEqual(a, b)
        self.assertTrue(a.endswith(".png"))
        self.assertIn("hero_photo", a)

    def test_build_with_fake_opener(self) -> None:
        html = b"""<html><head><title>Demo</title></head>
        <body><p>Hello world</p><img src="/pic.png"><a href="/two">Two</a></body></html>"""
        png = b"\x89PNG\r\n\x1a\n" + b"x" * 20
        pages = {
            "https://example.com/": (html, "text/html"),
            "https://example.com/two": (b"<html><title>Two</title><p>Second</p></html>", "text/html"),
            "https://example.com/pic.png": (png, "image/png"),
        }
        opener = FakeOpener(pages)
        with tempfile.TemporaryDirectory() as tmp:
            result = build_dossier("https://example.com/", Path(tmp) / "out", opener=opener, max_pages=4, max_images=4)
            self.assertTrue(result["ok"], result)
            out = Path(result["out"])
            self.assertTrue((out / "dossier.md").exists())
            self.assertTrue((out / "pages.json").exists())
            data = json.loads((out / "pages.json").read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(data["pages"]), 1)
            md = (out / "dossier.md").read_text(encoding="utf-8")
            self.assertIn("Demo", md)

    def test_cli_blocks_localhost(self) -> None:
        code = main(["http://127.0.0.1/secret", "--json"])
        self.assertEqual(code, 2)

    def test_render_bounds(self) -> None:
        text = render_markdown(
            {"root_url": "https://example.com/", "pages": [{"title": "A", "url": "https://example.com/", "text": "x" * 5000}]},
            [],
            max_chars=200,
        )
        self.assertLessEqual(len(text), 200)


if __name__ == "__main__":
    unittest.main()
