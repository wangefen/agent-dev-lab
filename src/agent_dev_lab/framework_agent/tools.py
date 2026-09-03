from langchain.tools import tool
from langchain_tavily import TavilySearch
from openai import max_retries

from agent_dev_lab.native_agent.llm import AGENT_TOOLS


web_serach = TavilySearch(
    max_results=5,
    topic="general",
)

@tool
def get_company_info(company: str) -> str:
    """Get basic information about a company."""

    return (
        f"Company information for {company}: "
        f"{company} is a technology company."
    )

AGENT_TOOLS = [
    web_serach,
    get_company_info,
]