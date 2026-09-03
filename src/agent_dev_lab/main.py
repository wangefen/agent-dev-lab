from agent_dev_lab.framework_agent.agent import run_career_agent



def main() -> None:
    response = run_career_agent("帮我找上海agent实习岗位。")

    print(response)


if __name__ == "__main__":
    main()