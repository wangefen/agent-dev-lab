import asyncio

from langchain.agents import create_agent

from agent_dev_lab.framework_agent.model import (
    create_model,
)
from agent_dev_lab.framework_agent.tools import (
    load_agent_tools,
)

from langgraph.checkpoint.postgres.aio import (AsyncPostgresSaver)

from agent_dev_lab.config import DATABASE_URL


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
    checkpointer: AsyncPostgresSaver
) -> str:
    tools = await load_agent_tools()

    agent = create_agent(
        model=create_model(),
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
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