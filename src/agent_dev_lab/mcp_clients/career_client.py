import sys

from langchain_mcp_adapters.client import (
    MultiServerMCPClient,
)

def create_career_mcp_client() -> MultiServerMCPClient:
    return MultiServerMCPClient(
        {
            "career":{
                "transport": "stdio",
                "command": sys.executable,
                "args":[
                    "-m",
                    "agent_dev_lab.mcp_servers.career_server",
                ],
            }
        }
    )


#要与career_erver通信，所以是异步的
async def load_career_mcp_tools():
    client = create_career_mcp_client()

    return await client.get_tools()