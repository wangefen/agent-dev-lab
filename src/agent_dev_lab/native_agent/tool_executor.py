import json
from typing import Any


from agent_dev_lab.native_agent.tools import (
    get_company_info,
    search_jobs,
)

#这里面字典的值是函数，不是字符串
TOOL_REGISTRY = {
    "search_jobs": search_jobs,
    "get_company_info": get_company_info,
}

def execute_tool_call(tool_call: Any) -> str:
    tool_name = tool_call.function.name

    # tool_call.function.arguments:LLM 帮你生成的、准备传给这个函数的参数。
    arguments = json.loads(tool_call.function.arguments)

    tool = TOOL_REGISTRY.get(tool_name)

    if tool is None:
        raise ValueError(
        f"Unknown tool: {tool_name}"
        )

    #**会对字典进行关键字参数解包。
    return tool(**arguments)

