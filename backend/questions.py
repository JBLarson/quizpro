import json

def load_json(filename):
	with open(filename, 'r', encoding='utf-8') as f:
		return json.load(f)


def extract_text_from_pptx(parsed_pptx):
	text_blocks = []

	for slide in parsed_pptx.get('slides', []):
		texts = slide.get('text', [])
		for line in texts:
			line = line.strip()
			if line:
				text_blocks.append(line)

	return '\n\n---\n\n'.join(text_blocks)


pptx_json = load_json("json_files/powerpoint.json")
pptx_text = extract_text_from_pptx(pptx_json)

print(f"\n\n{pptx_text}")