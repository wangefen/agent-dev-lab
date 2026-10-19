"""
认证模块的数据访问层（Repository）。

本文件只负责和 PostgreSQL 交互，包括创建用户表、保存用户以及
按邮箱或 UUID 查询用户。它不处理 HTTP 请求，也不决定注册、
登录等业务流程，这样数据库操作可以被 service.py 统一调用。
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from psycopg.errors import UniqueViolation
from psycopg_pool import AsyncConnectionPool


@dataclass(frozen=True)
class UserRecord:
    """
    后端内部使用的完整用户记录。

    password_hash 只能留在后端，不能通过接口返回给前端。
    对外返回用户信息时，应使用 schemas.py 中的 UserResponse。
    """

    # 用户的全局唯一编号，由 service.py 使用 uuid4() 生成。
    id: UUID

    # 经过统一小写处理的登录邮箱。
    email: str

    # 由 Argon2 生成的密码摘要，不是用户的明文密码。
    password_hash: str

    # PostgreSQL 插入用户记录时自动生成的注册时间。
    created_at: datetime


class DuplicateEmailError(Exception):
    """准备保存的邮箱已经存在。"""


def _row_to_user(
    row: dict[str, Any],
) -> UserRecord:
    """
    把数据库返回的一行字典转换成 UserRecord。

    当前连接池使用 dict_row，因此可以通过字段名读取查询结果。
    函数名开头的下划线表示它只供本文件内部使用。
    """

    return UserRecord(
        id=row["id"],
        email=row["email"],
        password_hash=row["password_hash"],
        created_at=row["created_at"],
    )


async def create_auth_tables(
    pool: AsyncConnectionPool,
) -> None:
    """
    创建认证模块使用的用户表。

    IF NOT EXISTS 让应用可以安全地重复启动：
    表已经存在时不会再次创建，也不会因此报错。
    """

    async with pool.connection() as connection:
        # async with 会向连接池借用一个连接，执行结束后自动归还。
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS app_users (
                id UUID PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )


async def get_user_by_email(
    pool: AsyncConnectionPool,
    email: str,
) -> UserRecord | None:
    """根据邮箱查询用户；没有找到时返回 None。"""

    async with pool.connection() as connection:
        cursor = await connection.execute(
            """
            SELECT
                id,
                email,
                password_hash,
                created_at
            FROM app_users
            WHERE email = %s
            """,
            # 使用 %s 占位符传参数，避免把用户输入直接拼进 SQL，
            # 从而防止 SQL 注入。(email,) 是只有一个元素的元组。
            (email,),
        )

        # fetchone() 最多读取一行；邮箱有 UNIQUE 约束，
        # 因此同一个邮箱不可能查询出多条用户记录。
        row = await cursor.fetchone()

    if row is None:
        return None

    return _row_to_user(row)


async def get_user_by_id(
    pool: AsyncConnectionPool,
    user_id: UUID,
) -> UserRecord | None:
    """根据 JWT 中的用户 UUID 查询用户。"""

    async with pool.connection() as connection:
        cursor = await connection.execute(
            """
            SELECT
                id,
                email,
                password_hash,
                created_at
            FROM app_users
            WHERE id = %s
            """,
            # UUID 作为查询参数交给 psycopg 安全转换。
            (user_id,),
        )
        row = await cursor.fetchone()

    if row is None:
        return None

    return _row_to_user(row)


async def create_user(
    pool: AsyncConnectionPool,
    user_id: UUID,
    email: str,
    password_hash: str,
) -> UserRecord:
    """
    保存新用户并返回数据库生成的完整记录。

    这里只接收密码摘要，绝不能把明文密码写入数据库。
    """

    try:
        async with pool.connection() as connection:
            # RETURNING 让 INSERT 完成后直接返回刚创建的用户，
            # 包括由 PostgreSQL 自动填写的 created_at。
            cursor = await connection.execute(
                """
                INSERT INTO app_users (
                    id,
                    email,
                    password_hash
                )
                VALUES (%s, %s, %s)
                RETURNING
                    id,
                    email,
                    password_hash,
                    created_at
                """,
                (
                    user_id,
                    email,
                    password_hash,
                ),
            )
            row = await cursor.fetchone()

    # 即使两个相同邮箱的注册请求同时到达，数据库的 UNIQUE
    # 约束仍会阻止重复数据。这里把数据库异常转换成业务异常。
    except UniqueViolation as error:
        raise DuplicateEmailError(
            "Email is already registered."
        ) from error

    if row is None:
        # 正常执行带 RETURNING 的 INSERT 一定会返回一行。
        # 如果没有返回，说明数据库行为不符合程序预期。
        raise RuntimeError(
            "User was created but no data was returned."
        )

    return _row_to_user(row)
