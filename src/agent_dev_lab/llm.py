import json

from openai import OpenAI

from agent_dev_lab.config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
)
from agent_dev_lab.schemas import TaskIntent

JOB_SEARCH_TOOL = {
    "type":"function",
    "function": {
        "name":"search_jobs",
        "description": (
            "Search for job openings by city "
            "and keyword."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The target city.",
                },
                "keyword": {
                    "type": "string",
                    "description": "The job keyword.",
                },
            },
            "required": [
                "city",
                "keyword",
            ],
        },
    },
}

COMPANY_INFO_TOOL = {
    "type": "function",
    "function": {
        "name": "get_company_info",
        "description": (
            "Get basic information about "
            "a company."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "company": {
                    "type": "string",
                    "description": (
                        "The company name."
                    ),
                },
            },
            "required": [
                "company",
            ],
        },
    },
}

AGENT_TOOLS = [
    JOB_SEARCH_TOOL,
    COMPANY_INFO_TOOL,
]

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

def analyze_intent(prompt: str) -> TaskIntent:
    client = create_client()

    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Analyze the user's request. "
                    "Return JSON containing exactly these fields: "
                    "intent, needs_tool, reason."
                ),
            },
            {
                "role":"user",
                "content":prompt,
            },
        ],
        #如果不写则默认普通文本输出模式
        response_format={
            "type":"json_object",
        },
        extra_body={
            "thinking": {
                "type": "disabled",
            }
        },
    )

    #这里得到的content其实是JSON 格式的字符串
    content = response.choices[0].message.content

    if content is None:
        raise RuntimeError(
            "The model returned an empty response."
        )
    #将data转化为dict格式
    data = json.loads(content)

    #model_validate：Pydantic 再检查是否每个字段都对应上了
    return TaskIntent.model_validate(data)

def ask_with_tools(prompt: str):
    client = create_client()

    response = client.chat.completions.create(
        model = DEEPSEEK_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a career assistant. "
                    "Use tools when external job "
                    "information is needed."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        tools=[
            JOB_SEARCH_TOOL,
        ],
        tool_choice="auto",
        extra_body={
            "thinking": {
                "type": "disabled",
            }
        },
    )
    #message包含：message role, content, tool_calls, 其他一些字段
    return response.choices[0].message