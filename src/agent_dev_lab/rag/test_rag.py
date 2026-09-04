from pathlib import Path

from agent_dev_lab.rag.loader import load_pdf
from agent_dev_lab.rag.splitter import split_documents
from agent_dev_lab.rag.vector_store import (
    create_vector_store,
)
from agent_dev_lab.rag.retriever import (
    create_retriever,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

RESUME_PATH = (
    PROJECT_ROOT
    / "data"
    / "documents"
    / "resume2.pdf"
)

def main() -> None:
    documents = load_pdf(RESUME_PATH)

    print(
        f"Loaded documents: {len(documents)}"
    )

    chunks = split_documents(documents)

    print(
        f"Created chunks: {len(chunks)}"
    )

    vector_store = create_vector_store(
        chunks
    )

    retriever = create_retriever(
        vector_store
    )

    query = "我的项目经历中有哪些 Python 相关经验？"

    results = retriever.invoke(query)

    print("\n===== Retrieval Results =====\n")

    for index, document in enumerate(
        results,
        start=1,
    ):
        print(f"[{index}]")
        print(document.page_content)
        print(
            f"metadata: {document.metadata}"
        )
        print()


if __name__ == "__main__":
    main()