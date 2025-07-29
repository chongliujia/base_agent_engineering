"""
知识库使用示例
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.knowledge_base.knowledge_base_manager import knowledge_base_manager


async def main():
    """知识库使用示例"""
    
    print("🚀 知识库管理示例")
    print("=" * 50)
    
    # 1. 添加单个文件示例
    print("\n📄 1. 添加单个文件示例")
    # 注意：请替换为实际存在的文件路径
    # result = await knowledge_base_manager.add_file("./examples/sample.pdf")
    # print(f"结果: {result}")
    
    # 2. 添加目录示例
    print("\n📁 2. 添加目录示例")
    # 注意：请替换为实际存在的目录路径
    # result = await knowledge_base_manager.add_directory("./knowledge_base")
    # print(f"结果: {result}")
    
    # 3. 搜索示例
    print("\n🔍 3. 搜索示例")
    search_result = await knowledge_base_manager.search("人工智能", k=3, include_scores=True)
    print(f"搜索结果: {search_result}")
    
    # 4. 获取统计信息
    print("\n📊 4. 知识库统计信息")
    stats = knowledge_base_manager.get_knowledge_base_stats()
    print(f"统计信息: {stats}")
    
    print("\n✅ 示例完成!")


if __name__ == "__main__":
    asyncio.run(main())