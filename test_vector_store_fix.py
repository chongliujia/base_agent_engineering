#!/usr/bin/env python3
"""
测试修复后的向量存储管理器
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from langchain_core.documents import Document
from src.knowledge_base.vector_store_manager import VectorStoreManager

# 加载环境变量
load_dotenv()

async def test_vector_store():
    """测试向量存储管理器"""
    print("🔍 测试向量存储管理器...")
    
    try:
        # 初始化向量存储管理器
        vs_manager = VectorStoreManager()
        print("✅ 向量存储管理器初始化成功")
        
        # 创建测试文档
        test_docs = [
            Document(
                page_content="这是第一个测试文档，包含人工智能的基础知识。",
                metadata={"source": "test1.txt", "type": "test"}
            ),
            Document(
                page_content="这是第二个测试文档，介绍机器学习的基本概念。",
                metadata={"source": "test2.txt", "type": "test"}
            )
        ]
        
        print(f"📝 准备添加 {len(test_docs)} 个测试文档...")
        
        # 测试添加文档
        result = await vs_manager.add_documents(test_docs)
        
        print("📊 添加结果:")
        print(f"   成功: {result.get('success', False)}")
        print(f"   总文档数: {result.get('total_documents', 0)}")
        print(f"   成功添加: {result.get('added_count', 0)}")
        print(f"   失败数量: {result.get('failed_count', 0)}")
        print(f"   成功率: {result.get('success_rate', 0)}%")
        
        if result.get('success', False):
            print("✅ 文档添加成功！")
            
            # 测试搜索
            print("\n🔍 测试搜索功能...")
            search_results = await vs_manager.search_similar("人工智能", k=2)
            
            print(f"📋 搜索结果: {len(search_results)} 个文档")
            for i, doc in enumerate(search_results):
                print(f"   {i+1}. {doc.page_content[:50]}...")
        else:
            print("❌ 文档添加失败")
            if 'batch_results' in result:
                for batch_result in result['batch_results']:
                    if not batch_result.get('success', True):
                        print(f"   错误: {batch_result.get('error', 'Unknown error')}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 开始测试修复后的向量存储...")
    
    # 检查API密钥
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("❌ DASHSCOPE_API_KEY 环境变量未设置")
        exit(1)
    
    print(f"🔑 API Key: {api_key[:10]}...")
    
    # 运行测试
    success = asyncio.run(test_vector_store())
    
    if success:
        print("\n🎉 向量存储测试成功！现在可以运行原始脚本了。")
    else:
        print("\n💡 建议:")
        print("   1. 检查 Milvus 服务是否正常运行")
        print("   2. 检查网络连接")
        print("   3. 查看详细错误信息")