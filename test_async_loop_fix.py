#!/usr/bin/env python3
"""
测试异步事件循环修复
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.async_utils import safe_async_run, is_async_context, AsyncLoopManager
from src.knowledge_base.vector_store_manager import VectorStoreManager
from langchain_core.documents import Document


async def test_nested_async_calls():
    """测试嵌套异步调用"""
    print("🧪 测试嵌套异步调用...")
    
    try:
        # 初始化向量存储管理器
        print("🔍 初始化向量存储管理器...")
        vector_manager = VectorStoreManager()
        print("✅ 向量存储管理器初始化成功")
        
        # 创建简单测试文档
        test_doc = Document(
            page_content="这是一个测试文档，用于验证异步事件循环修复。",
            metadata={
                "source": "test_async.txt",
                "filename": "test_async.txt",
                "file_type": ".txt",
                "file_size": 100,
                "file_hash": "test123",
                "created_time": "2024-01-01T00:00:00",
                "modified_time": "2024-01-01T00:00:00",
                "processed_time": "2024-01-01T00:00:00",
                "chunk_id": 0,
                "chunk_size": 30,
                "split_time": "2024-01-01T00:00:00"
            }
        )
        
        print("📝 添加测试文档...")
        result = await vector_manager.add_documents([test_doc])
        
        if result["success"]:
            print("✅ 文档添加成功！")
            print(f"   成功添加: {result['added_count']} 个文档")
            
            # 测试搜索
            print("🔍 测试搜索...")
            search_results = await vector_manager.search_similar("测试", k=1)
            
            if search_results:
                print("✅ 搜索成功！")
                print(f"   找到 {len(search_results)} 个结果")
                return True
            else:
                print("❌ 搜索失败")
                return False
        else:
            print("❌ 文档添加失败")
            print(f"   错误: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_loop_manager():
    """测试事件循环管理器"""
    print("\n🧪 测试事件循环管理器...")
    
    try:
        manager = AsyncLoopManager()
        
        # 测试获取当前循环
        loop = manager.get_or_create_loop()
        print(f"✅ 获取事件循环成功: {type(loop).__name__}")
        
        # 测试是否在异步上下文中
        in_async = is_async_context()
        print(f"✅ 异步上下文检测: {in_async}")
        
        return True
        
    except Exception as e:
        print(f"❌ 事件循环管理器测试失败: {e}")
        return False


async def async_main():
    """异步主函数"""
    print("🚀 开始测试异步事件循环修复...")
    
    # 检查 API Key
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("❌ 未找到 DASHSCOPE_API_KEY 环境变量")
        return False
    
    print(f"🔑 API Key: {api_key[:10]}...")
    
    # 测试事件循环管理器
    loop_test = await test_loop_manager()
    
    # 测试嵌套异步调用
    nested_test = await test_nested_async_calls()
    
    success = loop_test and nested_test
    
    if success:
        print("\n🎉 异步事件循环修复测试成功！")
        print("\n💡 修复要点:")
        print("   1. 使用 AsyncLoopManager 统一管理事件循环")
        print("   2. 使用 safe_async_run 安全运行异步函数")
        print("   3. 使用 is_async_context 检测异步上下文")
        print("   4. 在向量存储管理器中实现异步/同步回退机制")
    else:
        print("\n❌ 异步事件循环修复测试失败")
    
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