"""
Extract text and apply FA formatting rules for ODT and DOCX documents

Usage: python fa_formatter.py <input_file>
Supported input formats:
- Plain text (.txt)
- OpenDocument Text (.odt)
- Microsoft Word (.docx) [Requires python-docx library]
"""

import sys
import os
import chardet
from odf.opendocument import load
from odf.text import P, H
from odf.element import Element

# Optional import: python-docx for processing Microsoft Word (.docx) files.
try:
    from docx import Document as DocxDocument
except Exception:
    DocxDocument = None

fa_replacement_rules = {
    "starting_text": "",
    "ending_text": "",
    "replacements": {
        ("\t", ""),
        ("\n", "\n\n"),
    },
    "title_tag": ("[h1]", "[/h1]"),
    "sub_title_tag": ("[h2]", "[/h2]"),
    "sup_tag": ("[sup]", "[/sup]"),
    "sub_tag": ("[sub]", "[/sub]"),
    "italic_tag": ("[i]", "[/i]"),
    "bold_tag": ("[b]", "[/b]")
}

def clean_text(text):
    # Replaces smart quotes, ellipses, and dashes with their ASCII equivalents
    replacements = {
        '“': '"',
        '”': '"',
        '‘': "'",
        '’': "'",
        '…': '...',
        '–': '-',
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


curr_replacement_rule = fa_replacement_rules

def detect_encoding(file_path):
    try:
        with open(file_path, 'rb') as file:
            raw_bytes = file.read()
        result = chardet.detect(raw_bytes)
        return result['encoding']
    except Exception as e:
        print(f"Error detecting encoding: {e}")
        return 'utf-8'  # Provide a default encoding

def read_text_from_file(file_path):
    try:
        encoding = detect_encoding(file_path)
        with open(file_path, 'r', encoding=encoding) as file:
            return file.read()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except UnicodeDecodeError:
        print(f"Error decoding file: {file_path}. Try using a different encoding.")
        return None

def write_text_to_file(original_file_path, modified_text, output_file_suffix=" (FurAffinity Compatible)"):
    try:
        # Get the directory and base filename from the original file path
        directory, filename = os.path.split(original_file_path)
        
        # Create the output file path by appending the suffix
        output_file_path = os.path.join(directory, f"{os.path.splitext(filename)[0]}{output_file_suffix}.txt")

        # Detect the encoding of the original file
        original_encoding = detect_encoding(original_file_path) or 'utf-8'

        with open(output_file_path, 'w', encoding=original_encoding) as file:
            file.write(modified_text)

        print("Modified text written to:", output_file_path)
        return output_file_path

    except Exception as e:
        print(f"Error writing to file: {e}")
        return None

def process_odt(file_path):
    try:
        doc = load(file_path)
        paragraphs = []

        for elem in doc.getElementsByType(P) + doc.getElementsByType(H):
            para_text = ""

            for node in elem.childNodes:
                # If it's a styled span
                if isinstance(node, Element) and node.tagName == 'text:span':
                    span_text = ""
                    for subnode in node.childNodes:
                        if hasattr(subnode, 'data'):
                            span_text += subnode.data
                    
                    # Safe access to style attribute
                    style = None
                    try:
                        style = node.getAttribute(('text', 'style-name'))
                    except Exception:
                        pass  # No style

                    # Debug output if needed
                    # print(f"SPAN: '{span_text}' | STYLE: {style}")

                    if style:
                        if 'Bold' in style:
                            span_text = f"{curr_replacement_rule['bold_tag'][0]}{span_text}{curr_replacement_rule['bold_tag'][1]}"
                        if 'Italic' in style:
                            span_text = f"{curr_replacement_rule['italic_tag'][0]}{span_text}{curr_replacement_rule['italic_tag'][1]}"
                    
                    para_text += span_text

                # Plain text node
                elif hasattr(node, 'data'):
                    para_text += node.data

            paragraphs.append(para_text + "\n")

        return ''.join(paragraphs)

    except Exception as e:
        print(f"Error processing .odt file: {e}")
        return ""


def process_docx(file_path):
    """
    Convert DOCX content to text extracting inline formatting and headings.
    Uses tagging from `curr_replacement_rule` to render bold/italic/sub/sup tags
    and map Heading 1/Heading 2 to title/subtitle tags.
    """
    if DocxDocument is None:
        print("python-docx not installed. Can't process .docx files.")
        return ""
    try:
        doc = DocxDocument(file_path)
        paragraphs = []

        for para in doc.paragraphs:
            para_text = ""
            style_name = None
            try:
                style_name = para.style.name
            except Exception:
                style_name = None

            # Determine heading tags if the paragraph is a heading
            heading_start = heading_end = ""
            if style_name:
                if 'Heading 1' in style_name or 'Title' in style_name:
                    heading_start, heading_end = curr_replacement_rule['title_tag']
                elif 'Heading 2' in style_name:
                    heading_start, heading_end = curr_replacement_rule['sub_title_tag']

            # Iterate runs and apply inline formatting
            for run in para.runs:
                run_text = run.text or ""
                if getattr(run, 'bold', False):
                    run_text = f"{curr_replacement_rule['bold_tag'][0]}{run_text}{curr_replacement_rule['bold_tag'][1]}"
                if getattr(run, 'italic', False):
                    run_text = f"{curr_replacement_rule['italic_tag'][0]}{run_text}{curr_replacement_rule['italic_tag'][1]}"

                font = getattr(run, 'font', None)
                if font is not None:
                    if getattr(font, 'superscript', False):
                        run_text = f"{curr_replacement_rule['sup_tag'][0]}{run_text}{curr_replacement_rule['sup_tag'][1]}"
                    if getattr(font, 'subscript', False):
                        run_text = f"{curr_replacement_rule['sub_tag'][0]}{run_text}{curr_replacement_rule['sub_tag'][1]}"

                para_text += run_text

            if heading_start or heading_end:
                para_text = f"{heading_start}{para_text}{heading_end}"

            paragraphs.append(para_text + "\n")

        return ''.join(paragraphs)
    except Exception as e:
        print(f"Error processing .docx file: {e}")
        return ""

def perform_replacements(text, replacements):
    for replacement_pair in replacements:
        if len(replacement_pair) != 2:
            print("Invalid replacement pair:", replacement_pair)
            continue

        old_str, new_str = replacement_pair
        text = text.replace(old_str, new_str)

    return text

def save_to_txt(content, output_txt_path):
    with open(output_txt_path, 'w', encoding='utf-8') as txt_file:
        txt_file.write(content)

    print("Modified content saved to:", output_txt_path)

def ask_for_header():
    header_text = ""

    title = input("Title: ")
    sub_title = input("Subtitle: ")
    by = input("By: ")
    to = input("For: ")

    if title or sub_title or by or to:
        header_text = "[center]\n"
        if title:
            title_tag = curr_replacement_rule["title_tag"]
            header_text += f"{title_tag[0]}{title}{title_tag[1]}\n\n"
        if sub_title:
            sub_title_tag = curr_replacement_rule["sub_title_tag"]
            header_text += f"{sub_title_tag[0]}{sub_title}{sub_title_tag[1]}\n"
        if by:
            by_tag = curr_replacement_rule["sup_tag"]
            header_text += f"{by_tag[0]}By {by}{by_tag[1]}\n"
        if to:
            to_tag = curr_replacement_rule["sub_tag"]
            header_text += f"{to_tag[0]}For {to}{to_tag[1]}\n"
        header_text += "[/center]"
    
    return header_text

def ask_for_disclaimer():
    response = input("Add disclaimer? [Y/n] ").strip().lower()
    if response in ["", "y", "yes"]:
        return "\n\n[center]-----\n[b]DISCLAIMER[/b]\n\nThis story contains sexual acts performed without the consent of all involved parties. These acts are to remain fully in the realm of fiction and should [b]NEVER[/b] be replicated in real life under any circumstances. \n\nAlways play [b]safe[/b], [b]sane[/b] and [b]consensual[/b].\n\n-----[/center]"
    else:
        print("Skipping disclaimer.")
        return ""

# Example usage:
file_path = sys.argv[1]
input_text = None

lower_file = file_path.lower()
if lower_file.endswith(".odt"):
    input_text = process_odt(file_path)
elif lower_file.endswith(".docx"):
    input_text = process_docx(file_path)
else:
    input_text = read_text_from_file(file_path)

# If reading returned None (file missing or decode error), normalize to empty string
if input_text is None:
    print("Warning: No input content was read from the file; continuing with empty content.")
    input_text = ""

# Apply custom replacements
# Perform replacements
input_text = perform_replacements(input_text, curr_replacement_rule["replacements"])

# Remove leading spaces from each line
input_text = '\n'.join(line.lstrip() for line in input_text.split('\n'))

# Remove first three lines of the extracted content
input_text_lines = input_text.splitlines()
if len(input_text_lines) > 3:
    input_text = "\n".join(input_text_lines[3:])  # skip the first three lines

# Wrap with starting/ending text
input_text = curr_replacement_rule["starting_text"] + input_text + curr_replacement_rule["ending_text"]

# Add header on top
header_text = ask_for_header()

# Ask for disclaimer
disclaimer_text = ask_for_disclaimer()

# Combine all parts
input_text = header_text + disclaimer_text + input_text

# Clean smart characters, ellipses, dashes, etc.
input_text = clean_text(input_text)
output_file_path = write_text_to_file(file_path, input_text)

print("Wrote changes to file:", output_file_path)
