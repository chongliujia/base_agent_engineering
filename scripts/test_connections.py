#!/usr/bin/env python3
"""
Test various service connections
"""
import os
import sys
import redis
from pymilvus import connections, utility
from urllib.parse import urlparse

# Add project root directory to Python path
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import get_settings

def test_redis_connection():
    """Test Redis connection"""
    try:
        settings = get_settings()
        
        # Parse Redis URL
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
        print(f"✅ Redis connection successful ({host}:{port})")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

def test_milvus_connection():
    """Test Milvus connection"""
    try:
        settings = get_settings()
        connections.connect(
            alias="default",
            host=settings.milvus_host,
            port=settings.milvus_port,
            user=settings.milvus_user if settings.milvus_user else None,
            password=settings.milvus_password if settings.milvus_password else None
        )
        
        # Check connection
        if connections.has_connection("default"):
            print(f"✅ Milvus connection successful ({settings.milvus_host}:{settings.milvus_port})")
            
            # List collections
            collections = utility.list_collections()
            print(f"📋 Existing collections: {collections}")
            return True
        else:
            print("❌ Milvus connection failed")
            return False
    except Exception as e:
        print(f"❌ Milvus connection failed: {e}")
        return False

def main():
    """Main function"""
    print("🔍 Testing service connections...")
    print("-" * 50)
    
    redis_ok = test_redis_connection()
    milvus_ok = test_milvus_connection()
    
    print("-" * 50)
    if redis_ok and milvus_ok:
        print("🎉 All service connections are working!")
        return 0
    else:
        print("⚠️  Some service connections failed, please check Docker service status")
        return 1

if __name__ == "__main__":
    sys.exit(main())