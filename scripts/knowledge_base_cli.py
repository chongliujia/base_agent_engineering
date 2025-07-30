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


async def add_file_command(file_path: str, collection_name: str = None, chunking_strategy: str = None, strategy_params: dict = None):
    """添加文件命令（支持分块策略选择）"""
    print(f"🚀 开始添加文件: {file_path}")
    if collection_name:
        print(f"   目标知识库: {collection_name}")
    if chunking_strategy:
        print(f"   分块策略: {chunking_strategy}")
    
    kb_manager = KnowledgeBaseManager(
        collection_name=collection_name,
        chunking_strategy=chunking_strategy or "recursive",
        strategy_params=strategy_params or {}
    )
    result = await kb_manager.add_file(
        file_path,
        chunking_strategy=chunking_strategy,
        strategy_params=strategy_params
    )
    
    if result.get("success", False):
        print(f"✅ 文件添加成功!")
        print(f"   文件路径: {result['file_path']}")
        print(f"   总分块数: {result['total_chunks']}")
        print(f"   有效分块: {result['valid_chunks']}")
        print(f"   成功添加: {result.get('added_count', 'N/A')}")
    else:
        print(f"❌ 文件添加失败: {result.get('message', result.get('error', 'Unknown error'))}")


async def add_directory_command(directory_path: str, recursive: bool = True, collection_name: str = None, 
                               auto_strategy: bool = True, chunking_strategy: str = None, strategy_params: dict = None):
    """添加目录命令（支持自动策略选择和分块策略选择）"""
    print(f"🚀 开始添加目录: {directory_path}")
    if collection_name:
        print(f"   目标知识库: {collection_name}")
    if chunking_strategy:
        print(f"   分块策略: {chunking_strategy}")
    elif auto_strategy:
        print(f"   策略模式: 自动选择（根据文件类型）")
    
    kb_manager = KnowledgeBaseManager(
        collection_name=collection_name,
        chunking_strategy=chunking_strategy or "recursive",
        strategy_params=strategy_params or {}
    )
    result = await kb_manager.add_directory(
        directory_path, 
        recursive=recursive,
        auto_strategy=auto_strategy,
        chunking_strategy=chunking_strategy,
        strategy_params=strategy_params
    )
    
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


async def search_command(query: str, k: int = 5, include_scores: bool = False, collection_name: str = None):
    """搜索命令"""
    print(f"🔍 搜索: {query}")
    if collection_name:
        print(f"   搜索知识库: {collection_name}")
    kb_manager = KnowledgeBaseManager(collection_name=collection_name)
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


async def stats_command(collection_name: str = None):
    """统计信息命令"""
    if collection_name:
        print(f"📊 知识库统计信息 ({collection_name}):")
    else:
        print("📊 知识库统计信息:")
    
    kb_manager = KnowledgeBaseManager(collection_name=collection_name)
    stats = kb_manager.get_knowledge_base_stats()
    
    if "error" not in stats:
        vector_stats = stats.get("vector_store_stats", {})
        processing_stats = stats.get("processing_stats", {})
        
        print(f"   向量存储:")
        print(f"     集合名称: {vector_stats.get('collection_name', 'N/A')}")
        print(f"     文档数量: {vector_stats.get('total_entities', 'N/A')}")
        if "description" in vector_stats:
            print(f"     描述: {vector_stats.get('description', 'N/A')}")
        if "status" in vector_stats:
            print(f"     状态: {vector_stats.get('status', 'N/A')}")
        
        print(f"   处理统计:")
        print(f"     总操作数: {processing_stats.get('total_operations', 0)}")
        print(f"     成功操作: {processing_stats.get('successful_operations', 0)}")
        print(f"     成功率: {processing_stats.get('success_rate', 0):.1f}%")
        print(f"     最后更新: {processing_stats.get('last_updated', 'None')}")
        
        # 显示知识库路径信息
        print(f"   存储路径:")
        print(f"     知识库目录: {stats.get('knowledge_base_path', 'N/A')}")
        print(f"     元数据目录: {stats.get('metadata_path', 'N/A')}")
    else:
        print(f"❌ 获取统计信息失败: {stats.get('message', 'Unknown error')}")
        
    # 尝试进行一次搜索测试来验证系统状态
    print(f"\n🔍 系统状态测试:")
    try:
        test_results = await kb_manager.search("测试", k=1, include_scores=False)
        if test_results.get("success", False):
            results_count = len(test_results.get("results", []))
            print(f"     搜索功能: ✅ 正常 (找到 {results_count} 个结果)")
        else:
            print(f"     搜索功能: ❌ 异常 - {test_results.get('message', 'Unknown error')}")
    except Exception as e:
        print(f"     搜索功能: ❌ 测试失败 - {str(e)}")


async def list_kb_command():
    """列出所有知识库命令"""
    print("📚 知识库列表:")
    collections = KnowledgeBaseManager.list_knowledge_bases()
    
    if not collections:
        print("   (无知识库)")
    else:
        for i, collection in enumerate(collections, 1):
            print(f"   {i}. {collection}")
    
    print(f"\n总计: {len(collections)} 个知识库")


async def list_strategies_command():
    """列出所有可用分块策略命令"""
    from src.knowledge_base.document_processor import DocumentProcessor
    
    print("🧠 可用分块策略:")
    strategies = DocumentProcessor.list_available_strategies()
    
    if not strategies:
        print("   (无可用策略)")
        return
    
    for i, (name, info) in enumerate(strategies.items(), 1):
        print(f"\n{i}. {name}")
        if info.get("available", True):
            print(f"   描述: {info.get('description', 'N/A')}")
            
            # 显示参数
            params = info.get("parameters", {})
            if params:
                print(f"   参数: {params}")
            
            # 显示适用场景
            suitable_for = info.get("suitable_for", [])
            if suitable_for:
                print(f"   适用: {', '.join(suitable_for)}")
            
            # 显示优势
            advantages = info.get("advantages", [])
            if advantages:
                print(f"   优势: {', '.join(advantages)}")
            
            # 显示要求
            requirements = info.get("requirements", [])
            if requirements:
                print(f"   要求: {', '.join(requirements)}")
        else:
            print(f"   状态: 不可用 - {info.get('description', 'Unknown error')}")
    
    print(f"\n总计: {len(strategies)} 个策略")


async def recommend_strategy_command(file_type: str = None, use_case: str = None):
    """获取策略推荐命令"""
    from src.knowledge_base.document_processor import DocumentProcessor
    
    print("🎯 策略推荐:")
    
    if file_type:
        strategy = DocumentProcessor.get_strategy_recommendation(file_type=file_type)
        print(f"   文件类型 '{file_type}' 的推荐策略: {strategy}")
    
    if use_case:
        strategy = DocumentProcessor.get_strategy_recommendation(use_case=use_case)
        print(f"   使用场景 '{use_case}' 的推荐策略: {strategy}")
    
    if not file_type and not use_case:
        print("   请指定文件类型或使用场景")
        print("   示例: --file-type pdf 或 --use-case knowledge_base")


async def create_kb_command(collection_name: str, chunking_strategy: str = None, strategy_params: dict = None):
    """创建知识库命令（支持指定默认分块策略）"""
    print(f"🚀 创建知识库: {collection_name}")
    if chunking_strategy:
        print(f"   默认分块策略: {chunking_strategy}")
    
    result = await KnowledgeBaseManager.create_knowledge_base(
        collection_name,
        chunking_strategy=chunking_strategy or "recursive",
        strategy_params=strategy_params or {}
    )
    
    if result.get("success", False):
        print(f"✅ 知识库创建成功!")
        print(f"   知识库名称: {result['collection_name']}")
        print(f"   存储路径: {result['path']}")
    else:
        print(f"❌ 知识库创建失败: {result.get('message', result.get('error', 'Unknown error'))}")


async def delete_kb_command(collection_name: str, confirm: bool = False):
    """删除知识库命令"""
    if not confirm:
        print(f"⚠️  确认要删除知识库 '{collection_name}' 吗？")
        print("   此操作将永久删除所有数据！")
        print("   如确认删除，请使用: --confirm 参数")
        return
    
    print(f"🗑️  删除知识库: {collection_name}")
    result = await KnowledgeBaseManager.delete_knowledge_base(collection_name, confirm=True)
    
    if result.get("success", False):
        print(f"✅ 知识库删除成功!")
        print(f"   已删除: {collection_name}")
    else:
        print(f"❌ 知识库删除失败: {result.get('message', result.get('error', 'Unknown error'))}")


def switch_kb_command(collection_name: str):
    """切换知识库命令"""
    print(f"🔄 切换知识库: {collection_name}")
    result = KnowledgeBaseManager.switch_knowledge_base(collection_name)
    
    if result.get("success", False):
        print(f"✅ 切换成功!")
        print(f"   当前知识库: {result['collection_name']}")
        if result.get("note"):
            print(f"   注意: {result['note']}")
    else:
        print(f"❌ 切换失败: {result.get('message', result.get('error', 'Unknown error'))}")


async def async_main():
    """异步主函数"""
    parser = argparse.ArgumentParser(description="知识库管理工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 添加全局参数
    parser.add_argument("--collection", "-c", help="指定知识库名称", dest="collection")
    
    # 添加文件命令
    add_file_parser = subparsers.add_parser("add-file", help="添加单个文件")
    add_file_parser.add_argument("file_path", help="文件路径")
    add_file_parser.add_argument("--strategy", "-s", help="分块策略 (recursive, token, semantic, character, code, format)")
    add_file_parser.add_argument("--chunk-size", type=int, help="分块大小")
    add_file_parser.add_argument("--chunk-overlap", type=int, help="分块重叠")
    add_file_parser.add_argument("--format-type", help="文件格式类型 (用于format策略)")
    add_file_parser.add_argument("--language", help="编程语言 (用于code策略)")
    
    # 添加目录命令
    add_dir_parser = subparsers.add_parser("add-dir", help="添加目录")
    add_dir_parser.add_argument("directory_path", help="目录路径")
    add_dir_parser.add_argument("--no-recursive", action="store_true", 
                               help="不递归处理子目录")
    add_dir_parser.add_argument("--no-auto-strategy", action="store_true",
                               help="不自动选择策略，使用统一策略")
    add_dir_parser.add_argument("--strategy", "-s", help="分块策略 (recursive, token, semantic, character, code, format)")
    add_dir_parser.add_argument("--chunk-size", type=int, help="分块大小")
    add_dir_parser.add_argument("--chunk-overlap", type=int, help="分块重叠")
    add_dir_parser.add_argument("--format-type", help="文件格式类型 (用于format策略)")
    add_dir_parser.add_argument("--language", help="编程语言 (用于code策略)")
    
    # 搜索命令
    search_parser = subparsers.add_parser("search", help="搜索知识库")
    search_parser.add_argument("query", help="搜索查询")
    search_parser.add_argument("-k", "--top-k", type=int, default=5, 
                              help="返回结果数量")
    search_parser.add_argument("--scores", action="store_true", 
                              help="显示相似度分数")
    
    # 统计命令
    subparsers.add_parser("stats", help="显示知识库统计信息")
    
    # 知识库管理命令
    subparsers.add_parser("list-kb", help="列出所有知识库")
    
    create_parser = subparsers.add_parser("create-kb", help="创建新知识库")
    create_parser.add_argument("name", help="知识库名称")
    create_parser.add_argument("--strategy", "-s", help="默认分块策略")
    create_parser.add_argument("--chunk-size", type=int, help="默认分块大小")
    create_parser.add_argument("--chunk-overlap", type=int, help="默认分块重叠")
    
    # 策略管理命令
    subparsers.add_parser("list-strategies", help="列出所有可用分块策略")
    
    recommend_parser = subparsers.add_parser("recommend-strategy", help="获取策略推荐")
    recommend_parser.add_argument("--file-type", help="文件类型 (pdf, docx, txt, md, py, js, etc.)")
    recommend_parser.add_argument("--use-case", help="使用场景 (general, llm_input, knowledge_base, code_analysis, fast_processing)")
    
    delete_parser = subparsers.add_parser("delete-kb", help="删除知识库")
    delete_parser.add_argument("name", help="知识库名称")
    delete_parser.add_argument("--confirm", action="store_true", help="确认删除")
    
    switch_parser = subparsers.add_parser("switch-kb", help="切换当前知识库")
    switch_parser.add_argument("name", help="知识库名称")
    
    args = parser.parse_args()
    
    # 获取集合名称（优先使用命令行参数）
    collection_name = getattr(args, 'collection', None)
    
    # 构建策略参数
    def build_strategy_params(args):
        params = {}
        if hasattr(args, 'chunk_size') and args.chunk_size:
            params['chunk_size'] = args.chunk_size
        if hasattr(args, 'chunk_overlap') and args.chunk_overlap:
            params['chunk_overlap'] = args.chunk_overlap
        if hasattr(args, 'format_type') and args.format_type:
            params['format_type'] = args.format_type
        if hasattr(args, 'language') and args.language:
            params['language'] = args.language
        return params
    
    if args.command == "add-file":
        strategy_params = build_strategy_params(args)
        await add_file_command(args.file_path, collection_name, args.strategy, strategy_params)
    elif args.command == "add-dir":
        recursive = not args.no_recursive
        auto_strategy = not args.no_auto_strategy
        strategy_params = build_strategy_params(args)
        await add_directory_command(args.directory_path, recursive, collection_name, 
                                   auto_strategy, args.strategy, strategy_params)
    elif args.command == "search":
        await search_command(args.query, args.top_k, args.scores, collection_name)
    elif args.command == "stats":
        await stats_command(collection_name)
    elif args.command == "list-kb":
        await list_kb_command()
    elif args.command == "create-kb":
        strategy_params = build_strategy_params(args)
        await create_kb_command(args.name, args.strategy, strategy_params)
    elif args.command == "delete-kb":
        await delete_kb_command(args.name, args.confirm)
    elif args.command == "switch-kb":
        switch_kb_command(args.name)
    elif args.command == "list-strategies":
        await list_strategies_command()
    elif args.command == "recommend-strategy":
        await recommend_strategy_command(args.file_type, args.use_case)
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