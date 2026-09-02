from doctest import debug_script
from pydoc import describe

from pydantic import BaseModel, Field


class TaskIntent(BaseModel):
    intent: str = Field(
        description="The user's primary intent."
    )

    needs_tool: bool = Field(
        description="Whether external tools are needed."
    )

    reason: str = Field(
        description="Why a tool is or is not needed."
    )