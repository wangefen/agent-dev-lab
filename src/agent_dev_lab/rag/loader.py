from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document


def load_pdf(path: str | Path) -> list[Document]:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Document not found: {path}"
        )

    loader = PyPDFLoader(str(path))

    return loader.load()