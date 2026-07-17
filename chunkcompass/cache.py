"""Two-level cache for rendered biome tiles: an in-memory LRU plus on-disk PNGs.

Revisiting an area (e.g. jumping back to a waypoint, or toggling a setting off
and on) then returns instantly instead of regenerating. The disk cache lives
under %LOCALAPPDATA%\\ChunkCompass\\cache and persists across sessions.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
import threading
from collections import OrderedDict
from pathlib import Path

from PIL import Image

_MEM: "OrderedDict[str, Image.Image]" = OrderedDict()
_MEM_MAX = 80
_LOCK = threading.Lock()


def cache_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
    d = Path(base) / "ChunkCompass" / "cache"
    try:
        d.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return d


def key_hash(parts) -> str:
    return hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:20]


def get(key: str):
    with _LOCK:
        if key in _MEM:
            _MEM.move_to_end(key)
            return _MEM[key]
    path = cache_dir() / f"{key}.png"
    if path.exists():
        try:
            img = Image.open(path)
            img.load()
            img = img.convert("RGB")
        except Exception:  # noqa: BLE001
            return None
        _put_mem(key, img)
        return img
    return None


def put(key: str, img: Image.Image) -> None:
    _put_mem(key, img)
    try:
        img.save(cache_dir() / f"{key}.png")
    except Exception:  # noqa: BLE001
        pass


def _put_mem(key: str, img: Image.Image) -> None:
    with _LOCK:
        _MEM[key] = img
        _MEM.move_to_end(key)
        while len(_MEM) > _MEM_MAX:
            _MEM.popitem(last=False)


def clear() -> None:
    with _LOCK:
        _MEM.clear()
    for f in cache_dir().glob("*.png"):
        try:
            f.unlink()
        except OSError:
            pass
