"""Normalize Water Panda sprites without distorting natural poses."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
CANVAS_SIZE = (180, 180)
GROUND_Y = 172


def alpha_bbox(image: Image.Image) -> tuple[int, int, int, int]:
    box = image.getchannel("A").getbbox()
    if box is None:
        raise ValueError("Sprite has no visible pixels")
    return box


def place_on_canvas(
    image: Image.Image,
) -> Image.Image:
    image = image.convert("RGBA")
    cropped = image.crop(alpha_bbox(image))
    canvas = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    x = (CANVAS_SIZE[0] - cropped.width) // 2
    y = GROUND_Y - cropped.height
    canvas.alpha_composite(cropped, (x, y))
    return canvas


def normalize_file(path: Path) -> None:
    with Image.open(path) as image:
        normalized = place_on_canvas(image)
    normalized.save(path, optimize=True)


def main() -> None:
    paths = sorted(ASSETS.glob("panda_*.png"))
    if not paths:
        raise SystemExit("No panda PNG assets found")
    for path in paths:
        normalize_file(path)
    print(f"Normalized {len(paths)} sprites to {CANVAS_SIZE[0]}x{CANVAS_SIZE[1]}")


if __name__ == "__main__":
    main()
