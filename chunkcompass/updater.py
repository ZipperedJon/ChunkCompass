"""Check GitHub for a newer release and download its installer.

Uses only the standard library (urllib + ssl). Network calls should be run off
the UI thread by the caller.
"""

from __future__ import annotations

import json
import os
import ssl
import tempfile
import urllib.request

from . import __version__

REPO = "ZipperedJon/ChunkCompass"
_API = f"https://api.github.com/repos/{REPO}/releases/latest"
_HEADERS = {
    "User-Agent": "ChunkCompass-Updater",
    "Accept": "application/vnd.github+json",
}


def _ctx() -> ssl.SSLContext:
    # create_default_context() loads the Windows system trust store, so HTTPS
    # to GitHub verifies without bundling CA certs.
    return ssl.create_default_context()


def _version_tuple(text: str) -> tuple:
    nums = []
    for part in text.lstrip("vV").replace("-", ".").split("."):
        if part.isdigit():
            nums.append(int(part))
        else:
            break
    return tuple(nums)


def get_latest(timeout: int = 15) -> dict:
    """Return {'tag', 'assets': {name: url}, 'url', 'notes'} for the latest release."""
    req = urllib.request.Request(_API, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout, context=_ctx()) as resp:
        data = json.load(resp)
    assets = {a["name"]: a["browser_download_url"] for a in (data.get("assets") or [])}
    return {
        "tag": data.get("tag_name", ""),
        "assets": assets,
        "url": data.get("html_url", ""),
        "notes": data.get("body", ""),
    }


def is_newer(tag: str) -> bool:
    return bool(tag) and _version_tuple(tag) > _version_tuple(__version__)


def pick_installer(assets: dict) -> tuple:
    """Prefer the .msi, then the .exe. Returns (name, url) or (None, None)."""
    for suffix in (".msi", ".exe"):
        for name, url in assets.items():
            if name.lower().endswith(suffix):
                return name, url
    return None, None


def download(url: str, name: str, timeout: int = 120) -> str:
    """Download an asset to a temp folder and return its path."""
    dest_dir = os.path.join(tempfile.gettempdir(), "ChunkCompass-update")
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, name)
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout, context=_ctx()) as resp, \
            open(dest, "wb") as fh:
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            fh.write(chunk)
    return dest
