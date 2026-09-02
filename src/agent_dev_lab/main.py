from agent_dev_lab.llm import ask_llm


def main() -> None:
    response = ask_llm("研二积蓄俩万五算多算少")

    print(response)


if __name__ == "__main__":
    main()