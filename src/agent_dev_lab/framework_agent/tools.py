from uuid import UUID

from psycopg_pool import AsyncConnectionPool

from agent_dev_lab.framework_agent.resume_tool import create_resume_tool
from agent_dev_lab.mcp_clients.career_client import load_career_mcp_tools
from agent_dev_lab.skills.tools import load_skill


async def load_agent_tools(
    pool: AsyncConnectionPool | None,
    user_id: UUID | None,
):
    """组装本次 Agent 调用可以使用的工具。"""

    mcp_tools = await load_career_mcp_tools()
    tools = []

    for mcp_tool in mcp_tools:
        tools.append(mcp_tool)

    resume_tool = create_resume_tool(
        pool=pool,
        user_id=user_id,
    )

    tools.append(resume_tool)
    tools.append(load_skill)

    return tools