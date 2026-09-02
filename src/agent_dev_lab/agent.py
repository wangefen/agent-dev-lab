from agent_dev_lab.config import DEEPSEEK_MODEL
from agent_dev_lab.llm import (
    AGENT_TOOLS,
    create_client,
)
from agent_dev_lab.tool_executor import execute_tool_call

MAX_STEPS = 5


def run_agent(prompt: str) -> str:
    client = create_client()

    messages = [
        {
            "role": "system",
              "content": (
                "You are a career assistant. "
                "Use tools when external job "
                "information is needed."
            ),
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    for step in range(MAX_STEPS):
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=messages,
            tools=AGENT_TOOLS,
            tool_choice="auto"
        )
        message = response.choices[0].message

        print(f"Agent step {step + 1}")

        if not message.tool_calls:
            return message.content or ""

        messages.append(
            message.model_dump(exclude_none=True)
        )

        for tool_call in message.tool_calls:
            print(
                "Calling tool:",
                tool_call.function.name,
            )

            tool_result = execute_tool_call(tool_call)

            print(
                "Tool result:",
                tool_result,
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                }
            )

    raise RuntimeError(
        "Agent exceeded maximum steps."
    )