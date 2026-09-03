from langchain_openai import ChatOpenAI

from agent_dev_lab.config import (
    DEEPSEEK_MODEL,
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
)

def create_model() -> ChatOpenAI:
    if not DEEPSEEK_API_KEY:
        raise RuntimeError(
            "DEEPSEEK_API_KEY is not configured."
        )

    return ChatOpenAI(
        model=DEEPSEEK_MODEL,
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        temperature=0,
    )