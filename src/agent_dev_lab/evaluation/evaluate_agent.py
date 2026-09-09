from uuid import uuid4

from dotenv import load_dotenv
from langsmith import Client
from pydantic import BaseModel, Field

from agent_dev_lab.framework_agent.agent import (
    run_career_agent,
)
from agent_dev_lab.framework_agent.model import (
    create_model,
)


load_dotenv()


DATASET_NAME = "career-agent-v1"


# =========================
# 1. LLM Judge 输出结构
# =========================

class JudgeResult(BaseModel):
    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Overall quality score from 0 to 1.",
    )

    reason: str = Field(
        description="Reason for the score.",
    )


# 创建一个专门用于评测的模型
judge_model = (
    create_model()
    .with_structured_output(
        JudgeResult,
        method="json_mode",
    )
)


# =========================
# 2. Target
# 被测试的 Career Agent
# =========================

def target(
    inputs: dict,
) -> dict:
    """
    Run the Career Agent for one evaluation example.
    """

    answer = run_career_agent(
        prompt=inputs["prompt"],

        # 每条测试数据使用独立 thread，
        # 避免 Memory 相互污染
        thread_id=f"eval-{uuid4()}",
    )

    return {
        "answer": answer,
    }


# =========================
# 3. 规则 Evaluator
# =========================

def required_sections_evaluator(
    outputs: dict,
    reference_outputs: dict,
) -> dict:
    """
    Check whether the answer contains all
    required sections defined in the dataset.
    """

    answer = outputs["answer"]

    required_sections = (
        reference_outputs[
            "required_sections"
        ]
    )

    matched = sum(
        section in answer
        for section in required_sections
    )

    score = (
        matched
        / len(required_sections)
    )

    return {
        "key": "required_sections",
        "score": score,
    }


# =========================
# 4. LLM-as-a-Judge
# =========================

def answer_quality_evaluator(
    inputs: dict,
    outputs: dict,
) -> dict:
    """
    Use another LLM call as a judge
    to evaluate the quality of the
    Career Agent's final answer.
    """

    user_prompt = inputs["prompt"]
    agent_answer = outputs["answer"]

    judge_prompt = f"""
    你是一名严格的 AI Agent 评测员。

    你的任务是评价一个求职助手生成的回答质量。

    ====================
    用户问题
    ====================

    {user_prompt}


    ====================
    Agent 回答
    ====================

    {agent_answer}


    ====================
    评分标准
    ====================

    请综合评价以下五个方面：

    1. 问题相关性
       是否真正回答了用户提出的问题，
       是否存在明显跑题。

    2. 分析具体程度
       回答是否包含具体分析，
       而不是大量空泛、模板化表达。

    3. 分析逻辑
       对用户优势、技术缺口、
       求职竞争力等方面的分析是否合理。

    4. 建议可执行性
       给出的学习、项目、求职或投递建议
       是否明确并且具有实际可执行性。

    5. 表达质量
       回答是否结构清晰、逻辑连贯，
       是否容易理解。


    请给出一个 0 到 1 之间的综合分数。

    评分参考：

    0.0：
    回答质量很差，基本无法帮助用户。

    0.3：
    部分回答了问题，但存在明显缺失。

    0.5：
    基本可用，但分析比较普通。

    0.7：
    回答较好，有比较明确的分析和建议。

    0.8：
    质量较高，分析具体且建议具有可执行性。

    0.9：
    非常优秀，分析深入、具体且实用。

    1.0：
    几乎没有明显问题。


    注意：

    你目前只能评价回答本身的质量。

    你没有看到用户完整原始简历，
    因此不要声称自己能够确定
    Agent 是否百分之百忠于简历事实。


    ====================
    输出格式
    ====================

    只允许返回下面这种 JSON 结构：

    {{
        "score": 0.0,
        "reason": "用一段简洁文字说明评分理由"
    }}

    要求：

    1. score 必须是 0 到 1 之间的数字。
    2. reason 必须是字符串。
    3. 字段名必须严格为 "score" 和 "reason"。
    4. 不要返回 "reasoning" 字段。
    5. 不要增加任何其他字段。
    6. 不要返回 Markdown。
    7. 不要在 JSON 前后添加解释文字。
"""

    result = judge_model.invoke(
        judge_prompt
    )

    return {
        "key": "answer_quality",
        "score": result.score,
        "comment": result.reason,
    }


# =========================
# 5. 运行 LangSmith Experiment
# =========================

def main() -> None:
    client = Client()

    results = client.evaluate(
        target,

        data=DATASET_NAME,

        evaluators=[
            required_sections_evaluator,
            answer_quality_evaluator,
        ],

        experiment_prefix=(
            "career-agent-v1"
        ),

        # 目前保持单线程评测
        # 避免同时跑多个 Agent
        # 让调试结果更稳定
        max_concurrency=1,
    )

    print(results)


if __name__ == "__main__":
    main()