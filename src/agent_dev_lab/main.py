import sys

from agent_dev_lab.framework_agent.agent import (
    run_career_agent,
)


def _configure_utf8_stdio() -> None:
    # Windows 中文控制台/管道默认用 GBK 编码，无法输出模型回答里的
    # emoji（如 🟢），print 会抛 UnicodeEncodeError。切到 UTF-8 并
    # 用 errors="replace" 兜底，保证任何终端下都不会崩溃。
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def main() -> None:
    _configure_utf8_stdio()

    thread_id = "career-test-001"

    response1 = run_career_agent(
        "记住，我找工作优先上海，"
        "而且优先考虑银行科技岗和央国企。",
        thread_id=thread_id,
    )

    print("===== 第一轮 =====")
    print(response1)

    response2 = run_career_agent(
        "我刚才说自己优先考虑什么城市和什么类型的单位？",
        thread_id=thread_id,
    )

    print("\n===== 第二轮 =====")
    print(response2)


if __name__ == "__main__":
    main()



