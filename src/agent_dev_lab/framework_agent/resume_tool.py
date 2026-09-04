from threading import Lock

from langchain_core.tools import tool

from agent_dev_lab.rag.retriever import create_retriever
from agent_dev_lab.rag.vector_store import load_vector_store

# langgraph 会用线程池并发执行多个工具调用，而 chromadb 的
# PersistentClient 并发创建是线程不安全的（会随机抛
# AttributeError/KeyError/ValueError）。所以在进程内只建一次
# retriever 并缓存复用，首次初始化用锁保护。
_lock = Lock()
_cached_retriever = None


def _get_retriever():
    global _cached_retriever

    if _cached_retriever is None:
        with _lock:
            if _cached_retriever is None:  #双重加锁
                vector_store = load_vector_store()
                _cached_retriever = create_retriever(vector_store)

    return _cached_retriever


@tool
def search_resume(query: str) -> str:
    """Search the user's resume for relevant experience, skills, education, and projects."""

    retriever = _get_retriever()

    documents = retriever.invoke(query)

    if not documents:
        return "No relevant resume information found."

    contents = [
        document.page_content
        for document in documents
    ]

    return "\n\n---\n\n".join(contents)