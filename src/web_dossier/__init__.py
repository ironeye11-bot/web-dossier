"""Public-web dossier: URL in, markdown + images out. No LAN, no credentials."""

from web_dossier.dossier import build_dossier
from web_dossier.safety import UnsafeUrl, safe_public_url

__version__ = "1.0.0"
__all__ = ["build_dossier", "safe_public_url", "UnsafeUrl", "__version__"]
