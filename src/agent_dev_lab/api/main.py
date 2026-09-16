from fastapi import FastAPI
from openai.resources import ChatWithRawResponse
from pydantic import BaseModel
from typer import prompt

from agent_dev_lab.framework_agent.agent import (
    arun_career_agent,
)

app = FastAPI(
    title="Career Agent API",
    version="1.0",
)

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"

class ChatResponse(BaseModel):
    answer: str

@app.post(
    "/chat",
    response_model=ChatResponse, #告诉 FastAPI：这个接口返回的数据必须符合 ChatResponse 这个格式
)
async def chat(request: ChatRequest):
    print("========== CHAT ENTER ==========")
    answer = await arun_career_agent(
        prompt = request.message,
        thread_id=request.thread_id,
    )

    return ChatResponse(answer = answer)
