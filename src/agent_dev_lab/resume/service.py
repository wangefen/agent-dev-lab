from pathlib import Path

from langchain_core.documents import Document

from agent_dev_lab.rag.loader import load_pdf
from agent_dev_lab.rag.splitter import split_documents


def split_resume(pdf_path: Path) -> list[Document]:
    pages = load_pdf(pdf_path)

    pages_with_text = []

    for page in pages:
        if page.page_content.strip():
            pages_with_text.append(page)

    if not pages_with_text:
        raise ValueError("PDF 没有可提取的文字，扫描件需要先做 OCR。")

    return split_documents(pages_with_text)