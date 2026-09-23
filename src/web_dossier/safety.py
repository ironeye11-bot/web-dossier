"""SSRF guard: public http(s) on 80/443 only. No creds, no LAN, no odd ports."""

from __future__ import annotations

import ipaddress
import socket
import urllib.parse

ALLOWED_PORTS = {None, 80, 443}
BLOCKED_HOSTS = {"localhost", "localhost.localdomain"}


class UnsafeUrl(ValueError):
    """URL is not allowed for fetch."""


def is_public_ip(raw: str) -> bool:
    try:
        address = ipaddress.ip_address(raw)
    except ValueError:
        return False
    return not (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


def host_is_public(hostname: str) -> bool:
    host = str(hostname or "").strip().rstrip(".").lower()
    if not host or host in BLOCKED_HOSTS or host.endswith(".local"):
        return False
    try:
        ipaddress.ip_address(host)
        return is_public_ip(host)
    except ValueError:
        pass
    try:
        entries = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except OSError:
        return False
    if not entries:
        return False
    for entry in entries:
        raw = entry[4][0]
        if not is_public_ip(str(raw)):
            return False
    return True


def safe_public_url(url: str) -> str:
    try:
        parsed = urllib.parse.urlsplit(str(url or "").strip())
    except ValueError as exc:
        raise UnsafeUrl("malformed") from exc
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise UnsafeUrl("scheme")
    if parsed.username or parsed.password:
        raise UnsafeUrl("credentials")
    try:
        port = parsed.port
    except ValueError as exc:
        raise UnsafeUrl("port") from exc
    if port not in ALLOWED_PORTS:
        raise UnsafeUrl("port")
    if not host_is_public(parsed.hostname):
        raise UnsafeUrl("private_host")
    return urllib.parse.urlunsplit(
        (parsed.scheme.lower(), parsed.netloc, parsed.path or "/", parsed.query, "")
    )


def try_safe_url(url: str) -> str | None:
    try:
        return safe_public_url(url)
    except UnsafeUrl:
        return None
