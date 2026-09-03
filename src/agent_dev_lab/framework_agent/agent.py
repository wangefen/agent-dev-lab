from langchain.agents import create_agent

from agent_dev_lab.framework_agent.model import create_model
from agent_dev_lab.framework_agent.tools import AGENT_TOOLS

SYSTEM_PROMPT = """
You are a career research assistant.

Use tools when job or company information
is required.

Never invent tool results.
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
            "messsages": [
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