#!/bin/bash

# 设置错误时退出
set -e

# 显示执行的命令
set -x

# 检查必要的命令是否存在
command -v docker >/dev/null 2>&1 || { echo "需要安装 docker"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "需要安装 docker-compose"; exit 1; }

# 创建必要的目录
mkdir -p logs uploads storage nginx/ssl prometheus/data grafana/data

# 生成自签名SSL证书（如果不存在）
if [ ! -f nginx/ssl/server.crt ]; then
    mkdir -p nginx/ssl
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/server.key -out nginx/ssl/server.crt \
        -subj "/C=CN/ST=Beijing/L=Beijing/O=Company/OU=IT/CN=localhost"
fi

# 停止并删除现有容器
docker-compose down

# 清理未使用的镜像和卷
docker system prune -f

# 构建新镜像
docker-compose build --no-cache

# 启动服务
docker-compose up -d

# 等待MySQL启动
echo "等待MySQL启动..."
sleep 30

# 执行数据库迁移
docker-compose exec app alembic upgrade head

# 检查服务健康状态
echo "检查服务健康状态..."
curl -k https://localhost/health || { echo "��务健康检查失败"; exit 1; }

# 显示运行状态
docker-compose ps

echo "部署完成!" 