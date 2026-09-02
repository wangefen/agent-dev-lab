from agent_dev_lab.config import DEEPSEEK_MODEL
from agent_dev_lab.llm import (
    JOB_SEARCH_TOOL,
    create_client,
)
from agent_dev_lab.tool_executor import execute_tool_call


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

    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=messages,
        tools=[JOB_SEARCH_TOOL],
    )

    message = response.choices[0].message

    if not message.tool_calls:
        return message.content or ""

    #message.model_dump:把openai sdk中的message换成python能看懂的dict
    messages.append(message.model_dump(exclude_none=True))

    for tool_call in message.tool_calls:
        tool_result = execute_tool_call(tool_call)

        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result,
            }
        )

    final_response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=messages,
        tools=[
            JOB_SEARCH_TOOL,
        ],
    )

    final_content = (
        final_response
        .choices[0]
        .message
        .content
    )

    if final_content is None:
        raise RuntimeError(
            "The model returned an empty response."
        )

    return final_content