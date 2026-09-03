from langchain.agents import create_agent

from agent_dev_lab.framework_agent.model import create_model
from agent_dev_lab.framework_agent.tools import AGENT_TOOLS

SYSTEM_PROMPT = """
You are a career research assistant.

You can use:
1. Web search for current jobs, companies, and external information.
2. Resume search for the user's skills, education, projects, and experience.

When the user asks for job recommendations or job-fit analysis,
use both web search and resume search when appropriate.

Never invent job information or resume information.
Base your analysis on tool results.
"""


def create_career_agent():
    return create_agent(
        model = create_model(),
        tools = AGENT_TOOLS,
        system_prompt=SYSTEM_PROMPT,
    )

def run_career_agent(prompt: str) -> str:
    agent = create_career_agent()

    result = agent.invoke(
        {
            "messages": [
                {
                    "role":"user",
                    "content":prompt,
                }
            ]
        }
    )

    #result["messages"]:拿到消息列表,如：messages=[user,assistant,tool,assitant]
    #把 Agent 最后生成的回答返回给调用者
    return result["messages"][-1].content