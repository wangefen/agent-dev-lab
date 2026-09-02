
from openai import OpenAI

from agent_dev_lab.config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
)


def create_client() -> OpenAI:
    if not DEEPSEEK_API_KEY:
        raise RuntimeError(
        "DEEPSEEK_API_KEY is not configured."
        )

    return OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
    )

def ask_llm(prompt: str) -> str:
    client = create_client()

    #向一个兼容 OpenAI Chat Completions 格式的大模型服务器发送一次“聊天生成请求”，
    #然后拿到模型返回结果。
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages = [
            {
                "role": "system",
                "content":"You are a helpful AI assistant.",
            },
            {
            "role":"user",
                "content":prompt,
            },
        ],
        #extra_body是 OpenAI Python SDK 提供的一个“额外请求体参数入口”
        #比如说这里deepseek就需要额外的参数thinking
        extra_body={
        "thinking":{
            "type":"disabled",
            }
        },
    )

    content = response.choices[0].message.content

    if content is None:
        raise  RuntimeError(
        "The model returned an empty response."
    )

    return content