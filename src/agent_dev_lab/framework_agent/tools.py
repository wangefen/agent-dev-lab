from langchain.tools import tool

from agent_dev_lab.native_agent.llm import AGENT_TOOLS


@tool
def search_jobs(city: str, keyword:str,) -> str:
    #Python 的 docstring。告诉langchain这个工具是干什么的
    """Search for job openings by city and keyword."""

    return (
        f"Searching jobs in {city} "
        f"with keyword {keyword}."
    )

@tool
def get_company_info(company: str) -> str:
    """Get basic information about a company."""

    return (
        f"Company information for {company}: "
        f"{company} is a technology company."
    )

AGENT_TOOLS = [
    search_jobs,
    get_company_info,
]