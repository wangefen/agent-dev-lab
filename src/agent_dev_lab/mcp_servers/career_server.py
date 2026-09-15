import os
import sys

from dotenv import load_dotenv
from langchain_tavily import TavilySearch
from mcp.server.fastmcp import FastMCP


load_dotenv()


#创建一个 MCP Server
mcp = FastMCP(
    "career-tools"
)   #"career-tools" = 服务器mcp自我介绍时的名字

web_search = TavilySearch(
    max_results=5,  #Tavily 每次搜索最多返回 5 条搜索结果
    topic="general",
)


@mcp.tool() #把下面这个 search_jobs 函数注册到 mcp 这个 MCP Server 里
async def search_jobs(
    city: str,
    keyword: str,
) -> str:
    """
    Search the web for current job
    opportunities by city and keyword.
    """

    query = (
        f"{city} {keyword} "
        f"实习 招聘 岗位"
    )

    result = await web_search.ainvoke(
        {
            "query": query,
        }
    )

    return str(result)



if __name__ == "__main__":
    mcp.run(
        transport="stdio"
    )