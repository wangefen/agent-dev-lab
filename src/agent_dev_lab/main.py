from agent_dev_lab.agent import run_agent



def main() -> None:
    response = run_agent("帮我了解一下字节跳动这家公司。")

    print(response)


if __name__ == "__main__":
    main()