from agent_dev_lab.agent import run_agent
from agent_dev_lab.llm import ask_with_tools
from agent_dev_lab.tool_executor import execute_tool_call


def main() -> None:
    response = run_agent("帮我找上海目前的 agent 实习岗位")

    print(response)


if __name__ == "__main__":
    main()