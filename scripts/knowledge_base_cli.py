#!/usr/bin/env python3
"""
知识库命令行工具
"""

import asyncio
import argparse
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.knowledge_base.knowledge_base_manager import KnowledgeBaseManager
from src.utils.async_utils import safe_async_run, is_async_context


async def add_file_command(file_path: str):
    """添加文件命令"""
    print(f"🚀 开始添加文件: {file_path}")
    kb_manager = KnowledgeBaseManager()
    result = await kb_manager.add_file(file_path)
    
    if result.get("success", False):
        print(f"✅ 文件添加成功!")
        print(f"   文件路径: {result['file_path']}")
        print(f"   总分块数: {result['total_chunks']}")
        print(f"   有效分块: {result['valid_chunks']}")
        print(f"   成功添加: {result.get('added_count', 'N/A')}")
    else:
        print(f"❌ 文件添加失败: {result.get('message', result.get('error', 'Unknown error'))}")


async def add_directory_command(directory_path: str, recursive: bool = True):
    """添加目录命令"""
    print(f"🚀 开始添加目录: {directory_path}")
    kb_manager = KnowledgeBaseManager()
    result = await kb_manager.add_directory(directory_path, recursive)
    
    if result.get("success", False):
        print(f"✅ 目录添加成功!")
        print(f"   目录路径: {result['directory_path']}")
        
        doc_summary = result.get("document_summary", {})
        print(f"   处理文件: {doc_summary.get('total_files', 0)} 个")
        print(f"   总分块数: {doc_summary.get('total_chunks', 0)} 个")
        print(f"   文件大小: {doc_summary.get('total_size_mb', 0)} MB")
        print(f"   成功添加: {result.get('added_count', 'N/A')}")
    else:
        print(f"❌ 目录添加失败: {result.get('message', result.get('error', 'Unknown error'))}")


async def search_command(query: str, k: int = 5, include_scores: bool = False):
    """搜索命令"""
    print(f"🔍 搜索: {query}")
    kb_manager = KnowledgeBaseManager()
    result = await kb_manager.search(query, k, include_scores)
    
    if result.get("success", False):
        print(f"✅ 找到 {len(result['results'])} 个相关结果:")
        
        for i, item in enumerate(result["results"], 1):
            print(f"\n📄 结果 {i}:")
            if include_scores:
                print(f"   相似度: {item['score']:.4f}")
            print(f"   来源: {item['metadata'].get('source', 'unknown')}")
            print(f"   内容: {item['content'][:200]}...")
    else:
        print(f"❌ 搜索失败: {result.get('message', result.get('error', 'Unknown error'))}")


def stats_command():
    """统计信息命令"""
    print("📊 知识库统计信息:")
    kb_manager = KnowledgeBaseManager()
    stats = kb_manager.get_knowledge_base_stats()
    
    if "error" not in stats:
        vector_stats = stats.get("vector_store", {})
        processing_stats = stats.get("processing", {})
        
        print(f"   向量存储:")
        print(f"     集合名称: {vector_stats.get('collection_name', 'N/A')}")
        print(f"     文档数量: {vector_stats.get('document_count', 'N/A')}")
        
        print(f"   处理统计:")
        print(f"     总操作数: {processing_stats.get('total_operations', 0)}")
        print(f"     成功操作: {processing_stats.get('successful_operations', 0)}")
        print(f"     成功率: {processing_stats.get('success_rate', 0):.1f}%")
        print(f"     最后更新: {processing_stats.get('last_updated', 'None')}")
    else:
        print(f"❌ 获取统计信息失败: {stats.get('message', 'Unknown error')}")


async def async_main():
    """异步主函数"""
    parser = argparse.ArgumentParser(description="知识库管理工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 添加文件命令
    add_file_parser = subparsers.add_parser("add-file", help="添加单个文件")
    add_file_parser.add_argument("file_path", help="文件路径")
    
    # 添加目录命令
    add_dir_parser = subparsers.add_parser("add-dir", help="添加目录")
    add_dir_parser.add_argument("directory_path", help="目录路径")
    add_dir_parser.add_argument("--no-recursive", action="store_true", 
                               help="不递归处理子目录")
    
    # 搜索命令
    search_parser = subparsers.add_parser("search", help="搜索知识库")
    search_parser.add_argument("query", help="搜索查询")
    search_parser.add_argument("-k", "--top-k", type=int, default=5, 
                              help="返回结果数量")
    search_parser.add_argument("--scores", action="store_true", 
                              help="显示相似度分数")
    
    # 统计命令
    subparsers.add_parser("stats", help="显示知识库统计信息")
    
    args = parser.parse_args()
    
    if args.command == "add-file":
        await add_file_command(args.file_path)
    elif args.command == "add-dir":
        recursive = not args.no_recursive
        await add_directory_command(args.directory_path, recursive)
    elif args.command == "search":
        await search_command(args.query, args.top_k, args.scores)
    elif args.command == "stats":
        stats_command()
    else:
        parser.print_help()


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