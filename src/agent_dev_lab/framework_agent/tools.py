from langchain_tavily import TavilySearch

from agent_dev_lab.framework_agent.resume_tool import (
    search_resume,
)

web_search = TavilySearch(
    max_results=5,
    topic="general",
)


AGENT_TOOLS = [
    web_search,
    search_resume,
]