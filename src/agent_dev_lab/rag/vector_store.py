from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document

from agent_dev_lab.rag.embeddings import create_embeddings


PROJECT_ROOT = Path(__file__).resolve().parents[3]

CHROMA_DIR = (
    PROJECT_ROOT
    / "data"
    / "chroma"
)

COLLECTION_NAME = "resume"

def create_vector_store(
    documents: list[Document],
) -> Chroma:
    embeddings = create_embeddings()

    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(CHROMA_DIR), #把 Chroma 数据持久化保存到硬盘这个目录里。
    )

    return vector_store

def load_vector_store() -> Chroma:
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=create_embeddings(),
        persist_directory=str(CHROMA_DIR),
    )