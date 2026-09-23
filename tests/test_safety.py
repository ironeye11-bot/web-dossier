from __future__ import annotations

import unittest

from web_dossier.parse import parse_html, same_site, srcset_urls
from web_dossier.safety import UnsafeUrl, safe_public_url, try_safe_url


class SafetyTests(unittest.TestCase):
    def test_blocks_loopback(self) -> None:
        for url in (
            "http://127.0.0.1/",
            "http://localhost/admin",
            "http://[::1]/",
            "http://0.0.0.0/",
        ):
            with self.subTest(url=url):
                self.assertIsNone(try_safe_url(url))

    def test_blocks_private_lan(self) -> None:
        for url in (
            "http://192.168.1.10/x",
            "http://10.0.0.5/x",
            "http://172.16.0.4/x",
            "http://169.254.1.1/x",
        ):
            with self.subTest(url=url):
                self.assertIsNone(try_safe_url(url))

    def test_blocks_credentials_and_ports_and_schemes(self) -> None:
        self.assertIsNone(try_safe_url("http://user:pass@example.com/"))
        self.assertIsNone(try_safe_url("http://example.com:8080/"))
        self.assertIsNone(try_safe_url("ftp://example.com/"))
        self.assertIsNone(try_safe_url("file:///etc/passwd"))

    def test_https_example_allowed_if_public_dns(self) -> None:
        # example.com is IANA reserved and resolves to public docs IPs.
        try:
            out = safe_public_url("https://example.com/path?q=1#frag")
        except UnsafeUrl:
            self.skipTest("example.com did not resolve in this environment")
        self.assertTrue(out.startswith("https://example.com/path"))
        self.assertNotIn("#", out)

    def test_parser_skips_script(self) -> None:
        html = "<html><head><title>Hi</title><script>steal()</script></head><body><p>Hello</p><img src='/a.png'></body></html>"
        parsed = parse_html(html, "https://example.com/page")
        self.assertEqual(parsed["title"], "Hi")
        self.assertIn("Hello", parsed["text"])
        self.assertNotIn("steal", parsed["text"])
        self.assertEqual(parsed["images"], ["https://example.com/a.png"])

    def test_srcset_and_same_site(self) -> None:
        self.assertEqual(srcset_urls("a.jpg 1x, b.jpg 2x"), ["a.jpg", "b.jpg"])
        self.assertTrue(same_site("https://a.com/x", "https://a.com/y"))
        self.assertFalse(same_site("https://a.com/x", "https://b.com/x"))


if __name__ == "__main__":
    unittest.main()
