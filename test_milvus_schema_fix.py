#!/usr/bin/env python3
"""
测试修复后的 Milvus schema 配置
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import get_model_config
from src.knowledge_base.vector_store_manager import VectorStoreManager
from src.utils.async_utils import safe_async_run, is_async_context
from langchain_core.documents import Document

async def test_milvus_schema_fix():
    """测试修复后的 Milvus schema 配置"""
    print("🧪 开始测试修复后的 Milvus schema...")
    
    # 检查 API Key
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("❌ 未找到 DASHSCOPE_API_KEY 环境变量")
        return False
    
    print(f"🔑 API Key: {api_key[:10]}...")
    
    try:
        # 初始化向量存储管理器
        print("🔍 初始化向量存储管理器...")
        vector_manager = VectorStoreManager()
        print("✅ 向量存储管理器初始化成功")
        
        # 创建测试文档（包含完整的 metadata 字段，与 document_processor.py 保持一致）
        test_docs = [
            Document(
                page_content="这是第一个测试文档，包含人工智能的基础知识。人工智能是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。",
                metadata={
                    "source": "test1.txt",
                    "filename": "test1.txt",
                    "file_type": ".txt",
                    "file_size": 1024,
                    "file_hash": "abc123def456",
                    "created_time": "2024-01-01T00:00:00",
                    "modified_time": "2024-01-01T00:00:00",
                    "processed_time": "2024-01-01T00:00:00",
                    "chunk_id": 0,
                    "chunk_size": 89,
                    "split_time": "2024-01-01T00:00:00"
                }
            ),
            Document(
                page_content="这是第二个测试文档，讨论机器学习的应用。机器学习是人工智能的一个子集，它使计算机能够在没有明确编程的情况下学习和改进。",
                metadata={
                    "source": "test2.txt", 
                    "filename": "test2.txt",
                    "file_type": ".txt",
                    "file_size": 2048,
                    "file_hash": "def456ghi789",
                    "created_time": "2024-01-01T00:00:00",
                    "modified_time": "2024-01-01T00:00:00",
                    "processed_time": "2024-01-01T00:00:00",
                    "chunk_id": 0,
                    "chunk_size": 91,
                    "split_time": "2024-01-01T00:00:00"
                }
            )
        ]
        
        print(f"📝 准备添加 {len(test_docs)} 个测试文档...")
        
        # 添加文档到向量存储
        result = await vector_manager.add_documents(test_docs)
        
        if result["success"]:
            print("✅ 文档添加成功！")
            print(f"   成功添加: {result['added_count']} 个文档")
            print(f"   失败数量: {result['failed_count']} 个文档")
            print(f"   成功率: {result['success_rate']:.1%}")
            
            # 测试搜索功能
            print("\n🔍 测试搜索功能...")
            search_results = await vector_manager.search_similar("人工智能", k=2)
            
            print(f"📊 搜索结果: 找到 {len(search_results)} 个相关文档")
            for i, doc in enumerate(search_results, 1):
                print(f"   {i}. {doc.page_content[:50]}...")
                print(f"      文件名: {doc.metadata.get('filename', 'N/A')}")
                print(f"      来源: {doc.metadata.get('source', 'N/A')}")
                print(f"      文件哈希: {doc.metadata.get('file_hash', 'N/A')}")
            
            return True
        else:
            print("❌ 文档添加失败")
            print(f"   错误: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def async_main():
    """异步主函数"""
    success = await test_milvus_schema_fix()
    
    if success:
        print("\n🎉 Milvus schema 修复测试成功！")
        print("\n💡 建议:")
        print("   1. 现在可以运行原始脚本 scripts/add_test_documents.py")
        print("   2. 检查 Milvus 集合是否正确创建了动态字段")
    else:
        print("\n❌ Milvus schema 修复测试失败")
        print("\n💡 建议:")
        print("   1. 先运行: python reset_milvus_collection.py")
        print("   2. 检查 Milvus 服务是否正常运行")
        print("   3. 查看详细错误信息")

def main():
    """主函数 - 安全运行异步代码"""
    if is_async_context():
        print("⚠️ 检测到异步上下文，请直接使用 await async_main()")
        return async_main()
    else:
        return safe_async_run(async_main())

if __name__ == "__main__":
    result = main()
    if asyncio.iscoroutine(result):
        print("请在异步环境中运行此脚本")
        sys.exit(1)
    else:
        sys.exit(0 if result else 1)