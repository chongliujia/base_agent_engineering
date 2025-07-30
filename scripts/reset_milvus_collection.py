#!/usr/bin/env python3
"""
重置 Milvus 集合，解决 schema 问题
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import get_settings
from pymilvus import connections, utility, Collection

def reset_milvus_collection():
    """重置 Milvus 集合"""
    print("🔄 开始重置 Milvus 集合...")
    
    settings = get_settings()
    
    try:
        # 连接到 Milvus
        print("🔗 连接到 Milvus...")
        connections.connect(
            alias="default",
            host=settings.milvus_host,
            port=settings.milvus_port,
            user=settings.milvus_user if settings.milvus_user else None,
            password=settings.milvus_password if settings.milvus_password else None
        )
        print("✅ Milvus 连接成功")
        
        # 检查现有集合
        collection_name = "knowledge_base"
        collections = utility.list_collections()
        print(f"📋 现有集合: {collections}")
        
        if collection_name in collections:
            print(f"🗑️ 删除现有集合: {collection_name}")
            utility.drop_collection(collection_name)
            print("✅ 集合删除成功")
        else:
            print(f"ℹ️ 集合 {collection_name} 不存在，无需删除")
        
        print("🎉 Milvus 集合重置完成！")
        print("\n💡 现在可以运行测试脚本，新集合将使用动态字段 schema")
        
        return True
        
    except Exception as e:
        print(f"❌ 重置失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 断开连接
        try:
            connections.disconnect("default")
            print("🔌 已断开 Milvus 连接")
        except:
            pass

def main():
    """主函数"""
    success = reset_milvus_collection()
    
    if success:
        print("\n🚀 下一步:")
        print("   1. 运行: python test_milvus_schema_fix.py")
        print("   2. 如果成功，运行: python scripts/add_test_documents.py")
    else:
        print("\n❌ 重置失败，请检查:")
        print("   1. Milvus 服务是否正常运行")
        print("   2. 连接配置是否正确")

if __name__ == "__main__":
    main()