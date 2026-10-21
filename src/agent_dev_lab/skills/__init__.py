"""
Agent Skill 运行系统。

项目根目录中的 skills/ 保存具体的 Skill 内容；
当前 Python 包负责发现、校验、注册和加载这些 Skill。
"""

"""
定义 Skill 系统使用的数据结构。

这个文件只描述“一个合法的 Skill 应该包含什么”，
不负责读取文件，也不负责把 Skill 交给 Agent。
"""

from pathlib import Path

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class SkillMetadata(BaseModel):
    """
    SKILL.md 顶部 YAML 元数据对应的数据模型。

    例如：

    ---
    name: job-fit-analysis
    description: 分析简历和岗位之间的匹配程度。
    version: "1.0.0"
    ---
    """

    model_config = ConfigDict(
        # 如果 YAML 中出现了当前模型没有定义的字段，
        # 直接报错，避免因为字段拼错而被悄悄忽略。
        extra="forbid",

        # 模型创建完成后不允许修改，
        # 避免 Skill 注册后元数据意外发生变化。
        frozen=True,
    )

    name: str = Field(
        ...,
        description="Skill 的唯一名称。",
        pattern=(
            r"^[a-z0-9]+"
            r"(?:-[a-z0-9]+)*$"
        ),
    )

    description: str = Field(
        ...,
        min_length=1,
        description=(
            "描述 Skill 的用途，以及什么情况下应该使用它。"
        ),
    )

    version: str = Field(
        default="1.0.0",
        description="Skill 的版本号。",
        pattern=r"^\d+\.\d+\.\d+$",
    )


class SkillDefinition(BaseModel):
    """
    一个已经完成读取和校验的完整 Skill。

    metadata：
        SKILL.md 顶部的 YAML 元数据。

    instructions：
        SKILL.md 中 YAML 元数据之后的 Markdown 正文，
        也就是最终交给 Agent 阅读的操作手册。

    source_path：
        该 Skill 对应的 SKILL.md 文件位置。
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    metadata: SkillMetadata

    instructions: str = Field(
        ...,
        min_length=1,
    )

    source_path: Path
