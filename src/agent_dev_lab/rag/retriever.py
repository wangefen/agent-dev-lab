from huggingface_hub import search_spaces
from langchain_chroma import Chroma

def create_retriever(vector_store: Chroma):
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 4, #每次检索返回最相关的 4 个 Document
        },
    )