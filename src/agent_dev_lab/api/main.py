import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from langgraph.checkpoint.postgres.aio import (
    AsyncPostgresSaver,
)
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from pydantic import BaseModel

from agent_dev_lab.config import DATABASE_URL
from agent_dev_lab.framework_agent.agent import (
    arun_career_agent,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)

logger = logging.getLogger(__name__)


# PostgreSQL 连接池。
#
# open=False：
# 创建对象时先不连接数据库，
# 等 FastAPI 启动时在 lifespan 中统一打开。
#
# min_size=1：
# 至少保持 1 个数据库连接。
#
# max_size=5：
# 最多允许同时维护 5 个数据库连接。
pool = AsyncConnectionPool(
    conninfo=DATABASE_URL,
    min_size=1,
    max_size=5,
    open=False,
    kwargs={
        # LangGraph PostgreSQL Checkpointer
        # 需要连接处于 autocommit 模式。
        "autocommit": True,

        # 禁用 prepared statement 缓存，
        # 避免某些 PostgreSQL / 连接池环境下
        # prepared statement 冲突。
        "prepare_threshold": 0,

        # AsyncPostgresSaver 读取查询结果时，
        # 需要字典形式的数据行。
        "row_factory": dict_row,
    },
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    管理整个 FastAPI 服务生命周期中的共享资源。

    yield 之前：
        FastAPI 启动阶段

    yield 之后：
        FastAPI 关闭阶段
    """

    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not configured."
        )

    # FastAPI 启动时打开 PostgreSQL 连接池。
    await pool.open()

    # 等待 min_size 个数据库连接真正建立完成。
    await pool.wait()

    # AsyncPostgresSaver 不再自己创建数据库连接，
    # 而是直接复用整个 FastAPI 服务共享的连接池。
    app.state.checkpointer = AsyncPostgresSaver(
        pool
    )

    logger.info(
        "PostgreSQL connection pool started."
    )

    try:
        # FastAPI 从这里开始正式提供 HTTP 服务。
        yield

    finally:
        # FastAPI 关闭时统一释放数据库连接池。
        await pool.close()

        logger.info(
            "PostgreSQL connection pool closed."
        )


app = FastAPI(
    title="Career Agent API",
    version="1.0",
    lifespan=lifespan,
)


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"


class ChatResponse(BaseModel):
    answer: str


@app.post(
    "/chat",
    response_model=ChatResponse,
)
async def chat(payload: ChatRequest, request: Request,) -> ChatResponse:
    # 从 FastAPI 应用状态中拿到启动时创建好的
    # PostgreSQL Checkpointer。
    #request 是 FastAPI 自动注入的当前 HTTP 请求对象；
    # 你没有创建它，因为HTTP请求到达时FastAPI已经帮你创建并传给chat() 了。
    checkpointer = (
        request.app.state.checkpointer
    )

    # Agent 不再负责创建 PostgreSQL 连接，
    # 直接使用 FastAPI 提供的共享 Checkpointer。
    answer = await arun_career_agent(
        prompt=payload.message,
        thread_id=payload.thread_id,
        checkpointer=checkpointer,
    )

    return ChatResponse(
        answer=answer
    )