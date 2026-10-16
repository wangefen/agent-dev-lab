import os
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
                "env":{
                    # MCP Server 是一个新的 Python 子进程。
                    # 先继承当前进程的环境变量，确保它能读取
                    # TAVILY_API_KEY 等 .env 配置。
                    **os.environ,

                    # 再单独覆盖这两个变量，关闭 MCP 子进程中的
                    # LangSmith 追踪。
                    "LANGSMITH_TRACING": "false",
                    "LANGCHAIN_TRACING_V2": "false",
                },
            }
        }
    )


#要与career_erver通信，所以是异步的
async def load_career_mcp_tools():
    client = create_career_mcp_client()

    return await client.get_tools()
