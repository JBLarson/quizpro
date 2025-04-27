import zipfile
import xml.etree.ElementTree as ET

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