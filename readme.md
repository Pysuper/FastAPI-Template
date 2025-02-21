# Speedy

Speedy是一个现代化的Python Web后端框架，专注于高性能、可扩展性和开发效率。

## 🌟 特性

- 🚀 高性能异步处理
- 🛡️ 内置安全机制
- 📦 模块化设计
- 🔌 插件化架构
- 🎯 类型安全
- 📝 自动API文档
- 🔄 热重载支持
- 🐳 容器化部署

## 📁 项目结构

> core [核心功能模块](./docs/core/README.md)

```bash
Speedy/
├── api/ # API接口定义
│ ├── base/ # 基础API组件
│ └── v1/ # V1版本API接口
│
├── core/ # 核心功能模块
│ ├── cache/ # 缓存实现
│ ├── config/ # 配置管理
│ ├── db/ # 数据库操作
│ ├── decorators/ # 装饰器
│ ├── dependencies/ # 依赖注入
│ ├── exceptions/ # 异常处理
│ ├── I18n/ # 国际化
│ ├── interceptor/ # 拦截器
│ ├── loge/ # 日志系统
│ ├── middlewares/ # 中间件
│ ├── monitor/ # 监控系统
│ ├── rbac/ # 权限控制
│ ├── repositories/ # 数据仓储
│ ├── response/ # 响应处理
│ ├── security/ # 安全机制
│ ├── services/ # 核心服务
│ ├── strong/ # 增强功能
│ ├── tasks/ # 异步任务
│ ├── third/ # 第三方集成
│ └── utils/ # 工具函数
│
├── models/ # 数据模型
├── schemas/ # 数据验证
├── services/ # 业务服务
├── tests/ # 测试用例
├── utils/ # 通用工具
├── constants/ # 常量定义
├── docs/ # 项目文档
└── deploy/ # 部署配置
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Redis
- PostgreSQL

### 安装
```bash
# 克隆项目
git clone https://github.com/yourusername/speedy.git

# 安装依赖
poetry install

# 或使用pip
pip install -r requirements.txt
```

### 配置
```bash
# 复制环境变量模板
cp.env.example.env

# 修改.env文件
vi .env
```

### 运行
```bash
# 启动服务
poetry run start

# 或使用pip
python -m speedy start

# main
python mian.py
```

## 🔧 核心模块

### API (api/)
- `base/`: API基础组件
- `v1/`: V1版本API实现

### 核心功能 (core/)
- `cache/`: 缓存实现（Redis支持）
- `config/`: 配置管理系统
- `db/`: 数据库操作封装
- `security/`: 安全相关功能
- `middlewares/`: 中间件实现
- `monitor/`: 系统监控
- `rbac/`: 权限控制系统
- `tasks/`: 异步任务处理

### 业务层 (services/)
- 业务逻辑实现
- 服务编排
- 领域驱动设计

## 📚 文档

详细文档请参考 `docs/` 目录：
- API文档
- 开发指南
- 部署文档
- 贡献指南

## 🔒 安全特性

- RBAC权限控制
- JWT认证
- 请求频率限制
- SQL注入防护
- XSS防护
- CORS配置

## 🔧 开发工具

- Poetry: 依赖管理
- Black: 代码格式化
- Flake8: 代码检查
- MyPy: 类型检查
- Pytest: 单元测试
- Docker: 容器化

## 📈 性能优化

- 异步处理
- 缓存策略
- 数据库优化
- 连接池
- 负载均衡

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

[MIT License](LICENSE)

## 🔗 相关链接

- [文档](docs/)
- [变更日志](CHANGELOG.md)
- [贡献指南](CONTRIBUTING.md)

## 📞 联系我们

- Issue: [GitHub Issues](https://github.com/yourusername/speedy/issues)
- Email: small.spider.p@gmail.com

## 🌟 致谢

感谢所有贡献者的付出！


