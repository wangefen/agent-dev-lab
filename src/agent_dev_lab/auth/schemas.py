"""
认证接口的数据模型（Schemas）。

本文件使用 Pydantic 描述前端请求和后端响应的结构。FastAPI 会
根据这些模型校验输入、生成 Swagger 文档，并过滤不应返回给
前端的内部字段。这里只定义数据形状，不执行注册或登录逻辑。
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)


class UserRegisterRequest(BaseModel):
    """
    用户注册接口接收的数据。
    """

    # EmailStr 会检查邮箱格式是否基本合法。
    email: EmailStr

    # 暂时要求密码至少 8 个字符。
    # 最大长度用于避免异常大的请求消耗服务器资源。
    password: str = Field(
        min_length=8,
        max_length=128,
    )


class UserLoginRequest(BaseModel):
    """
    用户登录接口接收的数据。
    """

    # 登录时同样先验证邮箱的基本格式。
    email: EmailStr

    # 与注册密码使用相同的长度范围，异常输入会直接返回 422。
    password: str = Field(
        min_length=8,
        max_length=128,
    )


class UserResponse(BaseModel):
    """
    返回给前端的公开用户信息。

    这里绝对不能包含 password 或 password_hash。
    """

    # 允许以后直接从数据库对象或普通字典创建模型。
    model_config = ConfigDict(
        from_attributes=True,
    )

    # 后端注册时生成的用户唯一编号。
    id: UUID

    # 用户登录使用的邮箱。
    email: EmailStr

    # 用户注册时间。
    created_at: datetime


class TokenResponse(BaseModel):
    """
    注册或登录成功后返回给前端的数据。
    """

    # 前端后续访问接口时携带的 JWT。
    access_token: str

    # token_type 告诉前端应该怎样把 access_token 发送给后端。
    # Bearer 是 HTTP 的一种身份认证方式，不是 Python 数据类型，
    # 也不是 JWT 内部表示令牌用途的 type="access"。
    # 前端访问需要登录的接口时，应把令牌放进请求头：
    # Authorization: Bearer <access_token>
    #
    # Literal["bearer"] 表示这个字段只允许是固定字符串 "bearer"；
    # 后面的 = "bearer" 则为它设置默认值，创建响应时不用重复传入。
    # 简单区分：JWT 内部的 type="access" 表示令牌“用来做什么”，
    # 此处的 token_type="bearer" 表示客户端“怎样携带这枚令牌”。
    token_type: Literal["bearer"] = "bearer"

    # 同时返回当前用户的公开信息。
    user: UserResponse
