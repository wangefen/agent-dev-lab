"""
会话模块的数据访问代码。

负责与 PostgreSQL 中的 conversations 表交互。
"""
from uuid import UUID

from psycopg_pool import AsyncConnectionPool


async def create_conversation_table(
    pool: AsyncConnectionPool,
) -> None:
    """
    创建会话目录表。

    一行代表一段用户会话；
    Agent具体的执行状态仍保存在checkpoint相关表中。
    """

    # 从连接池借用数据库连接，用完后自动归还。
    async with pool.connection() as connection:
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id UUID PRIMARY KEY,

                user_id UUID NOT NULL
                    REFERENCES app_users(id),

                title TEXT NOT NULL DEFAULT '新对话',

                created_at TIMESTAMPTZ NOT NULL
                    DEFAULT NOW(),

                updated_at TIMESTAMPTZ NOT NULL
                    DEFAULT NOW()
            )
            """
        )


async def create_conversation(
    pool: AsyncConnectionPool,
    conversation_id: UUID,
    user_id: UUID,
) -> dict:
    """
    创建一条会话记录，并返回数据库保存的结果。

    conversation_id：
        后端生成的会话UUID。

    user_id：
        创建这段会话的用户UUID。
    """

    async with pool.connection() as connection:
        # 使用占位符传递参数，不直接把值拼接进SQL。
        cursor = await connection.execute(
            """
            INSERT INTO conversations (
                id,
                user_id
            )
            VALUES (%s, %s)
            RETURNING
                id,
                user_id,
                title,
                created_at,
                updated_at
            """,
            (
                conversation_id,
                user_id,
            ),
        )

        # RETURNING返回插入后的这一行。
        row = await cursor.fetchone()

    if row is None:
        raise RuntimeError(
            "Conversation was created but no data was returned."
        )

    return row


async def list_conversations(
    pool: AsyncConnectionPool,
    user_id: UUID,
) -> list[dict]:
    """
    查询指定用户的会话列表。

    按最近更新时间倒序排列：
    最近使用的会话排在前面。
    """

    async with pool.connection() as connection:
        cursor = await connection.execute(
            """
            SELECT
                id,
                user_id,
                title,
                created_at,
                updated_at
            FROM conversations
            WHERE user_id = %s
            ORDER BY updated_at DESC, id DESC
            """,
            (user_id,),
        )

        # fetchall()读取符合条件的所有行。
        rows = await cursor.fetchall()

    return rows

async def get_conversation(pool: AsyncConnectionPool, conversation_id: UUID, user_id: UUID) -> dict | None:
    """查询属于指定用户的会话；不存在时返回 None。"""
    # 从共享连接池借用连接，退出代码块时自动归还。
    async with pool.connection() as connection:
        cursor = await connection.execute(
            """
            SELECT id, user_id, title, created_at, updated_at
            FROM conversations
            WHERE id = %s AND user_id = %s
            """,
            (conversation_id, user_id),
        )

        # 会话 ID 是主键，最多返回一行。
        row = await cursor.fetchone()

    return row
