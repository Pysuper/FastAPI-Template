# 目录结构

## 建议目录结构
```bash
exceptions/
├── __init__.py           # 导出所有异常类
├── base.py              # 基础异常类
├── http/                # HTTP相关异常
│   ├── __init__.py
│   ├── auth.py         # 认证相关异常
│   ├── validation.py   # 验证相关异常
│   └── client.py       # 客户端相关异常
├── business/           # 业务相关异常
│   ├── __init__.py
│   ├── user.py        # 用户相关异常
│   ├── order.py       # 订单相关异常
│   └── payment.py     # 支付相关异常
├── system/            # 系统相关异常
│   ├── __init__.py
│   ├── database.py    # 数据库异常
│   ├── cache.py       # 缓存异常
│   └── file.py        # 文件操作异常
├── third_party/       # 第三方服务异常
│   ├── __init__.py
│   ├── payment.py     # 支付服务异常
│   └── storage.py     # 存储服务异常
├── handlers/          # 异常处理器
│   ├── __init__.py
│   ├── http.py       # HTTP异常处理器
│   ├── business.py   # 业务异常处理器
│   └── system.py     # 系统异常处理器
└── codes/            # 错误码
    ├── __init__.py
    ├── base.py      # 错误码基类
    ├── http.py      # HTTP错误码
    ├── business.py  # 业务错误码
    └── system.py    # 系统错误码
```

## 当前目录结构
```bash
exceptions/
├── __init__.py
├── base.py              # 基础异常类
├── codes/              # 错误码管理
│   ├── __init__.py
│   └── base.py
├── http/               # HTTP异常
│   ├── __init__.py
│   ├── base.py
│   ├── auth.py
│   ├── validation.py
│   └── client.py
├── system/            # 系统异常
│   ├── __init__.py
│   ├── base.py
│   ├── database.py
│   └── cache.py
└── handlers/          # 异常处理器
    ├── __init__.py
    ├── base.py
    ├── http.py
    └── system.py
```

# 使用示例
## 代码

```python
# 抛出HTTP异常
from core.exceptions.http.auth import AuthenticationException

async def login(credentials: dict):
    if not valid_credentials(credentials):
        raise AuthenticationException(
            message="用户名或密码错误",
            details={"username": credentials["username"]},
            context={"login_attempts": get_login_attempts()}
        )

# 抛出系统异常
from core.exceptions.system.database import QueryException

async def get_user(user_id: int):
    try:
        return await db.query(User).filter_by(id=user_id).first()
    except SQLAlchemyError as e:
        raise QueryException(
            message="查询用户失败",
            details={"user_id": user_id},
            context={"query": str(e)}
        )

# 配置异常处理
from core.exceptions.middleware import setup_exception_handlers

app = FastAPI()
setup_exception_handlers(app)
```

## 响应
```JSON
{
    "code": "5001",
    "message": "认证失败",
    "details": {
        "username": "test_user",
        "login_attempts": 3
    }
}
```