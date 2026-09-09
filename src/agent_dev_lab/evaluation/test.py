import os
from dotenv import load_dotenv
from langsmith import Client

load_dotenv()

key = os.getenv("LANGSMITH_API_KEY")


def main() -> None:
    print(key is not None)
    print(key[:6] if key else None)
    client = Client()

    datasets = list(client.list_datasets(limit=1))

    print("LangSmith API key works.")


if __name__ == "__main__":
    main()