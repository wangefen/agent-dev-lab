import asyncio
from uuid import UUID

from langchain.agents import create_agent

from agent_dev_lab.skills.tools import (
    skill_registry,
)

from agent_dev_lab.framework_agent.model import (
    create_model,
)
from agent_dev_lab.framework_agent.tools import (
    load_agent_tools,
)

from langgraph.checkpoint.postgres.aio import (AsyncPostgresSaver)

from agent_dev_lab.config import DATABASE_URL

from psycopg_pool import AsyncConnectionPool


SYSTEM_PROMPT = """
You are a career research assistant.

You can use:

1. search_jobs:
   Search for current job opportunities
   by city and keyword.

2. search_resume:
   Search the user's resume for skills,
   education, projects, and experience.

If the user's question can be answered
directly from conversation history,
do not call tools unnecessarily.

Use search_jobs when current job
information is needed.

Use search_resume when resume information
is needed.

For job-fit analysis, use both tools
when appropriate.

Never invent job information or
resume information.
"""




async def arun_career_agent(
    prompt: str,
    thread_id: str,
    checkpointer: AsyncPostgresSaver,
    pool: AsyncConnectionPool | None=None,
    user_id: UUID | None=None
) -> str:
    tools = await load_agent_tools(pool, user_id)

    # 获取可用Skill的名称和简介。
    # 第一次调用时，注册表会扫描项目的skills目录。
    skill_catalog = skill_registry.render_catalog()

    # 在原有系统提示词后面加入Skill目录和使用规则。
    # 完整的Skill内容由Agent需要时调用load_skill获取。
    system_prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        "Available Skills:\n"
        f"{skill_catalog}\n\n"
        "If the user's request matches an available Skill, "
        "call load_skill with the exact Skill name before "
        "performing the task. Follow the loaded instructions."
    )

    agent = create_agent(
        model=create_model(),
        tools=tools,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
    )



    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        },
        config={
            "configurable": {
                "thread_id": thread_id,
            }
        },
    )

    # 临时观察Agent调用了哪些工具。
    # result["messages"]可能包含当前thread的历史消息，
    # 所以这里也可能打印之前对话中的工具调用。
    for message in result["messages"]:
        tool_calls = getattr(
            message,
            "tool_calls",
            [],
        )

        for tool_call in tool_calls:
            print(
                "Agent调用工具：",
                tool_call["name"],
            )

    return result["messages"][-1].content

async def _run_with_temp_checkpointer(prompt: str, thread_id :str) -> str:
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured.")

    async with AsyncPostgresSaver.from_conn_string(DATABASE_URL) as checkpointer:
        return await arun_career_agent(
            prompt=prompt,
            thread_id=thread_id,
            checkpointer=checkpointer
        )

def run_career_agent(
    prompt: str,
    thread_id: str,
) -> str:
    return asyncio.run(
        _run_with_temp_checkpointer(
            prompt=prompt,
            thread_id=thread_id,
        )
    )