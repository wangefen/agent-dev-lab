from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document

from agent_dev_lab.rag.embeddings import (
    create_embeddings,
)

CHROMA_DIR = Path("data/chroma")


def create_vector_store(documents:list[Document]) -> Chroma:
    embeddings = create_embeddings()

    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name="resume",
        persist_directory=str(CHROMA_DIR)   #把 Chroma 数据持久化保存到硬盘这个目录里。
    )

    return vector_store