"""
会话模块的HTTP接口。
"""

from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException, status, Request
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel

from agent_dev_lab.auth.dependencies import (
    CurrentUser,
    DatabasePool,
)
from agent_dev_lab.conversation.repository import (
    create_conversation,
    list_conversations,
    get_conversation
)


router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


class ConversationResponse(BaseModel):
    """返回给前端的会话信息。"""

    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    """返回给前端的一条文本聊天消息。"""

    role: Literal["user", "assistant"]
    content: str


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_new_conversation(
    current_user: CurrentUser,
    pool: DatabasePool,
) -> ConversationResponse:
    """为当前登录用户创建一段新会话。"""

    # 后端生成新的会话编号。
    conversation_id = uuid4()

    # 用户ID从认证结果中获取，而不是让前端传入。
    row = await create_conversation(
        pool=pool,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )

    return ConversationResponse(
        id=row["id"],
        title=row["title"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )

@router.get("",response_model=list[ConversationResponse],)
async def get_conversations(
    current_user: CurrentUser,
    pool: DatabasePool,
) -> list[ConversationResponse]:
    """查询当前登录用户的会话列表。"""

    rows = await list_conversations(
        pool=pool,
        user_id=current_user.id,
    )

    conversations = []

    for row in rows:
        # 每读取一条数据库记录，就创建一个新的响应对象。
        con = ConversationResponse(
            id=row["id"],
            title=row["title"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

        # 将这个会话对象加入结果列表。
        conversations.append(con)

    return conversations

@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_conversation_messages(
    conversation_id: UUID,
    current_user: CurrentUser,
    pool: DatabasePool,
    request: Request,
) -> list[MessageResponse]:
    """检查会话归属，读取并返回当前用户的历史消息。"""
    # 数据库查询是异步函数，需要 await 才能得到查询结果。
    conversation = await get_conversation(pool, conversation_id, current_user.id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    # 读取时必须和 /chat 保存时使用完全相同的 thread_id。
    user_thread_id = (f"user:{current_user.id}:"
                      f"thread:{conversation_id}")

    # 使用应用启动时创建的共享 checkpointer。
    checkpointer = request.app.state.checkpointer

    # 4. 根据完整 thread_id 读取最近一次 checkpoint。
    checkpoint = await checkpointer.aget(
        {
            "configurable": {
                "thread_id": user_thread_id,
            }
        }
    )

    # 新会话还没有发过消息时，可能没有 checkpoint。
    if checkpoint is None:
        return []

    # 最新 checkpoint 的 channel_values 中保存 Agent 的状态。
    channel_values = checkpoint.get("channel_values", {})
    messages = channel_values.get("messages", [])
    result: list[MessageResponse] = []

    for message in messages:
        # 此版本只展示字符串内容；其他内容格式暂时跳过。
        if not isinstance(message.content, str):
            continue

        if isinstance(message, HumanMessage):
            # 用户消息转换为前端使用的 role 和 content。
            result.append(MessageResponse(role="user", content=message.content))
        elif isinstance(message, AIMessage):
            # 工具调用消息和空消息暂不展示在普通聊天区域。
            if message.tool_calls or not message.content.strip():
                continue
            result.append(MessageResponse(role="assistant", content=message.content))

    return result

