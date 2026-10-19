"""
认证模块的业务逻辑层（Service）。

本文件负责组织完整的注册和登录流程：规范化邮箱、查询用户、
散列或验证密码、创建用户，并签发 JWT。它位于 router.py 和
repository.py/security.py 之间，不直接处理 HTTP 响应或编写 SQL。
"""

from dataclasses import dataclass
from uuid import uuid4

from psycopg_pool import AsyncConnectionPool

from agent_dev_lab.auth.repository import (
    DuplicateEmailError,
    UserRecord,
    create_user,
    get_user_by_email,
)
from agent_dev_lab.auth.security import (
    create_access_token,
    hash_password,
    verify_password,
)


class EmailAlreadyRegisteredError(Exception):
    """注册邮箱已经被其他用户使用。"""


class InvalidCredentialsError(Exception):
    """邮箱或密码不正确。"""


@dataclass(frozen=True)
class AuthenticationResult:
    """
    注册或登录成功后的内部业务结果。

    router.py 会把它转换为对外的 TokenResponse。
    """

    # 已经从数据库读取或刚刚创建的完整用户记录。
    user: UserRecord

    # 为该用户新签发的 JWT 字符串。
    access_token: str


def normalize_email(email: str) -> str:
    """
    统一邮箱的保存和查询格式。

    去掉首尾空格并转换为小写，避免同一个邮箱因为大小写
    不同而被当成多个账号。
    """

    return email.strip().lower()


async def register_user(
    pool: AsyncConnectionPool,
    email: str,
    password: str,
) -> AuthenticationResult:
    """
    注册用户，并为新用户签发访问令牌。

    执行顺序：规范化邮箱 → 检查重复 → 生成 UUID → 散列密码
    → 写入数据库 → 生成 JWT。
    """

    # 数据库存储和查询都使用相同的规范化邮箱。
    normalized_email = normalize_email(email)

    # 先进行一次友好的重复检查，使常见情况能得到明确错误。
    existing_user = await get_user_by_email(
        pool,
        normalized_email,
    )
    if existing_user is not None:
        raise EmailAlreadyRegisteredError(
            "Email is already registered."
        )

    # uuid4() 在应用中生成随机用户编号。
    # 这个 UUID 会保存到数据库，也会写入 JWT 的 sub 字段。
    user_id = uuid4()

    # 数据库只保存不可逆的密码摘要，不保存用户的原始密码。
    password_hash = hash_password(password)

    try:
        user = await create_user(
            pool=pool,
            user_id=user_id,
            email=normalized_email,
            password_hash=password_hash,
        )
    except DuplicateEmailError as error:
        # 处理两个相同邮箱的注册请求同时到达的情况。
        raise EmailAlreadyRegisteredError(
            "Email is already registered."
        ) from error

    # 注册成功后直接签发 Token，前端无需再额外登录一次。
    return AuthenticationResult(
        user=user,
        access_token=create_access_token(user.id),
    )


async def login_user(
    pool: AsyncConnectionPool,
    email: str,
    password: str,
) -> AuthenticationResult:
    """
    验证邮箱和密码，成功后签发新的访问令牌。

    执行顺序：规范化邮箱 → 查询用户 → 验证密码 → 生成 JWT。
    """

    # 登录和注册必须使用相同的邮箱规范化规则。
    normalized_email = normalize_email(email)
    user = await get_user_by_email(
        pool,
        normalized_email,
    )

    # 无论邮箱不存在还是密码错误，都返回相同错误。
    # 这样不会向外部暴露某个邮箱是否已经注册。
    if user is None or not verify_password(
        password,
        user.password_hash,
    ):
        raise InvalidCredentialsError(
            "Email or password is incorrect."
        )

    # 每次成功登录都会签发一枚新的访问令牌。
    return AuthenticationResult(
        user=user,
        access_token=create_access_token(user.id),
    )
