# Contributing to Speedy Cache

我们非常欢迎并感谢您对Speedy Cache项目的贡献！本文档将指导您如何参与项目开发。

## 行为准则

本项目采用[Contributor Covenant](https://www.contributor-covenant.org/version/2/0/code_of_conduct/)行为准则。通过参与本项目，您同意遵守其条款。

## 如何贡献

### 报告Bug

如果您发现了bug，请创建一个issue，并包含以下信息：

1. Bug的简要描述
2. 重现步骤
3. 期望的行为
4. 实际的行为
5. 环境信息（操作系统、Python版本等）
6. 相关的日志输出
7. 可能的解决方案

### 提出新功能

如果您有新功能的建议，请创建一个issue，并包含以下信息：

1. 功能的详细描述
2. 为什么这个功能对项目有帮助
3. 可能的实现方案
4. 是否愿意参与实现

### Pull Request流程

1. Fork项目
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

### 开发指南

1. 克隆��目：

```bash
git clone https://github.com/yourusername/speedy-cache.git
cd speedy-cache
```

2. 创建虚拟环境：

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

3. 安装依赖：

```bash
pip install -r requirements.txt
```

4. 运行测试：

```bash
pytest
```

### 代码风格

- 使用[Black](https://github.com/psf/black)格式化代码
- 使用[isort](https://github.com/PyCQA/isort)排序导入
- 使用[mypy](https://github.com/python/mypy)进行类型检查
- 遵循[PEP 8](https://www.python.org/dev/peps/pep-0008/)编码规范

### 提交信息规范

提交信息应遵循以下格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型（type）：
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码风格更改
- refactor: 代码重构
- perf: 性能优化
- test: 测试相关
- chore: 构建过程或辅助工具的变动

### 文档

- 所有新功能都必须包含文档
- 更新现有功能时也要更新相关文档
- 文档应该清晰、准确、易于理解

### 测试

- 所有新功能都必须包含测试
- 修复bug时要添加相关的测试用例
- 保持测试覆盖率在80%以上

## 发布流程

1. 更新版本号
2. 更新CHANGELOG.md
3. 创建发布分��
4. 运行测试套件
5. 构建文档
6. 创建标签
7. 发布到PyPI

## 获取帮助

如果您需要帮助，可以：

1. 查看[文档](docs/README.md)
2. 创建issue
3. 发送邮件到maintainers@example.com

## 许可证

通过贡献您的代码，您同意将其授权给项目所使用的[MIT许可证](LICENSE)。 