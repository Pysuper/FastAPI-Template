# 目录结构

```bash
security/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── base.py          # 基础安全类
│   ├── constants.py     # 安全常量定义
│   └── exceptions.py    # 安全相关异常
├── auth/
│   ├── __init__.py
│   ├── rbac.py         # RBAC实现
│   ├── permission.py    # 权限管理
│   └── cache.py        # 权限缓存
├── audit/
│   ├── __init__.py
│   ├── base.py         # 基础审计类
│   ├── api.py          # API审计
│   └── permission.py   # 权限审计
├── protection/
│   ├── __init__.py
│   ├── sql.py          # SQL注入防护
│   ├── rate_limit.py   # 请求限制
│   └── encryption.py   # 数据加密
└── password/
    ├── __init__.py
    ├── policy.py       # 密码策略
    ├── hash.py         # 密码哈希
    └── validation.py   # 密码验证
```

