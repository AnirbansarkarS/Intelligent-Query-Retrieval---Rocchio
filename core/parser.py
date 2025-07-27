
import requests
import pdfplumber
import io
from docx import Document

def download_file(url: str) -> bytes:
    response = requests.get(url)
    response.raise_for_status()
    return response.content

def parse_document(url: str) -> str:
    if ".pdf" in url:
        return parse_pdf(url)
    elif ".docx" in url:
        return parse_docx(url)
    else:
        raise ValueError("Unsupported file format")

def parse_pdf(url: str) -> str:
    file_bytes = download_file(url)
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
    return text.strip()

def parse_docx(url: str) -> str:
    file_bytes = download_file(url)
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join([para.text for para in doc.paragraphs if para.text.strip()]).strip()