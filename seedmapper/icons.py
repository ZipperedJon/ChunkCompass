"""Programmatically drawn structure icons (no external image assets).

Each icon is a rounded colour badge with a simple white/dark pictogram, in the
spirit of map-viewer feature icons. `build_icons()` returns two dicts keyed by
structure key: normal icons and greyed-out ("explored") variants, as PIL images.
The app converts them to Tk PhotoImages.
"""

from __future__ import annotations

from PIL import Image, ImageDraw

from .engine import STRUCTURES

S = 22          # icon size in px
R = 5           # badge corner radius


def _lum(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return 0.299 * r + 0.587 * g + 0.114 * b


def _badge(color: str):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([1, 1, S - 2, S - 2], radius=R, fill=color,
                        outline="#0b1119", width=1)
    glyph = "#12202b" if _lum(color) > 150 else "#f2f7fb"
    return img, d, glyph


# --- individual pictograms (drawn within roughly the 4..18 box) ------------- #
def _house(d, c, wide=False):
    x0, x1 = (4, 18) if wide else (6, 16)
    d.polygon([(x0, 11), ((x0 + x1) // 2, 5), (x1, 11)], fill=c)      # roof
    d.rectangle([x0 + 1, 11, x1 - 1, 17], fill=c)                    # body
    d.rectangle([(x0 + x1) // 2 - 1, 13, (x0 + x1) // 2 + 1, 17],
                fill="#0b1119")                                      # door


def _tower(d, c):
    d.rectangle([8, 6, 14, 18], fill=c)
    d.polygon([(14, 6), (18, 7), (14, 9)], fill=c)                   # flag
    d.line([14, 6, 14, 18], fill=c, width=1)


def _pyramid(d, c, steps=False):
    d.polygon([(4, 17), (11, 5), (18, 17)], fill=c)
    if steps:
        d.line([7, 17, 9, 11], fill="#0b1119", width=1)
        d.line([15, 17, 13, 11], fill="#0b1119", width=1)


def _trapezoid(d, c):
    d.polygon([(5, 17), (8, 6), (14, 6), (17, 17)], fill=c)


def _dome(d, c):
    d.pieslice([4, 6, 18, 22], 180, 360, fill=c)
    d.rectangle([4, 13, 18, 15], fill=c)
    d.rectangle([10, 12, 12, 15], fill="#0b1119")


def _columns(d, c):
    d.rectangle([6, 8, 8, 18], fill=c)
    d.rectangle([11, 6, 13, 18], fill=c)
    d.rectangle([15, 10, 17, 18], fill=c)


def _anchor(d, c):
    d.ellipse([9, 4, 13, 8], outline=c, width=2)
    d.line([11, 7, 11, 17], fill=c, width=2)
    d.arc([5, 10, 17, 20], 20, 160, fill=c, width=2)


def _portal(d, c):
    d.rounded_rectangle([6, 5, 16, 18], radius=4, outline=c, width=2)


def _diamond(d, c):
    d.polygon([(11, 4), (18, 11), (11, 18), (4, 11)], fill=c)
    d.ellipse([9, 9, 13, 13], fill="#0b1119")


def _trail(d, c):
    for (x, y) in [(6, 15), (9, 12), (12, 9), (15, 6)]:
        d.ellipse([x - 1, y - 1, x + 2, y + 2], fill=c)


def _plus(d, c):
    d.rectangle([5, 5, 17, 17], outline=c, width=2)
    d.line([11, 8, 11, 14], fill=c, width=2)
    d.line([8, 11, 14, 11], fill=c, width=2)


def _chest(d, c):
    d.rectangle([5, 8, 17, 17], fill=c)
    d.rectangle([5, 8, 17, 11], fill=c, outline="#0b1119")
    d.rectangle([10, 10, 12, 13], fill="#0b1119")   # latch


def _pick(d, c):
    d.line([5, 16, 16, 5], fill=c, width=2)          # handle
    d.arc([9, 3, 19, 11], 200, 20, fill=c, width=2)  # head


def _eye(d, c):
    d.ellipse([5, 7, 17, 15], fill=c)
    d.ellipse([9, 9, 13, 13], fill="#0b2f18")        # pupil


def _arch(d, c):
    d.rectangle([5, 9, 8, 18], fill=c)
    d.rectangle([14, 9, 17, 18], fill=c)
    d.rectangle([5, 6, 17, 9], fill=c)               # lintel


def _bricks(d, c):
    d.rectangle([5, 6, 17, 17], fill=c, outline="#0b1119")
    d.line([5, 11, 17, 11], fill="#0b1119")
    d.line([11, 6, 11, 11], fill="#0b1119")
    d.line([8, 11, 8, 17], fill="#0b1119")
    d.line([14, 11, 14, 17], fill="#0b1119")


def _spire(d, c):
    d.polygon([(11, 3), (14, 8), (8, 8)], fill=c)    # spire top
    d.rectangle([8, 8, 14, 18], fill=c)              # tower
    d.rectangle([10, 12, 12, 18], fill="#0b1119")    # door


_GLYPHS = {
    "village":   lambda d, c: _house(d, c),
    "outpost":   lambda d, c: _tower(d, c),
    "monument":  lambda d, c: _trapezoid(d, c),
    "mansion":   lambda d, c: _house(d, c, wide=True),
    "desert":    lambda d, c: _pyramid(d, c, steps=True),
    "jungle":    lambda d, c: _pyramid(d, c),
    "hut":       lambda d, c: _house(d, c),
    "igloo":     lambda d, c: _dome(d, c),
    "ruin":      lambda d, c: _columns(d, c),
    "shipwreck": lambda d, c: _anchor(d, c),
    "portal":    lambda d, c: _portal(d, c),
    "city":      lambda d, c: _diamond(d, c),
    "trail":     lambda d, c: _trail(d, c),
    "trial":     lambda d, c: _plus(d, c),
    "treasure":  lambda d, c: _chest(d, c),
    "mineshaft": lambda d, c: _pick(d, c),
    "stronghold": lambda d, c: _eye(d, c),
    "fortress":  lambda d, c: _arch(d, c),
    "bastion":   lambda d, c: _bricks(d, c),
    "portal_n":  lambda d, c: _portal(d, c),
    "endcity":   lambda d, c: _spire(d, c),
}


def _grey(img: Image.Image) -> Image.Image:
    """Desaturate to a greyed, dimmed 'explored' variant with a check mark."""
    out = img.convert("RGBA")
    px = out.load()
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            v = int(0.3 * r + 0.59 * g + 0.11 * b)
            v = (v + 150) // 2                     # lift toward light grey
            px[x, y] = (v, v, v, 150)
    d = ImageDraw.Draw(out)
    d.line([14, 15, 16, 18], fill="#5fd66a", width=2)   # check mark
    d.line([16, 18, 20, 11], fill="#5fd66a", width=2)
    return out


def _disabled(img: Image.Image) -> Image.Image:
    """Dim the icon and draw a red diagonal strike (turned-off state)."""
    out = img.convert("RGBA")
    px = out.load()
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            if a:
                px[x, y] = (r // 2 + 40, g // 2 + 40, b // 2 + 40, 140)
    d = ImageDraw.Draw(out)
    d.line([2, S - 3, S - 3, 2], fill="#e53935", width=2)
    return out


def build_icons() -> tuple[dict, dict, dict]:
    """Return (normal, explored, disabled) dicts keyed by structure key."""
    normal, explored, disabled = {}, {}, {}
    for s in STRUCTURES:
        img, d, glyph = _badge(s["color"])
        drawer = _GLYPHS.get(s["key"])
        if drawer:
            drawer(d, glyph)
        normal[s["key"]] = img
        explored[s["key"]] = _grey(img)
        disabled[s["key"]] = _disabled(img)
    return normal, explored, disabled
