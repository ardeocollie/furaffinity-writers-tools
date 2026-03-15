#!/usr/bin/env python3
"""Generate a thumbnail image with words overlaid on a background."""

import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

suffix_patterns = [
    "tion", "ing", "ed", "er", "est", "able", "ible", "ment",
    "ness", "ful", "less", "ous", "ive", "al", "ly", "ity",
    "ty", "ship", "dom", "ism", "ist", "ate", "ify"
]

def hyphenate_word(word: str, max_width: int, font, is_last_line: bool = True) -> list[str]:
    """Split a word into hyphenated lines that fit within max_width.

    Handles multi-word inputs by treating the space as a literal character.
    is_last_line: If True, don't add trailing hyphen to the last line.
    """
    # If the whole thing fits, return as-is
    if font.getbbox(f"• {word}")[2] <= max_width:
        return [f"• {word}"]

    # Check if this is a multi-word input (contains a space)
    if " " in word:
        parts = word.split(" ", 1)
        first_word = parts[0]~
        second_word = parts[1]

        # Check if just the first word fits
        if font.getbbox(f"• {first_word}")[2] <= max_width:
            # First word fits, put second word on next line without bullet
            return [f"• {first_word}", second_word]

        # First word doesn't fit, try to hyphenate the first word
        for i in range(len(first_word) - 3, 0, -1):
            potential_suffix = first_word[i:]
            for pattern in suffix_patterns:
                if potential_suffix.startswith(pattern):
                    prefix = first_word[:i]
                    if font.getbbox(f"• {prefix}")[2] <= max_width:
                        if is_last_line:
                            return [f"• {prefix}-", f"{potential_suffix} {second_word}"]
                        return [f"• {prefix}-", f"{potential_suffix} {second_word}"]

        # Can't hyphenate first word nicely, put first word alone and second word on next line
        return [f"• {first_word}-", second_word]

    for i in range(len(word) - 3, 0, -1):
        potential_suffix = word[i:]
        # Check if the suffix matches any known hyphenation pattern
        for pattern in suffix_patterns:
            if potential_suffix.startswith(pattern):
                prefix = word[:i]
                if font.getbbox(f"• {prefix}")[2] <= max_width:
                    if is_last_line:
                        return [f"• {prefix}-", potential_suffix]
                    return [f"• {prefix}-", f"{potential_suffix}"]

    # No good hyphenation point found, split in half
    mid = len(word) // 2
    return [f"• {word[:mid]}-", word[mid:]]


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


def get_words_from_user(words: list[str] | None = None) -> list[str]:
    """Get words from command-line argument or user input."""
    if words is not None:
        return words
    user_input = input("Enter words separated by commas: ")
    return [word.strip() for word in user_input.split(",") if word.strip()]


def find_fitting_font_size(texts: list[str], max_width: int, font_path: str) -> int:
    """Find the largest font size that fits all texts within max_width."""
    # Use smaller font size for 6 words
    if len(texts) == 6:
        return 56

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
    draw = ImageDraw.Draw(background)

    custom_font_path = find_font_in_directory(FONTS_DIR)
    font = ImageFont.load_default()
    font_size = 24
    if custom_font_path:
        font_size = find_fitting_font_size(words, THUMBNAIL_SIZE - 80, str(custom_font_path))
        font = ImageFont.truetype(str(custom_font_path), font_size)

    margin_left = 45
    margin_right = 45
    max_lines = 6
    line_height = font_size + 12
    max_text_width = THUMBNAIL_SIZE - margin_left - margin_right

    # Estimate total height accounting for word wrapping and hyphenation
    estimated_height = 0
    for word in words[:max_lines]:
        hyphenated = hyphenate_word(word, max_text_width, font)
        estimated_height += len(hyphenated) * line_height

    start_y = (THUMBNAIL_SIZE - estimated_height) // 2

    y = start_y
    for word in words[:max_lines]:
        # Always hyphenate long words (even if they might fit)
        hyphenated = hyphenate_word(word, max_text_width, font)

        # Draw each part on its own line
        for part in hyphenated:
            draw.text((margin_left, y), part, fill=(255, 255, 255), font=font)
            y += line_height

    return background


def main():
    """Main entry point."""
    # Check for command-line argument
    words = None
    if len(sys.argv) > 1:
        words = [w.strip() for w in sys.argv[1].split(",") if w.strip()]

    if words is None:
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
