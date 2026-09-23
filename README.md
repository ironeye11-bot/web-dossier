# web-dossier

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/ironeye11-bot/web-dossier/actions/workflows/ci.yml/badge.svg)](https://github.com/ironeye11-bot/web-dossier/actions/workflows/ci.yml)


<p align="center">
  <img src="docs/hero.jpg" alt="field dossier" width="100%">
</p>
<p align="center">
  <img src="docs/hero.svg" alt="web-dossier" width="100%">
</p>

**Public URL in. Markdown plus images out.**

Same-site crawl with hard caps. Localhost, private LAN, link-local, credentials in the URL and ports other than 80/443 are refused. Redirects are checked again. No cloud account. No telemetry.

<p align="center">
  <img src="docs/terminal.svg" alt="CLI example" width="86%">
</p>

## Install

```bash
pip install git+https://github.com/ironeye11-bot/web-dossier.git
```

## Use

```bash
web-dossier https://example.com --out ./site
web-dossier https://example.com --pages 6 --images 10 --json
web-dossier http://127.0.0.1/admin
# blocked (private_host)
```

Writes:

```
site/dossier.md
site/pages.json
site/assets/…
```

## What it will not do

- fetch `localhost`, `127.0.0.1`, `10.*`, `192.168.*`, `169.254.*`
- follow a redirect onto those hosts
- open `file:`, `ftp:`, or port `8080`
- run JavaScript
- log in

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## License

MIT
