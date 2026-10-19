"""
FastAPI 认证依赖。

本文件负责从 FastAPI 应用中取得数据库连接池、读取请求头中的
Bearer Token、验证 JWT，并查询出当前登录用户。需要身份认证的
接口可以直接依赖 CurrentUser，不必重复实现这一整套流程。
"""

from typing import Annotated

from fastapi import (
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from psycopg_pool import AsyncConnectionPool

from agent_dev_lab.auth.repository import (
    UserRecord,
    get_user_by_id,
)
from agent_dev_lab.auth.security import (
    InvalidAccessTokenError,
    decode_access_token,
)


# HTTPBearer 会从 Authorization: Bearer <token> 请求头中
# 解析出认证方式和令牌，同时让 Swagger 显示认证入口。
# auto_error=False 让我们能够统一返回自己的 401 错误信息。
bearer_scheme = HTTPBearer(
    auto_error=False,
)


def get_database_pool(
    request: Request,
) -> AsyncConnectionPool:
    """
    取得 FastAPI 启动时保存的共享 PostgreSQL 连接池。

    request.app.state 是 FastAPI 用来保存应用级共享对象的位置。
    db_pool 需要在主程序启动阶段提前放入其中。
    """

    # getattr 的第三个参数 None 是默认值：如果尚未保存
    # db_pool，就返回 None，而不是直接触发 AttributeError。
    pool = getattr(
        request.app.state,
        "db_pool",
        None,
    )
    if pool is None:
        raise RuntimeError(
            "Database pool is not initialized."
        )

    return pool


# Annotated 把“参数类型”和“参数如何获得”写在一起。
# 路由参数标注为 DatabasePool 后，FastAPI 会自动调用
# get_database_pool()，并把返回的连接池传给该参数。
DatabasePool = Annotated[
    AsyncConnectionPool,
    Depends(get_database_pool),
]


def _unauthorized(detail: str) -> HTTPException:
    """
    创建统一格式的 HTTP 401 响应。

    WWW-Authenticate: Bearer 告诉客户端：该接口要求使用
    Bearer 方式提交访问令牌。
    """

    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )


async def get_current_user(
    pool: DatabasePool,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> UserRecord:
    """
    验证 Bearer Token，并返回当前登录用户。

    需要登录的接口只要依赖这个函数，就不用各自重复解析 JWT。
    """

    if credentials is None:
        # 请求中完全没有 Authorization 请求头。
        raise _unauthorized(
            "Authentication credentials were not provided."
        )

    if credentials.scheme.lower() != "bearer":
        # 请求提供了认证信息，但使用的不是 Bearer 方案。
        raise _unauthorized(
            "Unsupported authentication scheme."
        )

    try:
        # credentials.credentials 是 Bearer 后面的 JWT 字符串。
        # 解码成功后得到该令牌所属用户的 UUID。
        user_id = decode_access_token(
            credentials.credentials
        )
    except InvalidAccessTokenError as error:
        raise _unauthorized(
            "Access token is invalid or expired."
        ) from error

    user = await get_user_by_id(
        pool,
        user_id,
    )
    if user is None:
        # JWT 本身虽然有效，但对应用户可能已经从数据库删除。
        raise _unauthorized(
            "The user belonging to this token no longer exists."
        )

    return user


# 路由参数标注为 CurrentUser 后，FastAPI 会先执行
# get_current_user()；验证成功才会进入真正的接口函数。
CurrentUser = Annotated[
    UserRecord,
    Depends(get_current_user),
]
