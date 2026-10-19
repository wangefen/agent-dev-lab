"""
用户注册、登录和身份认证模块。

一、各文件的职责

1. schemas.py
   定义接口接收和返回的数据格式，并使用 Pydantic 校验数据。

2. security.py
   负责密码散列、密码验证，以及 JWT 的生成和解析。

3. repository.py
   负责创建用户表，以及在 PostgreSQL 中保存和查询用户。

4. service.py
   负责组织注册和登录的业务流程，并调用 repository.py 与
   security.py 完成数据库操作和安全操作。

5. dependencies.py
   负责读取请求中的 Bearer Token、解析 JWT、查询用户，最后
   得到当前登录用户，供需要登录的接口使用。

6. router.py
   对外提供 /auth/register、/auth/login 和 /auth/me 接口，
   接收前端请求并调用 service.py 或 dependencies.py。

7. __init__.py
   表示 auth 是一个 Python 包，并集中记录整个认证模块的结构。


二、模块之间的主要调用方向

router.py
    ├── schemas.py                 校验请求和组织响应
    ├── service.py                 执行注册、登录业务
    │       ├── repository.py      保存或查询用户
    │       └── security.py        处理密码和 JWT
    └── dependencies.py            获取当前登录用户
            ├── security.py        解析并验证 JWT
            └── repository.py      根据 UUID 查询用户


三、用户注册的执行顺序

前端发送邮箱和密码
    → schemas.py 校验邮箱格式和密码长度
    → router.py 的 register() 接收请求
    → service.py 的 register_user() 组织注册流程
    → repository.py 检查邮箱是否已经存在
    → security.py 将明文密码散列成 password_hash
    → repository.py 把新用户保存到 PostgreSQL
    → security.py 根据用户 UUID 生成 JWT
    → router.py 返回 TokenResponse 给前端


四、用户登录的执行顺序

前端发送邮箱和密码
    → schemas.py 校验请求数据
    → router.py 的 login() 接收请求
    → service.py 的 login_user() 组织登录流程
    → repository.py 根据邮箱查询用户
    → security.py 验证密码是否匹配 password_hash
    → security.py 根据用户 UUID 生成新的 JWT
    → router.py 返回 TokenResponse 给前端


五、访问受保护接口的执行顺序

前端在请求头中携带 Authorization: Bearer <JWT>
    → dependencies.py 的 HTTPBearer 读取 JWT
    → security.py 验证 JWT 并取出 sub 中的用户 UUID
    → repository.py 根据 UUID 查询数据库中的用户
    → dependencies.py 得到 CurrentUser
    → router.py 的受保护接口处理请求并返回公开用户信息


六、接入主程序时需要完成的事情

auth 模块本身不创建 FastAPI 应用。要让这些接口真正可以访问，
主程序还需要：
1. 启动时调用 create_auth_tables() 创建 app_users 表；
2. 把数据库连接池保存为 app.state.db_pool；
3. 使用 app.include_router() 注册 auth.router 中的路由。
"""
