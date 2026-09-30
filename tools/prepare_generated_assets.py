"""Normalize generated transparent pet art into consistent 512px sprite canvases."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageOps


CANVAS_SIZE = 512
CONTENT_SIZE = 472


def normalize(source: Path, destination: Path, mirror: bool = False) -> None:
    with Image.open(source) as opened:
        image = opened.convert("RGBA")
    alpha_box = image.getchannel("A").getbbox()
    if alpha_box is None:
        raise ValueError(f"No visible pixels in {source}")
    image = image.crop(alpha_box)
    if mirror:
        image = ImageOps.mirror(image)
    scale = min(CONTENT_SIZE / image.width, CONTENT_SIZE / image.height)
    size = (
        max(1, round(image.width * scale)),
        max(1, round(image.height * scale)),
    )
    image = image.resize(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    x = (CANVAS_SIZE - image.width) // 2
    y = (CANVAS_SIZE - image.height) // 2
    canvas.alpha_composite(image, (x, y))
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination, optimize=True)


def main() -> None:
    if len(sys.argv) not in (3, 4):
        raise SystemExit("usage: prepare_generated_assets.py SOURCE DESTINATION [mirror]")
    normalize(
        Path(sys.argv[1]),
        Path(sys.argv[2]),
        mirror=len(sys.argv) == 4 and sys.argv[3] == "mirror",
    )


if __name__ == "__main__":
    main()
