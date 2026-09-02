from agent_dev_lab.llm import ask_llm, analyze_intent


def main() -> None:
    result = analyze_intent("帮我找一下上海目前有哪些适合我的央国企 angent 实习岗位")

    print(result)
    print(result.intent)
    print(result.needs_tool)
    print(result.reason)


if __name__ == "__main__":
    main()