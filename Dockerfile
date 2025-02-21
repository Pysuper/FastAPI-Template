# 使用Python 3.11作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.4.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false

# 安装系统依赖
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安装Poetry
RUN curl -sSL https://install.python-poetry.org | python -

# 添加Poetry到PATH
ENV PATH="${POETRY_HOME}/bin:${PATH}"

# 复制项目文件
COPY pyproject.toml poetry.lock ./
COPY core core/
COPY tests tests/

# 安装项目依赖
RUN poetry install --no-dev --no-interaction --no-ansi

# 运行测试
CMD ["poetry", "run", "pytest"] 