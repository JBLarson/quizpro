import io
from docx import Document

# ----------------------------------------------------------------------------
# Function: docx_to_text
# Purpose: Extract all text from a DOCX file-like object and return as a string
# Inputs:
#   - file: a FileStorage or file-like object representing the uploaded .docx
# Outputs:
#   - A single string containing the concatenated text of all paragraphs
# ----------------------------------------------------------------------------
def docx_to_text(file):
    # Read file bytes
    data = file.read()
    # Reset file pointer
    try:
        file.seek(0)
    except Exception:
        pass
    # Load DOCX document from bytes
    doc = Document(io.BytesIO(data))
    texts = []
    for para in doc.paragraphs:
        if para.text and para.text.strip():
            texts.append(para.text.strip())
    return "\n\n".join(texts) 