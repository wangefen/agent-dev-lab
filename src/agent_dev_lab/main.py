from agent_dev_lab.framework_agent.agent import (
    run_career_agent,
)


def main() -> None:
    response = run_career_agent(
        "帮我搜索上海目前的 Agent 开发实习岗位，"
        "重点关注 Python、LangChain、LangGraph 相关岗位。"
    )

    print(response)


if __name__ == "__main__":
    main()