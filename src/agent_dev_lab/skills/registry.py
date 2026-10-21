"""
发现、校验、注册和加载项目中的 Agent Skill。

项目根目录下的 ``skills/`` 保存 Skill 内容；
当前模块负责把其中的 ``SKILL.md`` 转换成经过校验的 Python 对象。

注册表分成两个阶段工作：

1. ``discover()`` 扫描所有 Skill，读取并校验元数据，建立名称到文件的索引；
2. ``load()`` 在 Agent 真正需要某个 Skill 时，再返回完整操作说明。

这种设计可以让 Agent 一开始只看到简短的 Skill 目录，
需要某项能力时再加载完整说明，避免把所有 Skill 全部塞进模型上下文。
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from agent_dev_lab.skills.models import (
    SkillDefinition,
    SkillMetadata,
)


# registry.py 位于：
#
#   项目根目录/src/agent_dev_lab/skills/registry.py
#
# 因此向上三级可以得到项目根目录。
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# 默认从项目根目录的 skills/ 中发现 Skill。
DEFAULT_SKILLS_DIR = PROJECT_ROOT / "skills"

# 每个 Skill 目录中都必须使用这个固定文件名。
SKILL_FILE_NAME = "SKILL.md"

# YAML Front Matter 使用三条短横线作为开始和结束标记。
FRONT_MATTER_DELIMITER = "---"


class SkillRegistryError(RuntimeError):
    """Skill目录、文件格式或元数据不合法。"""


class SkillNotFoundError(SkillRegistryError):
    """根据名称找不到已经注册的Skill。"""


class SkillRegistry:
    """
    管理当前项目中所有可用的Skill。

    注册表不会执行Skill中的内容，它只负责：

    - 扫描Skill目录；
    - 校验SKILL.md格式；
    - 保存Skill名称与文件位置的对应关系；
    - 在需要时加载完整Skill。
    """

    def __init__(
        self,
        skills_dir: str | Path = DEFAULT_SKILLS_DIR,
    ) -> None:
        # 允许调用者传入字符串或Path，内部统一转换成绝对路径。
        # 测试时可以传入临时目录，不必依赖真实项目目录。
        self.skills_dir = Path(skills_dir).resolve()

        # 只保存已经通过校验的Skill元数据。
        self._metadata_by_name: dict[str, SkillMetadata] = {}

        # 保存Skill名称和SKILL.md路径之间的对应关系。
        # load()会从这里取出路径，而不是直接拼接用户输入，
        # 可以避免"../../"一类路径穿越问题。
        self._path_by_name: dict[str, Path] = {}

        # 用单独的布尔值记录是否完成扫描。
        # 不能只判断字典是否为空，因为一个合法但没有Skill的目录
        # 同样会得到空字典。
        self._discovered = False

    def discover(self) -> tuple[SkillMetadata, ...]:
        """
        扫描skills目录并注册所有合法Skill。

        只扫描skills目录的直接子目录，例如：

            skills/job-fit-analysis/SKILL.md

        扫描过程中会检查：

        - skills目录是否存在；
        - SKILL.md是否具有完整的YAML文件头；
        - 元数据能否通过Pydantic模型校验；
        - 文件夹名称是否与Skill名称一致；
        - Skill名称是否重复；
        - Markdown操作说明是否为空。
        """

        if not self.skills_dir.exists():
            raise SkillRegistryError(
                f"Skill directory does not exist: {self.skills_dir}"
            )

        if not self.skills_dir.is_dir():
            raise SkillRegistryError(
                f"Skill path is not a directory: {self.skills_dir}"
            )

        metadata_by_name: dict[str, SkillMetadata] = {}
        path_by_name: dict[str, Path] = {}

        # glob只匹配：skills/某个目录/SKILL.md。
        # sorted保证每次扫描顺序稳定，便于测试和排查问题。
        skill_paths = sorted(
            self.skills_dir.glob(
                f"*/{SKILL_FILE_NAME}"
            )
        )

        for skill_path in skill_paths:
            skill = self._parse_skill_file(skill_path)
            skill_name = skill.metadata.name
            directory_name = skill_path.parent.name

            # 目录名和元数据名称保持一致，可以让文件位置直观可预测。
            if directory_name != skill_name:
                raise SkillRegistryError(
                    "Skill directory name does not match "
                    f"metadata name: directory={directory_name!r}, "
                    f"name={skill_name!r}, file={skill_path}"
                )

            # 不允许两个目录注册同一个名称，否则Agent无法确定加载哪一个。
            if skill_name in metadata_by_name:
                existing_path = path_by_name[skill_name]
                raise SkillRegistryError(
                    f"Duplicate Skill name {skill_name!r}: "
                    f"{existing_path} and {skill_path}"
                )

            metadata_by_name[skill_name] = skill.metadata
            path_by_name[skill_name] = skill_path

        # 先使用局部字典完成全部校验，确认没有异常后再替换旧注册表。
        # 这样扫描中途失败时，不会留下只注册了一半的状态。
        self._metadata_by_name = metadata_by_name
        self._path_by_name = path_by_name
        self._discovered = True

        return self.list_metadata()

    def list_metadata(self) -> tuple[SkillMetadata, ...]:
        """返回所有已注册Skill的简要元数据。"""

        self._ensure_discovered()

        # 按Skill名称排序，使系统提示词和测试结果保持稳定。
        return tuple(
            self._metadata_by_name[name]
            for name in sorted(self._metadata_by_name)
        )

    def render_catalog(self) -> str:
        """
        把Skill元数据渲染成适合放进Agent提示词的目录。

        这里只暴露名称、版本和简介，不包含完整操作说明。
        完整内容需要Agent稍后通过load_skill工具按需加载。
        """

        metadata_list = self.list_metadata()

        if not metadata_list:
            return "No Skills are currently available."

        lines = [
            (
                f"- {metadata.name} "
                f"(version {metadata.version}): "
                f"{metadata.description}"
            )
            for metadata in metadata_list
        ]

        return "\n".join(lines)

    def load(self, name: str) -> SkillDefinition:
        """
        根据唯一名称加载一个完整Skill。

        name只能命中discover()已经建立的索引，不能被当成任意文件路径，
        因此调用者无法通过名称读取skills目录之外的文件。
        """

        self._ensure_discovered()

        skill_path = self._path_by_name.get(name)

        if skill_path is None:
            available_names = ", ".join(
                sorted(self._path_by_name)
            )
            available_text = available_names or "none"

            raise SkillNotFoundError(
                f"Unknown Skill {name!r}. "
                f"Available Skills: {available_text}."
            )

        # 真正需要Skill时重新读取文件，得到完整Markdown操作说明。
        skill = self._parse_skill_file(skill_path)

        # 如果discover()之后文件元数据被修改，要求重新扫描，
        # 避免目录中展示的信息和实际加载的信息不一致。
        registered_metadata = self._metadata_by_name[name]

        if skill.metadata != registered_metadata:
            raise SkillRegistryError(
                f"Skill metadata changed after discovery: {skill_path}. "
                "Run discover() again before loading it."
            )

        return skill

    def _ensure_discovered(self) -> None:
        """首次使用注册表时自动执行一次Skill扫描。"""

        if not self._discovered:
            self.discover()

    @staticmethod
    def _parse_skill_file(
        skill_path: Path,
    ) -> SkillDefinition:
        """
        读取并解析一个SKILL.md。

        文件结构必须是：

            ---
            name: example-skill
            description: Example description.
            version: "1.0.0"
            ---

            # Markdown instructions
        """

        try:
            content = skill_path.read_text(
                encoding="utf-8"
            )
        except OSError as exc:
            raise SkillRegistryError(
                f"Cannot read Skill file: {skill_path}"
            ) from exc

        lines = content.splitlines()

        # 文件第一行必须是YAML Front Matter开始标记。
        if (
            not lines
            or lines[0].strip()
            != FRONT_MATTER_DELIMITER
        ):
            raise SkillRegistryError(
                "SKILL.md must start with YAML front matter "
                f"delimiter '---': {skill_path}"
            )

        # 从第二行开始查找Front Matter结束标记。
        closing_index: int | None = None

        for index, line in enumerate(
            lines[1:],
            start=1,
        ):
            if line.strip() == FRONT_MATTER_DELIMITER:
                closing_index = index
                break

        if closing_index is None:
            raise SkillRegistryError(
                "SKILL.md is missing the closing YAML front "
                f"matter delimiter '---': {skill_path}"
            )

        yaml_text = "\n".join(
            lines[1:closing_index]
        ).strip()

        instructions = "\n".join(
            lines[closing_index + 1:]
        ).strip()

        if not yaml_text:
            raise SkillRegistryError(
                f"Skill metadata is empty: {skill_path}"
            )

        if not instructions:
            raise SkillRegistryError(
                f"Skill instructions are empty: {skill_path}"
            )

        try:
            raw_metadata: Any = yaml.safe_load(yaml_text)
        except yaml.YAMLError as exc:
            raise SkillRegistryError(
                f"Invalid YAML metadata in {skill_path}: {exc}"
            ) from exc

        # YAML的顶层必须是键值映射，不能是列表、字符串或数字。
        if not isinstance(raw_metadata, dict):
            raise SkillRegistryError(
                "Skill metadata must be a YAML mapping: "
                f"{skill_path}"
            )

        try:
            metadata = SkillMetadata.model_validate(
                raw_metadata
            )

            return SkillDefinition(
                metadata=metadata,
                instructions=instructions,
                source_path=skill_path,
            )
        except ValidationError as exc:
            raise SkillRegistryError(
                f"Invalid Skill data in {skill_path}: {exc}"
            ) from exc
