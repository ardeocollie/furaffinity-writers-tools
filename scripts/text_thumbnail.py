#!/usr/bin/env python3
"""Generate a thumbnail image with words overlaid on a background."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent

THUMBNAIL_SIZE = 500
BACKGROUND_PATH = PROJECT_ROOT / "assets" / "images" / "thumbnail_background.png"
OUTPUT_PATH = PROJECT_ROOT / "output" / "thumbnail.png"


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
    # Load and resize background
    background = Image.open(BACKGROUND_PATH)
    background = background.resize((THUMBNAIL_SIZE, THUMBNAIL_SIZE), Image.LANCZOS)

    # Darken the background by 50%
    # Convert to RGB if needed (to handle RGBA images properly)
    if background.mode == "RGBA":
        background = background.convert("RGB")
    background = background.point(lambda p: p // 2)

    # Create draw object
    draw = ImageDraw.Draw(background)

    # Try to use a system font, fall back to default
    font_paths = [
        "/System/fonts/Times New Roman.ttf",  # macOS
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",  # Linux
        "C:/Windows/Fonts/times.ttf",  # Windows
    ]

    font = ImageFont.load_default()
    for font_path in font_paths:
        try:
            font = ImageFont.truetype(font_path, 12)
            break
        except OSError:
            continue

    # Find fitting font size
    max_width = THUMBNAIL_SIZE - 20  # Leave 10px padding on each side
    font_size = find_fitting_font_size(words, max_width, font_path)
    font = ImageFont.truetype(font_path, font_size) if font_path else font

    # Calculate text positioning
    text_widths = [font.getbbox(word)[2] for word in words]
    total_width = max(text_widths)
    start_x = (THUMBNAIL_SIZE - total_width) // 2

    # Center text vertically
    line_height = font_size + 5
    total_text_height = len(words) * line_height
    start_y = (THUMBNAIL_SIZE - total_text_height) // 2 + line_height

    # Draw each word in white
    for word in words:
        bbox = font.getbbox(word)
        text_width = bbox[2]
        x = start_x + (total_width - text_width) // 2
        draw.text((x, start_y), word, fill=(255, 255, 255), font=font)
        start_y += line_height

    return background


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
