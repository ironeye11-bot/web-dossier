"""CLI for web-dossier."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from web_dossier import __version__, build_dossier
from web_dossier.safety import UnsafeUrl, safe_public_url


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="web-dossier",
        description="Fetch a public website into dossier.md plus local images. Blocks LAN and odd ports.",
    )
    parser.add_argument("--version", action="version", version=f"web-dossier {__version__}")
    parser.add_argument("url", help="public http(s) URL")
    parser.add_argument("--out", type=Path, default=Path("dossier-out"), help="output folder")
    parser.add_argument("--pages", type=int, default=8, help="max pages (default 8)")
    parser.add_argument("--depth", type=int, default=2, help="max link depth (default 2)")
    parser.add_argument("--images", type=int, default=12, help="max images (default 12)")
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        safe_public_url(args.url)
    except UnsafeUrl as exc:
        msg = f"web-dossier: blocked ({exc})"
        if args.json:
            print(json.dumps({"ok": False, "reason": str(exc)}))
        else:
            print(msg, file=sys.stderr)
        return 2

    result = build_dossier(
        args.url,
        args.out,
        max_pages=max(1, args.pages),
        max_depth=max(0, args.depth),
        max_images=max(0, args.images),
        timeout=max(1, args.timeout),
    )
    if args.json:
        print(json.dumps(result, indent=2))
    elif result.get("ok"):
        print(f"wrote {result['markdown']}")
        print(f"pages {result['pages']}  images {result['images']}")
    else:
        print(f"web-dossier: {result.get('reason')}", file=sys.stderr)
        return 1
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
