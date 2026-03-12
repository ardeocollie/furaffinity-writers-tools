#!/usr/bin/env python3
"""Generate a thumbnail image with words overlaid on a background."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent

THUMBNAIL_SIZE = 500
BACKGROUND_PATH = PROJECT_ROOT / "assets" / "images" / "thumbnail_background.png"
FONTS_DIR = PROJECT_ROOT / "assets" / "fonts"
OUTPUT_PATH = PROJECT_ROOT / "output" / "thumbnail.png"


def find_font_in_directory(font_dir: Path) -> Path | None:
    """Find a font file (.otf or .ttf) in the specified directory."""
    font_extensions = {".otf", ".ttf"}
    for font_file in font_dir.iterdir():
        if font_file.suffix.lower() in font_extensions:
            return font_file
    return None


def get_words_from_user() -> list[str]:
    """Ask user for comma-separated words."""
    user_input = input("Enter words separated by commas: ")
    return [word.strip() for word in user_input.split(",") if word.strip()]


def find_fitting_font_size(texts: list[str], max_width: int, font_path: str) -> int:
    """Find the largest font size that fits all texts within max_width."""
    font_size = 72
    while font_size > 0:
        try:
            font = ImageFont.truetype(font_path, font_size)
            max_text_width = max(font.getbbox(text)[2] for text in texts)
            if max_text_width <= max_width:
                return font_size
            font_size -= 1
        except OSError:
            return font_size
    return 12


def create_thumbnail(words: list[str]) -> Image.Image:
    """Create a thumbnail with words overlaid on the background."""
    background = Image.open(BACKGROUND_PATH)
    background = background.resize((THUMBNAIL_SIZE, THUMBNAIL_SIZE), Image.LANCZOS)
    if background.mode == "RGBA":
        background = background.convert("RGB")
    background = background.point(lambda p: p // 2)
    draw = ImageDraw.Draw(background)

    custom_font_path = find_font_in_directory(FONTS_DIR)
    font = ImageFont.load_default()
    font_size = 24
    if custom_font_path:
        font_size = find_fitting_font_size(words, THUMBNAIL_SIZE - 80, str(custom_font_path))
        font = ImageFont.truetype(str(custom_font_path), font_size)

    margin_left = 40
    margin_right = 40
    max_lines = 6
    line_height = font_size + 7
    max_text_width = THUMBNAIL_SIZE - margin_left - margin_right
    total_text_height = min(len(words), max_lines) * line_height
    start_y = (THUMBNAIL_SIZE - total_text_height) // 2

    for i, word in enumerate(words[:max_lines]):
        formatted_word = f"• {word}"
        bbox = font.getbbox(formatted_word)
        text_width = bbox[2]
        if text_width > max_text_width:
            words_per_line = max(1, len(formatted_word) // 2)
            truncated = formatted_word[:words_per_line] + "\u2010"
            draw.text((margin_left, start_y + (i * line_height)), truncated, fill=(255, 255, 255), font=font)
        else:
            draw.text((margin_left, start_y + (i * line_height)), formatted_word, fill=(255, 255, 255), font=font)


def main():
    """Main entry point."""
    words = get_words_from_user()

    if not words:
        print("No words provided.")
        return

    # Ensure output directory exists
    import os
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    try:
        thumbnail = create_thumbnail(words)
        thumbnail.save(OUTPUT_PATH)
        print(f"Thumbnail saved to {OUTPUT_PATH}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
