#!/bin/bash

# 启动所有服务的脚本

echo "🚀 启动 Base Agent Engineering Docker 服务..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker"
    exit 1
fi

# 创建网络（如果不存在）
docker network create base_agent_network 2>/dev/null || true

# 启动服务
echo "📦 启动基础服务 (Redis, Elasticsearch, Milvus)..."
docker-compose up -d redis elasticsearch etcd minio

echo "⏳ 等待基础服务启动..."
sleep 10

echo "🔍 启动 Milvus..."
docker-compose up -d milvus

echo "⏳ 等待 Milvus 启动..."
sleep 20

echo "🎨 启动 Attu 管理界面..."
docker-compose up -d attu

echo "✅ 所有服务已启动！"
echo ""
echo "📋 服务访问地址："
echo "  🔴 Redis:          localhost:6379"
echo "  🟡 Elasticsearch:  http://localhost:9200"
echo "  🟢 Milvus:         localhost:19530"
echo "  🔵 Attu 管理界面:   http://localhost:8889"
echo "  🟣 MinIO 控制台:   http://localhost:9001 (minioadmin/minioadmin)"
echo ""
echo "🔧 如需启动应用服务，运行："
echo "  docker-compose up -d app"
echo ""
echo "📊 查看服务状态："
echo "  docker-compose ps"
echo ""
echo "📝 查看日志："
echo "  docker-compose logs -f [service_name]"