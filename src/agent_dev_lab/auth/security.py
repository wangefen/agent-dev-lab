"""
认证模块的安全工具。

本文件负责两类操作：使用 Argon2 对密码进行不可逆散列和验证，
以及使用服务器密钥签发、验证 JWT 访问令牌。这里不访问数据库，
也不直接返回 HTTP 响应，便于其他业务模块复用和测试。
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from agent_dev_lab.config import (
    JWT_ALGORITHM,
    JWT_EXPIRE_MINUTES,
    JWT_SECRET,
)


# 使用 pwdlib 当前推荐的密码散列配置。
# 安装 pwdlib[argon2] 后，这里会使用 Argon2。
_password_hash = PasswordHash.recommended()


class InvalidAccessTokenError(Exception):
    """
    JWT 不合法、已过期或内容不正确。
    """


def hash_password(
    plain_password: str,
) -> str:
    """
    将明文密码转换为不可逆的密码摘要。

    每次散列都会自动加入随机盐，因此同一个密码多次散列得到的
    字符串通常不同，但 verify_password() 仍然能够正确验证。
    """

    return _password_hash.hash(
        plain_password
    )


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    验证明文密码是否匹配数据库中的密码摘要。

    返回 True 表示匹配，返回 False 表示密码错误。
    """

    return _password_hash.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(
    user_id: UUID,
) -> str:
    """
    为指定用户生成 JWT 访问令牌。

    令牌中只保存用户编号、令牌类型和时间信息，
    不保存密码、简历内容等敏感数据。
    """

    # JWT_SECRET 是服务器用来签名令牌的私密密钥。
    # 如果没有配置密钥，就不能安全地生成登录令牌，
    # 因此直接停止并给出明确错误。
    if not JWT_SECRET:
        raise RuntimeError(
            "JWT_SECRET is not configured."
        )

    # 使用带时区的 UTC 时间作为令牌签发时间。
    # 统一使用 UTC 可以避免本地开发环境和服务器时区不同
    # 导致令牌提前过期或延迟过期。
    issued_at = datetime.now(
        timezone.utc
    )

    # 过期时间 = 签发时间 + 配置的有效分钟数。
    # 默认配置为 10080 分钟，也就是 7 天。
    expires_at = (
        issued_at
        + timedelta(
            minutes=JWT_EXPIRE_MINUTES
        )
    )

    # payload 是写入 JWT 的公开声明数据。
    # JWT 的内容可以被查看，因此这里不能存放密码或密钥。
    payload = {
        # sub（subject）表示令牌属于哪个用户。
        # UUID 需要转换成字符串后才能写入 JSON 格式的 JWT。
        "sub": str(user_id),

        # 标记这是用于访问接口的 access token。
        # 以后如果增加刷新令牌，可以用 type 区分不同令牌。
        "type": "access",

        # iat（issued at）表示令牌的签发时间。
        "iat": issued_at,

        # exp（expiration time）表示令牌的过期时间。
        # jwt.decode() 验证时会自动检查该时间。
        "exp": expires_at,
    }

    # 使用 JWT_SECRET 和指定算法对 payload 进行签名。
    # 返回值是一段 header.payload.signature 格式的字符串，
    # 前端登录成功后需要保存并在后续请求中携带它。
    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(
    token: str,
) -> UUID:
    """
    验证 JWT 并返回其中的用户 UUID。

    如果令牌被篡改、已经过期、类型不正确，
    或者没有合法的用户编号，就抛出
    InvalidAccessTokenError。
    """

    # 生成和验证 JWT 必须使用同一个密钥。
    # 如果服务器没有配置 JWT_SECRET，就无法确认令牌
    # 是否确实由当前服务器签发，因此直接停止运行。
    if not JWT_SECRET:
        raise RuntimeError(
            "JWT_SECRET is not configured."
        )

    try:
        # 验证令牌签名并解析 payload。
        # algorithms 使用列表是为了明确限制允许的算法，
        # 防止攻击者在令牌中指定其他不安全算法。
        # jwt.decode() 也会自动检查 exp 是否已经过期。
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[
                JWT_ALGORITHM,
            ],
        )

        # 当前接口只接受 access token。
        # 如果以后增加 refresh token，不能让刷新令牌直接
        # 用来调用聊天、文件上传等受保护接口。
        if payload.get("type") != "access":
            raise InvalidAccessTokenError(
                "Unexpected token type."
            )

        # sub（subject）保存签发令牌时写入的用户编号。
        subject = payload.get("sub")

        # JWT 的 sub 应该是字符串。
        # 缺少 sub 或类型不正确，都说明令牌内容不符合要求。
        if not isinstance(subject, str):
            raise InvalidAccessTokenError(
                "Token subject is missing."
            )

        # 把 JWT 中的用户编号字符串还原成 UUID 对象。
        # 后续 dependencies.py 会使用这个 UUID 查询数据库，
        # 确认用户仍然存在并取得当前登录用户。
        return UUID(subject)

    # InvalidTokenError 包括签名错误、令牌过期、格式错误等
    # PyJWT 验证异常。
    # ValueError 和 TypeError 用来处理 sub 无法转换成 UUID
    # 等内容格式问题。
    except (
        InvalidTokenError,
        ValueError,
        TypeError,
    ) as error:
        # 对外统一抛出项目自己的异常，避免上层代码依赖
        # PyJWT 的具体异常类型。
        # dependencies.py 稍后会把它转换成 HTTP 401。
        raise InvalidAccessTokenError(
            "Access token is invalid or expired."
        ) from error
