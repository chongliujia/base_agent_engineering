#!/usr/bin/env python3
"""
测试隔离异步事件循环修复
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.async_utils import safe_async_run, is_async_context, run_in_isolated_loop_async
from src.knowledge_base.vector_store_manager import VectorStoreManager
from langchain_core.documents import Document


async def test_isolated_async_operations():
    """测试隔离的异步操作"""
    print("🧪 测试隔离的异步操作...")
    
    try:
        # 初始化向量存储管理器
        print("🔍 初始化向量存储管理器...")
        vector_manager = VectorStoreManager()
        print("✅ 向量存储管理器初始化成功")
        
        # 创建简单测试文档
        test_doc = Document(
            page_content="这是一个测试文档，用于验证隔离异步事件循环修复。包含人工智能和机器学习的内容。",
            metadata={
                "source": "test_isolated.txt",
                "filename": "test_isolated.txt",
                "file_type": ".txt",
                "file_size": 150,
                "file_hash": "isolated123",
                "created_time": "2024-01-01T00:00:00",
                "modified_time": "2024-01-01T00:00:00",
                "processed_time": "2024-01-01T00:00:00",
                "chunk_id": 0,
                "chunk_size": 50,
                "split_time": "2024-01-01T00:00:00"
            }
        )
        
        print("📝 添加测试文档（使用隔离事件循环）...")
        result = await vector_manager.add_documents([test_doc])
        
        if result["success"]:
            print("✅ 文档添加成功！")
            print(f"   成功添加: {result['added_count']} 个文档")
            print(f"   成功率: {result['success_rate']}%")
            
            # 测试搜索
            print("🔍 测试搜索（使用隔离事件循环）...")
            search_results = await vector_manager.search_similar("人工智能", k=1)
            
            if search_results:
                print("✅ 搜索成功！")
                print(f"   找到 {len(search_results)} 个结果")
                print(f"   内容预览: {search_results[0].page_content[:50]}...")
                
                # 测试带分数的搜索
                print("🔍 测试带分数搜索...")
                scored_results = await vector_manager.search_with_scores("机器学习", k=1)
                
                if scored_results:
                    print("✅ 带分数搜索成功！")
                    print(f"   找到 {len(scored_results)} 个结果")
                    if scored_results:
                        doc, score = scored_results[0]
                        print(f"   相似度分数: {score:.4f}")
                        print(f"   内容预览: {doc.page_content[:50]}...")
                    return True
                else:
                    print("❌ 带分数搜索失败")
                    return False
            else:
                print("❌ 搜索失败")
                return False
        else:
            print("❌ 文档添加失败")
            print(f"   错误: {result.get('message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_concurrent_operations():
    """测试并发操作"""
    print("\n🧪 测试并发操作...")
    
    try:
        vector_manager = VectorStoreManager()
        
        # 创建多个测试文档
        test_docs = []
        for i in range(3):
            doc = Document(
                page_content=f"这是第{i+1}个并发测试文档，包含不同的内容。",
                metadata={
                    "source": f"concurrent_test_{i+1}.txt",
                    "filename": f"concurrent_test_{i+1}.txt",
                    "file_type": ".txt",
                    "file_size": 100 + i * 10,
                    "file_hash": f"concurrent{i+1}",
                    "created_time": "2024-01-01T00:00:00",
                    "modified_time": "2024-01-01T00:00:00",
                    "processed_time": "2024-01-01T00:00:00",
                    "chunk_id": i,
                    "chunk_size": 30,
                    "split_time": "2024-01-01T00:00:00"
                }
            )
            test_docs.append(doc)
        
        print("📝 并发添加多个文档...")
        
        # 并发执行多个添加操作
        tasks = []
        for doc in test_docs:
            task = vector_manager.add_documents([doc])
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"❌ 文档 {i+1} 添加失败: {result}")
            elif result.get("success", False):
                print(f"✅ 文档 {i+1} 添加成功")
                success_count += 1
            else:
                print(f"❌ 文档 {i+1} 添加失败: {result.get('message', 'Unknown error')}")
        
        if success_count == len(test_docs):
            print(f"✅ 所有 {len(test_docs)} 个文档并发添加成功！")
            
            # 测试并发搜索
            print("🔍 测试并发搜索...")
            search_tasks = [
                vector_manager.search_similar("第1个", k=1),
                vector_manager.search_similar("第2个", k=1),
                vector_manager.search_similar("第3个", k=1)
            ]
            
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            search_success_count = 0
            for i, result in enumerate(search_results):
                if isinstance(result, Exception):
                    print(f"❌ 搜索 {i+1} 失败: {result}")
                elif result:
                    print(f"✅ 搜索 {i+1} 成功，找到 {len(result)} 个结果")
                    search_success_count += 1
                else:
                    print(f"❌ 搜索 {i+1} 无结果")
            
            return search_success_count == len(search_tasks)
        else:
            print(f"❌ 只有 {success_count}/{len(test_docs)} 个文档添加成功")
            return False
            
    except Exception as e:
        print(f"❌ 并发测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def async_main():
    """异步主函数"""
    print("🚀 开始测试隔离异步事件循环修复...")
    
    # 检查 API Key
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("❌ 未找到 DASHSCOPE_API_KEY 环境变量")
        return False
    
    print(f"🔑 API Key: {api_key[:10]}...")
    
    # 测试隔离异步操作
    isolated_test = await test_isolated_async_operations()
    
    # 测试并发操作
    concurrent_test = await test_concurrent_operations()
    
    success = isolated_test and concurrent_test
    
    if success:
        print("\n🎉 隔离异步事件循环修复测试成功！")
        print("\n💡 修复要点:")
        print("   1. 使用隔离的事件循环避免冲突")
        print("   2. 在独立线程中运行 LangChain 异步方法")
        print("   3. 多层回退机制确保功能稳定")
        print("   4. 支持并发操作而不会相互干扰")
        print("\n🔧 技术细节:")
        print("   - run_in_isolated_loop_async: 在隔离线程中运行异步代码")
        print("   - ThreadPoolExecutor: 管理隔离线程池")
        print("   - 异步/同步双重回退机制")
    else:
        print("\n❌ 隔离异步事件循环修复测试失败")
    
    return success


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