#!/bin/bash

# 停止所有服务的脚本

echo "🛑 停止 Base Agent Engineering Docker 服务..."

# 停止所有服务
docker-compose down

echo "🧹 清理未使用的资源..."
docker system prune -f

echo "✅ 所有服务已停止！"