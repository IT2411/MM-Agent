import io
import csv
from pypdf import PdfReader
from docx import Document
from fastapi import UploadFile

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extracts text programmatically using pypdf."""
    pdf_file = io.BytesIO(file_bytes)
    reader = PdfReader(pdf_file)
    extracted_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            extracted_text.append(text)
    return "\n".join(extracted_text).strip()

def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extracts text from Word documents."""
    docx_file = io.BytesIO(file_bytes)
    doc = Document(docx_file)
    extracted_text = []
    for para in doc.paragraphs:
        if para.text.strip():
            extracted_text.append(para.text)
    return "\n".join(extracted_text).strip()

def extract_text_from_csv(file_bytes: bytes) -> str:
    """Formats CSV rows into a readable structured text dataset."""
    csv_file = io.StringIO(file_bytes.decode('utf-8', errors='ignore'))
    reader = csv.reader(csv_file)
    rows_text = []
    for row in reader:
        rows_text.append(" | ".join(row))
    return "\n".join(rows_text).strip()

async def extract_text_from_file(file: UploadFile) -> str:
    """Dispatches the correct extractor based on the file extension."""
    content = await file.read()
    filename = file.filename.lower()

    if filename.endswith(".pdf"):
        return extract_text_from_pdf(content)
    elif filename.endswith(".docx"):
        return extract_text_from_docx(content)
    elif filename.endswith(".csv"):
        return extract_text_from_csv(content)
    return ""