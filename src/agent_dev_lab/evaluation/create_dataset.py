from langsmith import Client
from dotenv import load_dotenv

load_dotenv()
DATASET_NAME = "career-agent-v1"


def main() -> None:
    client = Client()

    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description=(
            "Offline evaluation dataset "
            "for the Career Research Agent."
        ),
    )

    examples = [
        {
            "inputs": {
                "prompt": (
                    "结合我的简历分析我是否适合 "
                    "Agent 开发实习，并分别说明"
                    "优势、缺口和建议。"
                )
            },
            "outputs": {
                "required_sections": [
                    "优势",
                    "缺口",
                    "建议",
                ]
            },
        },
        {
            "inputs": {
                "prompt": (
                    "结合我的简历分析我的求职竞争力，"
                    "请从优势、缺口和建议三个方面回答。"
                )
            },
            "outputs": {
                "required_sections": [
                    "优势",
                    "缺口",
                    "建议",
                ]
            },
        },
        {
            "inputs": {
                "prompt": (
                    "如果我要投递 Agent 开发岗位，"
                    "结合简历告诉我目前的优势、"
                    "技术缺口以及下一步学习建议。"
                )
            },
            "outputs": {
                "required_sections": [
                    "优势",
                    "缺口",
                    "建议",
                ]
            },
        },
    ]

    client.create_examples(
        dataset_id=dataset.id,
        examples=examples,
    )

    print(
        f"Created dataset: {dataset.name}"
    )


if __name__ == "__main__":
    main()