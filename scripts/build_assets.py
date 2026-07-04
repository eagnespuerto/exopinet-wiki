#!/usr/bin/env python3
"""Render the planet-type SVGs in assets/svg/ into 128x128 BMPs.

The Tk PhotoImage on some Pi OS builds can't decode BMP directly; the app
falls back to Pillow if that happens. Either way the BMPs need to exist, and
we regenerate them here so the SVG remains the single source of truth for the
design. Uses Pillow drawing primitives that mirror each SVG's design — no
cairosvg / rsvg-convert dependency on ARMv6.
"""

from __future__ import annotations

import pathlib

from PIL import Image, ImageDraw, ImageFont


ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "bmp"
OUT.mkdir(parents=True, exist_ok=True)

SIZE = 128
BG = (0, 8, 20)


def _radial(size, cx, cy, r, inner, mid, outer):
    """Simple 3-stop radial gradient onto a fresh image."""
    img = Image.new("RGB", (size, size), BG)
    px = img.load()
    for y in range(size):
        for x in range(size):
            dx = x - cx
            dy = y - cy
            dist = (dx * dx + dy * dy) ** 0.5
            if dist > r:
                continue
            t = dist / r
            if t < 0.4:
                c = _lerp(inner, mid, t / 0.4)
            else:
                c = _lerp(mid, outer, (t - 0.4) / 0.6)
            px[x, y] = c
    return img


def _lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _band(y, height, color, opacity):
    """Return a translucent horizontal ellipse band as an RGBA layer."""
    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.ellipse(
        (0, y - height, SIZE, y + height),
        fill=color + (int(opacity * 255),),
    )
    return layer


def _apply(base, layer):
    base_rgba = base.convert("RGBA")
    base_rgba.alpha_composite(layer)
    return base_rgba.convert("RGB")


def _highlight(base, cx, cy, rx, ry, opacity=0.2):
    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.ellipse(
        (cx - rx, cy - ry, cx + rx, cy + ry),
        fill=(255, 255, 255, int(opacity * 255)),
    )
    return _apply(base, layer)


def _mask_to_disk(img, cx, cy, r):
    """Clip anything outside the planet disk back to the space background."""
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    background = Image.new("RGB", (SIZE, SIZE), BG)
    return Image.composite(img, background, mask)


def build_terrestrial():
    img = _radial(SIZE, 58, 51, 46, (107, 183, 255), (45, 106, 167), (13, 42, 74))
    img = _mask_to_disk(img, 64, 64, 46)
    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse((36, 46, 62, 62), fill=(77, 139, 58, 220))
    d.ellipse((66, 70, 92, 92), fill=(110, 163, 79, 220))
    d.ellipse((56, 82, 74, 94), fill=(90, 149, 65, 220))
    img = _apply(img, layer)
    return _highlight(img, 50, 46, 12, 6)


def build_super_earth():
    img = _radial(SIZE, 54, 49, 52, (214, 154, 93), (138, 74, 37), (44, 17, 8))
    img = _mask_to_disk(img, 64, 64, 52)
    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse((38, 44, 66, 60), fill=(58, 31, 14, 140))
    d.ellipse((60, 60, 96, 80), fill=(58, 31, 14, 115))
    d.ellipse((48, 80, 72, 92), fill=(195, 122, 58, 125))
    d.ellipse((76, 42, 88, 50), fill=(195, 122, 58, 150))
    img = _apply(img, layer)
    return _highlight(img, 48, 42, 14, 7)


def build_mini_neptune():
    img = _radial(SIZE, 54, 49, 50, (142, 228, 200), (58, 143, 138), (13, 44, 52))
    img = _mask_to_disk(img, 64, 64, 50)
    img = _apply(img, _band(52, 4, (255, 255, 255), 0.12))
    img = _apply(img, _band(66, 3, (255, 255, 255), 0.08))
    img = _apply(img, _band(78, 4, (13, 44, 52), 0.20))
    img = _mask_to_disk(img, 64, 64, 50)
    return _highlight(img, 48, 42, 14, 6, 0.22)


def build_neptune_like():
    img = _radial(SIZE, 54, 49, 54, (90, 168, 255), (30, 79, 160), (4, 14, 40))
    img = _mask_to_disk(img, 64, 64, 54)
    img = _apply(img, _band(50, 4, (255, 255, 255), 0.14))
    img = _apply(img, _band(64, 3, (4, 14, 40), 0.25))
    img = _apply(img, _band(80, 5, (255, 255, 255), 0.10))
    img = _mask_to_disk(img, 64, 64, 54)
    # dark storm
    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse((68, 68, 84, 76), fill=(2, 8, 24, 150))
    img = _apply(img, layer)
    return _highlight(img, 48, 44, 16, 7, 0.22)


def build_gas_giant():
    img = _radial(SIZE, 54, 49, 58, (240, 212, 163), (176, 117, 64), (58, 28, 7))
    img = _mask_to_disk(img, 64, 64, 58)
    for y, color, opacity in (
        (42, (90, 47, 16), 0.35),
        (54, (247, 224, 172), 0.30),
        (66, (90, 47, 16), 0.30),
        (80, (247, 224, 172), 0.28),
        (92, (90, 47, 16), 0.28),
    ):
        img = _apply(img, _band(y, 4, color, opacity))
    img = _mask_to_disk(img, 64, 64, 58)
    # great red spot
    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse((72, 67, 92, 77), fill=(166, 53, 16, 220))
    img = _apply(img, layer)
    return _highlight(img, 48, 42, 18, 7, 0.2)


def build_unknown():
    img = _radial(SIZE, 54, 49, 48, (160, 160, 168), (84, 84, 92), (20, 20, 24))
    img = _mask_to_disk(img, 64, 64, 48)
    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 52)
    except OSError:
        font = ImageFont.load_default()
    d.text((64, 46), "?", fill=(255, 255, 255, 190), font=font, anchor="mm")
    img = _apply(img, layer)
    return _highlight(img, 50, 44, 14, 6)


BUILDERS = {
    "terrestrial": build_terrestrial,
    "super-earth": build_super_earth,
    "mini-neptune": build_mini_neptune,
    "neptune-like": build_neptune_like,
    "gas-giant": build_gas_giant,
    "unknown": build_unknown,
}


def main() -> None:
    for name, builder in BUILDERS.items():
        img = builder()
        out = OUT / f"{name}.bmp"
        img.save(out, format="BMP")
        print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
