"""
定义 Skill 系统使用的数据结构。

这里只规定一个合法的 Skill 应该包含哪些数据，
不负责扫描目录，也不负责读取 SKILL.md。
"""

from pathlib import Path

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class SkillMetadata(BaseModel):
    """
    表示 SKILL.md 顶部的 YAML 元数据。

    对应内容：

    ---
    name: job-fit-analysis
    description: 分析简历和岗位的匹配程度。
    version: "1.0.0"
    ---
    """

    model_config = ConfigDict(
        # YAML中出现未定义字段时直接报错。
        # 这样可以及时发现字段拼写错误。
        extra="forbid",

        # 对象创建后不允许修改字段。
        frozen=True,
    )

    name: str = Field(
        ...,
        description="Skill的唯一名称。",
        pattern=(
            r"^[a-z0-9]+"
            r"(?:-[a-z0-9]+)*$"
        ),
    )

    description: str = Field(
        ...,
        min_length=1,
        description=(
            "说明Skill的用途以及适用场景。"
        ),
    )

    version: str = Field(
        default="1.0.0",
        description="Skill版本号。",
        pattern=r"^\d+\.\d+\.\d+$",
    )


class SkillDefinition(BaseModel):
    """
    表示一个已经完成读取和校验的完整Skill。

    metadata：
        SKILL.md顶部的元数据。

    instructions：
        YAML元数据后面的Markdown操作说明。

    source_path：
        当前Skill对应的SKILL.md文件位置。
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