"""
把项目中的 Skill 加载能力提供给现有 LangChain Agent。
"""

from langchain_core.tools import tool

from agent_dev_lab.skills.registry import (
    SkillNotFoundError,
    SkillRegistry,
)


# 整个FastAPI进程共享一个Skill注册表。
#
# Agent创建系统提示词和调用load_skill时，
# 都使用这个相同的注册表对象。
skill_registry = SkillRegistry()


@tool
def load_skill(name: str) -> str:
    """
    Load the complete instructions for an available Agent Skill.

    Use the exact Skill name shown in the available Skill catalog.
    After loading a Skill, follow its workflow, tool guidance,
    output format, and constraints for the current user request.
    """

    try:
        skill = skill_registry.load(name)

    except SkillNotFoundError as exc:
        # 如果模型给出的Skill名称不正确，
        # 把可用名称返回给模型，让它自行改正。
        return (
            "Skill could not be loaded: "
            f"{exc}"
        )

    # 这段返回值会成为ToolMessage，
    # 进入当前Agent的消息上下文。
    return (
        f"Skill loaded: {skill.metadata.name}\n"
        f"Version: {skill.metadata.version}\n\n"
        f"{skill.instructions}"
    )