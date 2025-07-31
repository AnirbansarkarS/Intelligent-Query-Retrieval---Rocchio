import requests
import pdfplumber
import io
from docx import Document
from email import policy
from email.parser import BytesParser
from email.message import EmailMessage

def download_file(url: str) -> tuple[bytes, str]:
    response = requests.get(url)
    response.raise_for_status()
    content_type = response.headers.get("Content-Type", "").lower()
    return response.content, content_type

def parse_document(url: str) -> str:
    file_bytes, content_type = download_file(url)

    if "pdf" in content_type:
        return parse_pdf(file_bytes)
    elif "wordprocessingml" in content_type or "docx" in content_type:
        return parse_docx(file_bytes)
    elif "message/rfc822" in content_type or "eml" in content_type:
        return parse_eml(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {content_type}")

def parse_pdf(file_bytes: bytes) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
    return text.strip()

def parse_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join([para.text for para in doc.paragraphs if para.text.strip()]).strip()

def parse_eml(file_bytes: bytes) -> str:
    msg: EmailMessage = BytesParser(policy=policy.default).parsebytes(file_bytes)
    subject = msg.get("subject", "")
    sender = msg.get("from", "")
    recipient = msg.get("to", "")

    body = ""
    if msg.is_multipart():
        for part in msg.iter_parts():
            if part.get_content_type() == "text/plain":
                body += part.get_content()
    else:
        if msg.get_content_type() == "text/plain":
            body = msg.get_content()

    return f"Subject: {subject}\nFrom: {sender}\nTo: {recipient}\n\n{body.strip()}"
