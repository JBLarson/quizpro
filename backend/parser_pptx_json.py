# backend/parser_pptx_json.py
# Module to convert a .pptx file into a structured JSON format.
# Uses Python's built-in zipfile and xml.etree for low-level PPTX parsing.

import zipfile
import xml.etree.ElementTree as ET

# ------------------------------------------------------------------------------
# Function: pptx_to_json
# Purpose: Read the uploaded PPTX file, extract slide XML, and convert each slide to JSON.
# Inputs:
#   - pptx_file: a FileStorage or file-like object representing the uploaded .pptx
# Process:
#   - Open PPTX as a zip archive
#   - Iterate through all files in the archive
#   - Identify slide XML files by path: 'ppt/slides/slideN.xml'
#   - Parse each slide XML and extract its text content
# Outputs:
#   - A dict with a 'slides' key containing a list of slide_json objects
# ------------------------------------------------------------------------------
def pptx_to_json(pptx_file):
    pptx_json = {"slides": []}

    # Open PPTX package as zip to access individual slide XML
    with zipfile.ZipFile(pptx_file, 'r') as pptx:
        for filename in pptx.namelist():
            # Select slide XML files only (ignoring notes, media, etc.)
            if filename.startswith('ppt/slides/slide') and filename.endswith('.xml'):
                slide_data = pptx.read(filename)  # Binary XML data
                slide_json = parse_slide(slide_data)
                pptx_json["slides"].append(slide_json)
    return pptx_json

# ------------------------------------------------------------------------------
# Function: parse_slide
# Purpose: Extract all text elements from a slide's XML data.
# Inputs:
#   - slide_data: raw XML bytes for one slide
# Process:
#   - Parse XML into an ElementTree
#   - Iterate through all elements; detect text tags by tag suffix 't'
#   - Collect non-empty element text values
# Outputs:
#   - A dict with 'text': a list of strings for each text element
# ------------------------------------------------------------------------------
def parse_slide(slide_data):
    slide_json = {"text": []}
    root = ET.fromstring(slide_data)  # Parse XML from bytes

    # Walk through every element in the slide XML
    for element in root.iter():
        # In the PPTX namespace, text tags end with '}t'
        if 't' in element.tag and element.text:
            slide_json["text"].append(element.text)

    return slide_json