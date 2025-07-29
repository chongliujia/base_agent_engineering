#!/usr/bin/env python3
"""
测试各种服务连接
"""
import os
import sys
import redis
from pymilvus import connections, utility
from urllib.parse import urlparse

# 添加项目根目录到 Python 路径
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import get_settings

def test_redis_connection():
    """测试 Redis 连接"""
    try:
        settings = get_settings()
        
        # 解析 Redis URL
        if settings.redis_url:
            parsed = urlparse(settings.redis_url)
            host = parsed.hostname or 'localhost'
            port = parsed.port or 6379
        else:
            host = 'localhost'
            port = 6379
        
        r = redis.Redis(
            host=host,
            port=port,
            password=settings.redis_password if settings.redis_password else None,
            decode_responses=True
        )
        r.ping()
        print(f"✅ Redis 连接成功 ({host}:{port})")
        return True
    except Exception as e:
        print(f"❌ Redis 连接失败: {e}")
        return False

def test_milvus_connection():
    """测试 Milvus 连接"""
    try:
        settings = get_settings()
        connections.connect(
            alias="default",
            host=settings.milvus_host,
            port=settings.milvus_port,
            user=settings.milvus_user if settings.milvus_user else None,
            password=settings.milvus_password if settings.milvus_password else None
        )
        
        # 检查连接
        if connections.has_connection("default"):
            print(f"✅ Milvus 连接成功 ({settings.milvus_host}:{settings.milvus_port})")
            
            # 列出集合
            collections = utility.list_collections()
            print(f"📋 现有集合: {collections}")
            return True
        else:
            print("❌ Milvus 连接失败")
            return False
    except Exception as e:
        print(f"❌ Milvus 连接失败: {e}")
        return False

def main():
    """主函数"""
    print("🔍 测试服务连接...")
    print("-" * 50)
    
    redis_ok = test_redis_connection()
    milvus_ok = test_milvus_connection()
    
    print("-" * 50)
    if redis_ok and milvus_ok:
        print("🎉 所有服务连接正常！")
        return 0
    else:
        print("⚠️  部分服务连接失败，请检查 Docker 服务状态")
        return 1

if __name__ == "__main__":
    sys.exit(main())