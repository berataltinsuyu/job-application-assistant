from io import BytesIO

from docx import Document
from fastapi import HTTPException, UploadFile
from pypdf import PdfReader


ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}


async def extract_text_from_cv(cv_file: UploadFile) -> str:
    if cv_file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Sadece PDF veya DOCX formatında CV yükleyebilirsiniz."
        )

    file_bytes = await cv_file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Yüklenen CV dosyası boş görünüyor."
        )

    if cv_file.content_type == "application/pdf":
        text = extract_text_from_pdf(file_bytes)
    else:
        text = extract_text_from_docx(file_bytes)

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="CV dosyasından metin çıkarılamadı. Dosya taranmış görsel olabilir."
        )

    return text.strip()


def extract_text_from_pdf(file_bytes: bytes) -> str:
    pdf_reader = PdfReader(BytesIO(file_bytes))

    pages_text = []

    for page in pdf_reader.pages:
        page_text = page.extract_text()

        if page_text:
            pages_text.append(page_text)

    return "\n".join(pages_text)


def extract_text_from_docx(file_bytes: bytes) -> str:
    document = Document(BytesIO(file_bytes))

    paragraphs = []

    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            paragraphs.append(paragraph.text)

    return "\n".join(paragraphs)