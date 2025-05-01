import io
from PyPDF2 import PdfReader

# ----------------------------------------------------------------------------
# Function: pdf_to_text
# Purpose: Extract all text from a PDF file-like object and return as a string
# Inputs:
#   - file: a FileStorage/file-like object representing the uploaded PDF
# Outputs:
#   - A single string containing the concatenated text of all pages
# ----------------------------------------------------------------------------
def pdf_to_text(file):
    # Read file bytes
    data = file.read()
    # Reset file pointer
    try:
        file.seek(0)
    except Exception:
        pass
    # Load PDF reader
    reader = PdfReader(io.BytesIO(data))
    texts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            texts.append(text)
    return "\n\n".join(texts) 