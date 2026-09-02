from agent_dev_lab.llm import ask_with_tools


def main() -> None:
    message = ask_with_tools(
        "帮我找上海目前的 agent 实习岗位。"
    )

    print(message)
    print("content:", message.content)
    print("tool_calls:", message.tool_calls)



if __name__ == "__main__":
    main()