import asyncio
import selectors

# LangGraph 提供的异步 PostgreSQL Checkpointer
# 作用：把 Agent 的 checkpoint / 对话状态持久化到 PostgreSQL
from langgraph.checkpoint.postgres.aio import (
    AsyncPostgresSaver,
)

# 从项目配置中读取 PostgreSQL 连接地址
# 例如：
# postgresql://agent_user:password@localhost:5432/agent_dev_lab
from agent_dev_lab.config import DATABASE_URL


# 定义异步主函数
async def main() -> None:

    # 如果没有配置数据库连接地址，直接报错并停止程序
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not configured."
        )

    # 根据 DATABASE_URL 连接 PostgreSQL
    # async with 会负责：
    # 1. 建立数据库连接
    # 2. 把创建出的 checkpointer 对象赋值给 checkpointer
    # 3. 代码块结束后自动关闭 / 释放连接
    async with AsyncPostgresSaver.from_conn_string(
        DATABASE_URL
    ) as checkpointer:

        # 初始化 LangGraph Checkpointer 所需要的数据库表
        # 可以理解成：
        # 自动执行 CREATE TABLE / CREATE INDEX 等初始化操作
        #
        # 这一步通常只需要在第一次初始化数据库时运行
        await checkpointer.setup()

    # setup 成功后打印提示
    print(
        "PostgreSQL checkpointer setup completed."
    )




# 只有直接运行当前 Python 文件时，才执行 main()
if __name__ == "__main__":
    asyncio.run(
        main(),
        loop_factory=lambda: asyncio.SelectorEventLoop(
            selectors.SelectSelector()
        ),
    )