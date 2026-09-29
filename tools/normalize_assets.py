"""Normalize Water Panda sprites without distorting natural poses."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
CANVAS_SIZE = (180, 180)
GROUND_Y = 172
WALK_HEIGHT = 138


def alpha_bbox(image: Image.Image) -> tuple[int, int, int, int]:
    box = image.getchannel("A").getbbox()
    if box is None:
        raise ValueError("Sprite has no visible pixels")
    return box


def place_on_canvas(
    image: Image.Image,
    *,
    target_height: int | None = None,
) -> Image.Image:
    image = image.convert("RGBA")
    cropped = image.crop(alpha_bbox(image))
    if target_height is not None:
        scale = target_height / cropped.height
        width = max(1, round(cropped.width * scale))
        height = target_height
        if width > CANVAS_SIZE[0] - 8:
            scale = (CANVAS_SIZE[0] - 8) / cropped.width
            width = CANVAS_SIZE[0] - 8
            height = max(1, round(cropped.height * scale))
        cropped = cropped.resize((width, height), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    x = (CANVAS_SIZE[0] - cropped.width) // 2
    y = GROUND_Y - cropped.height
    canvas.alpha_composite(cropped, (x, y))
    alpha = canvas.getchannel("A").point(lambda value: 255 if value >= 92 else 0)
    canvas.putalpha(alpha)
    return canvas


def normalize_file(path: Path, target_height: int | None = None) -> None:
    with Image.open(path) as image:
        normalized = place_on_canvas(image, target_height=target_height)
    normalized.save(path, optimize=True)


def main() -> None:
    paths = sorted(ASSETS.glob("panda_*.png"))
    if not paths:
        raise SystemExit("No panda PNG assets found")
    for path in paths:
        target_height = WALK_HEIGHT if "panda_walk_" in path.name else None
        normalize_file(path, target_height=target_height)
    print(f"Normalized {len(paths)} sprites to {CANVAS_SIZE[0]}x{CANVAS_SIZE[1]}")


if __name__ == "__main__":
    main()
