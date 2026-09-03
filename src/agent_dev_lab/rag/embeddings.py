from langchain_openai import OpenAIEmbeddings

from agent_dev_lab.config import (
    DEEPSEEK_API_KEY,
    EMBEDDING_MODEL,
    EMBEDDING_BASE_URL
)

def create_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=DEEPSEEK_API_KEY,
        base_url=EMBEDDING_BASE_URL,
        check_embedding_ctx_length=False,
    )