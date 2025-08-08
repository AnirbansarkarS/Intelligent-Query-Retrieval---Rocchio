import requests
import pdfplumber
import io
from docx import Document
from email import policy
from email.parser import BytesParser
from email.message import EmailMessage

import re
import hashlib
import os

def sanitize_filename(name: str) -> str:
    # Remove illegal Windows characters
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def generate_unique_id(filename: str) -> str:
    # Separate base and extension
    base, _ = os.path.splitext(filename)
    base = sanitize_filename(base)
    
    # Create hash from original filename for uniqueness
    hash_part = hashlib.sha256(filename.encode()).hexdigest()[:8]  # short hash
    return f"{base}_{hash_part}"

def download_file(url: str) -> tuple[bytes, str, str]:
    response = requests.get(url)
    response.raise_for_status()
    
    content_type = response.headers.get("Content-Type", "").lower()
    content_disposition = response.headers.get("Content-Disposition", "")
    
    # Default: last part of the URL
    filename = url.split("/")[-1]
    
    # If Content-Disposition has filename, use it
    if "filename" in content_disposition.lower():
        match = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^\";]+)"?', content_disposition)
        if match:
            filename = match.group(1)
    
    # Generate Windows-safe, unique ID
    unique_id = generate_unique_id(filename)
    
    return response.content, content_type, unique_id



def parse_document(url: str):
    file_bytes, content_type , name= download_file(url)

    if "pdf" in content_type:
        return name, parse_pdf(file_bytes)
    elif "wordprocessingml" in content_type or "docx" in content_type:
        return name, parse_docx(file_bytes)
    elif "message/rfc822" in content_type or "eml" in content_type:
        return name, parse_eml(file_bytes)
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
