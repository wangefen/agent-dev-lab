from agent_dev_lab.framework_agent.agent import (
    run_career_agent,
)


def main() -> None:
    response = run_career_agent(
        "帮我搜索上海目前的 Agent 开发实习岗位，"
        "开发实习岗位，并结合我的简历分析我的匹配情况。"
    )

    print(response)


if __name__ == "__main__":
    main()