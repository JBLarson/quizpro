# backend/questions.py
# Helper module for loading and processing quiz content from JSON data.

import json

# ------------------------------------------------------------------------------
# Function: load_json
# Purpose: Read a JSON file from disk and parse it into a Python object.
# Inputs:
#   - filename: path to the .json file to load
# Returns:
#   - Parsed JSON data (typically a dict or list)
# ------------------------------------------------------------------------------
def load_json(filename):
    """
    Load JSON data from the specified filename using UTF-8 encoding.
    """
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)


# ------------------------------------------------------------------------------
# Function: extract_text_from_pptx
# Purpose: Flatten the text content from parsed PPTX JSON into a single string.
# Inputs:
#   - parsed_pptx: a dict containing 'slides', each with a 'text' list of strings
# Process:
#   - Iterate through each slide and each line of text
#   - Strip whitespace and filter out empty lines
#   - Append cleaned lines to a list
# Outputs:
#   - A single string with slide text joined by markdown-style separators
# ------------------------------------------------------------------------------
def extract_text_from_pptx(parsed_pptx):
    text_blocks = []

    # Iterate over slides (each slide is a dict with key 'text')
    for slide in parsed_pptx.get('slides', []):
        texts = slide.get('text', [])
        for line in texts:
            line = line.strip()  # Remove leading/trailing whitespace
            if line:  # Only keep non-empty lines
                text_blocks.append(line)

    # Join all text segments with a clear separator for readability
    return '\n\n---\n\n'.join(text_blocks)

# (Optional) Example usage commented out:
# pptx_json = load_json("json_files/powerpoint.json")
# pptx_text = extract_text_from_pptx(pptx_json)
# print(pptx_text)