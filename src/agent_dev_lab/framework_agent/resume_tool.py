from langchain_core.tools import tool

from agent_dev_lab.rag.retriever import create_retriever
from agent_dev_lab.rag.vector_store import load_vector_store


@tool
def search_resume(query: str) -> str:
    """Search the user's resume for relevant experience, skills, education, and projects."""

    vector_store = load_vector_store()

    retriever = create_retriever(vector_store)

    documents = retriever.invoke(query)

    if not documents:
        return "No relevant resume information found."

    contents = [
        document.page_content
        for document in documents
    ]

    return "\n\n---\n\n".join(contents)