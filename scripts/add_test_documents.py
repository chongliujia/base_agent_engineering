#!/usr/bin/env python3
"""
添加测试文档到知识库
"""
import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.knowledge_base.knowledge_base_manager import KnowledgeBaseManager
from src.utils.async_utils import safe_async_run, is_async_context

def create_test_documents():
    """创建一些测试文档"""
    test_docs_dir = project_root / "test_documents"
    test_docs_dir.mkdir(exist_ok=True)
    
    # 创建测试文本文件
    test_files = [
        {
            "name": "ai_introduction.txt",
            "content": """
人工智能简介

人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，旨在创建能够执行通常需要人类智能的任务的系统。

主要领域包括：
1. 机器学习 - 让计算机从数据中学习
2. 自然语言处理 - 理解和生成人类语言
3. 计算机视觉 - 理解和分析图像
4. 机器人学 - 创建能够与物理世界交互的系统

AI 的应用非常广泛，包括搜索引擎、推荐系统、自动驾驶汽车、医疗诊断等。
            """
        },
        {
            "name": "machine_learning.txt", 
            "content": """
机器学习基础

机器学习是人工智能的一个子领域，专注于开发能够从数据中学习和改进的算法。

主要类型：
1. 监督学习 - 使用标记数据进行训练
2. 无监督学习 - 从未标记数据中发现模式
3. 强化学习 - 通过与环境交互学习最优策略

常见算法：
- 线性回归
- 决策树
- 神经网络
- 支持向量机
- 随机森林

机器学习在图像识别、语音识别、自然语言处理等领域有广泛应用。
            """
        },
        {
            "name": "deep_learning.txt",
            "content": """
深度学习概述

深度学习是机器学习的一个子集，使用多层神经网络来学习数据的复杂模式。

关键概念：
1. 神经网络 - 模拟人脑神经元的计算模型
2. 反向传播 - 训练神经网络的核心算法
3. 激活函数 - 引入非线性的数学函数
4. 梯度下降 - 优化网络参数的方法

主要架构：
- 卷积神经网络（CNN）- 用于图像处理
- 循环神经网络（RNN）- 用于序列数据
- 变换器（Transformer）- 用于自然语言处理
- 生成对抗网络（GAN）- 用于生成新数据

深度学习推动了AI的重大突破，包括图像识别、语音识别和自然语言理解。
            """
        },
        {
            "name": "langchain_guide.txt",
            "content": """
LangChain 使用指南

LangChain 是一个用于构建基于大语言模型（LLM）应用程序的框架。

核心组件：
1. Models - 语言模型接口
2. Prompts - 提示模板管理
3. Chains - 将组件链接在一起
4. Agents - 使用工具的智能代理
5. Memory - 对话记忆管理
6. Vector Stores - 向量数据库集成

主要特性：
- 模型无关性 - 支持多种LLM提供商
- 模块化设计 - 可组合的组件
- 内置工具 - 丰富的预构建工具
- 向量检索 - RAG应用支持

LangChain 使开发者能够快速构建复杂的AI应用，如聊天机器人、问答系统、文档分析工具等。
            """
        }
    ]
    
    for file_info in test_files:
        file_path = test_docs_dir / file_info["name"]
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_info["content"].strip())
        print(f"✅ 创建测试文件: {file_path}")
    
    return test_docs_dir

async def async_main():
    """异步主函数"""
    try:
        print("📝 创建测试文档...")
        test_docs_dir = create_test_documents()
        
        print("\n📚 初始化知识库管理器...")
        kb_manager = KnowledgeBaseManager()
        
        print(f"\n📁 添加测试文档目录: {test_docs_dir}")
        result = await kb_manager.add_directory(str(test_docs_dir))
        
        print(f"\n✅ 处理结果:")
        if result.get('success', False):
            print(f"   成功文件数: {result.get('success_count', 'N/A')}")
            print(f"   失败文件数: {result.get('error_count', 'N/A')}")
            print(f"   总文档数: {result.get('total_documents', 'N/A')}")
            
            if 'document_summary' in result:
                summary = result['document_summary']
                print(f"   处理的文件: {summary.get('total_files', 'N/A')}")
                print(f"   文档块数: {summary.get('total_chunks', 'N/A')}")
        else:
            print(f"   处理失败: {result.get('message', result.get('error', 'Unknown error'))}")
        
        if result.get('errors'):
            print(f"\n❌ 错误信息:")
            for error in result['errors']:
                print(f"   {error}")
        
        print(f"\n📊 知识库统计:")
        stats = kb_manager.get_knowledge_base_stats()
        
        if "error" not in stats:
            vector_stats = stats.get("vector_store_stats", {})
            processing_stats = stats.get("processing_stats", {})
            
            print(f"   向量存储:")
            print(f"     集合名称: {vector_stats.get('collection_name', 'N/A')}")
            print(f"     文档数量: {vector_stats.get('total_entities', 'N/A')}")
            
            print(f"   处理统计:")
            print(f"     总操作数: {processing_stats.get('total_operations', 0)}")
            print(f"     成功操作: {processing_stats.get('successful_operations', 0)}")
            print(f"     成功率: {processing_stats.get('success_rate', 0):.1f}%")
            print(f"     最后更新: {processing_stats.get('last_updated', 'None')}")
        else:
            print(f"❌ 获取统计信息失败: {stats.get('message', 'Unknown error')}")
        
        return 0
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

def main():
    """主函数 - 安全运行异步代码"""
    if is_async_context():
        # 如果已经在异步上下文中，直接返回协程
        print("⚠️ 检测到异步上下文，请直接使用 await async_main()")
        return async_main()
    else:
        # 不在异步上下文中，安全运行
        return safe_async_run(async_main())

if __name__ == "__main__":
    result = main()
    if asyncio.iscoroutine(result):
        # 如果返回的是协程，说明在异步上下文中
        print("请在异步环境中运行此脚本")
        sys.exit(1)
    else:
        sys.exit(result)