import zipfile
import xml.etree.ElementTree as ET
import json
import os
from extensions import db

def pptx_to_json(pptx_file):
    pptx_json = {
        "slides": []
    }

    with zipfile.ZipFile(pptx_file, 'r') as pptx:
        for filename in pptx.namelist():
            if filename.startswith('ppt/slides/slide') and filename.endswith('.xml'):
                slide_data = pptx.read(filename)
                slide_json = parse_slide(slide_data)
                pptx_json["slides"].append(slide_json)
    return pptx_json

def parse_slide(slide_data):
    slide_json = {
        "text": []
    }
    root = ET.fromstring(slide_data)

    for element in root.iter():
        if 't' in element.tag and element.text:
            slide_json["text"].append(element.text)

    return slide_json

filepath = ''

for file in os.listdir("../pptxfiles"):
    if file.endswith(".pptx"):
        filepath = os.path.join("../pptxfiles", file)

pptx_file = filepath
pptx_json = pptx_to_json(pptx_file)

def getJSON():
    return json.dumps(pptx_json, indent=2)