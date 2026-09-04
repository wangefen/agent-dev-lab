from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from agent_dev_lab.framework_agent.model import create_model
from agent_dev_lab.framework_agent.tools import AGENT_TOOLS

SYSTEM_PROMPT = """
You are a career research assistant.

You can use:
1. Web search for current jobs, companies, and external information.
2. Resume search for the user's skills, education, projects, and experience.

If the user's question can be answered directly from the conversation
history, do not call tools unnecessarily.

Use tools only when external or resume information is actually needed.

When the user asks for current job recommendations or job-fit analysis,
use web search and resume search when appropriate.

Never invent job information or resume information.
Base factual analysis on tool results when tools are required.
"""

checkpointer = InMemorySaver()

carrer_agent = create_agent(
    model=create_model(),
    tools=AGENT_TOOLS,
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,
)
def run_career_agent(prompt: str, thread_id: str) -> str:
    result = carrer_agent.invoke(
        {
            "messages": [
                {
                    "role":"user",
                    "content":prompt,
                }
            ]
        },
        config={
            "configurable":{
                "thread_id": thread_id,
            }
        },
    )

    #result["messages"]:拿到消息列表,如：messages=[user,assistant,tool,assitant]
    #把 Agent 最后生成的回答返回给调用者
    return result["messages"][-1].content