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
    response = run_career_agent(
        prompt=(
            "帮我搜索上海目前的 Agent 开发实习岗位，"
            "并结合我的简历分析我的匹配情况。"
        ),
        thread_id="career-test-001",
    )

    print(response)




if __name__ == "__main__":
    main()



