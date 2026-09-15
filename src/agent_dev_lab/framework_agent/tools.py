from agent_dev_lab.framework_agent.resume_tool import (
    search_resume,
)
from agent_dev_lab.mcp_clients.career_client import (
    load_career_mcp_tools,
)


async def load_agent_tools():
    mcp_tools = await load_career_mcp_tools()

    return [
        *mcp_tools, #Python 的解包
        search_resume,
    ]