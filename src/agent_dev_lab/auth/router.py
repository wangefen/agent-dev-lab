"""
认证模块的 HTTP 路由层。

本文件定义前端能够调用的注册、登录和查询当前用户接口。它负责
接收并校验请求数据、调用 service.py 的业务函数，再把业务结果
转换成 HTTP 响应；密码处理和 SQL 查询不直接写在路由中。
"""

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from agent_dev_lab.auth.dependencies import (
    CurrentUser,
    DatabasePool,
)
from agent_dev_lab.auth.schemas import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from agent_dev_lab.auth.service import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    login_user,
    register_user,
)


# 这个模块中的所有接口都会自动带上 /auth 前缀，
# 并在 Swagger 文档中归入 Authentication 分组。
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: UserRegisterRequest,
    pool: DatabasePool,
) -> TokenResponse:
    """
    注册账号，成功后直接返回登录令牌。

    payload 由 FastAPI 根据 UserRegisterRequest 自动解析和校验；
    pool 由 dependencies.py 中的 DatabasePool 自动注入。
    """

    try:
        # 路由只传递数据，完整注册流程交给业务层处理。
        result = await register_user(
            pool=pool,
            email=str(payload.email),
            password=payload.password,
        )
    except EmailAlreadyRegisteredError as error:
        # 将业务层的“邮箱已注册”转换为 HTTP 409 冲突响应。
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
        ) from error

    # UserResponse 会过滤内部字段，不会把 password_hash 返回前端。
    return TokenResponse(
        access_token=result.access_token,
        user=UserResponse.model_validate(
            result.user
        ),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    payload: UserLoginRequest,
    pool: DatabasePool,
) -> TokenResponse:
    """
    使用邮箱和密码登录并取得新的访问令牌。

    登录失败统一返回“邮箱或密码不正确”，不会暴露邮箱是否存在。
    """

    try:
        # 密码验证和 JWT 签发都由 service.py 完成。
        result = await login_user(
            pool=pool,
            email=str(payload.email),
            password=payload.password,
        )
    except InvalidCredentialsError as error:
        # 401 表示当前请求没有通过身份认证。
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or password is incorrect.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from error

    return TokenResponse(
        access_token=result.access_token,
        user=UserResponse.model_validate(
            result.user
        ),
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
async def read_current_user(
    current_user: CurrentUser,
) -> UserResponse:
    """
    根据 Bearer Token 返回当前登录用户。

    CurrentUser 会在进入函数前自动验证 JWT 并查询数据库；
    验证失败时，dependencies.py 会直接返回 HTTP 401。
    """

    # 把内部 UserRecord 转换为允许公开的 UserResponse。
    return UserResponse.model_validate(
        current_user
    )
