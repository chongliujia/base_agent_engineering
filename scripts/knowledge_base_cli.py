#!/usr/bin/env python3
"""
Knowledge Base Command Line Tool

This script provides a command-line interface for managing knowledge bases,
including adding files/directories, searching, viewing statistics, listing knowledge bases,
and listing chunking strategies.

Features:
- Add single files or entire directories to knowledge base
- Search knowledge base content
- View knowledge base statistics
- List all available knowledge bases
- List all available chunking strategies
- Support for asynchronous operations
- Support for chunking strategy selection
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.knowledge_base.knowledge_base_manager import KnowledgeBaseManager
from src.utils.async_utils import safe_async_run, is_async_context


async def add_file_command(file_path: str, collection_name: str = None, 
                          chunking_strategy: str = None, strategy_params: dict = None):
    """Add file command"""
    print(f"📄 Adding file: {file_path}")
    if collection_name:
        print(f"   Target knowledge base: {collection_name}")
    if chunking_strategy:
        print(f"   Chunking strategy: {chunking_strategy}")
    
    try:
        result = await KnowledgeBaseManager.add_file_to_knowledge_base(
            file_path, 
            collection_name=collection_name,
            chunking_strategy=chunking_strategy,
            strategy_params=strategy_params or {}
        )
        
        if result.get("success", False):
            print(f"✅ File added successfully!")
            print(f"   File: {result['file_path']}")
            print(f"   Chunks: {result['chunks_count']}")
            print(f"   Knowledge base: {result['collection_name']}")
        else:
            print(f"❌ Failed to add file: {result.get('message', result.get('error', 'Unknown error'))}")
    except Exception as e:
        print(f"❌ Error adding file: {str(e)}")


async def add_directory_command(directory_path: str, recursive: bool = True, 
                               collection_name: str = None, auto_strategy: bool = True,
                               chunking_strategy: str = None, strategy_params: dict = None):
    """Add directory command"""
    print(f"📁 Adding directory: {directory_path}")
    print(f"   Recursive: {'Yes' if recursive else 'No'}")
    print(f"   Auto strategy: {'Yes' if auto_strategy else 'No'}")
    if collection_name:
        print(f"   Target knowledge base: {collection_name}")
    if chunking_strategy:
        print(f"   Chunking strategy: {chunking_strategy}")
    
    try:
        result = await KnowledgeBaseManager.add_directory_to_knowledge_base(
            directory_path, 
            recursive=recursive,
            collection_name=collection_name,
            auto_strategy=auto_strategy,
            chunking_strategy=chunking_strategy,
            strategy_params=strategy_params or {}
        )
        
        if result.get("success", False):
            print(f"✅ Directory added successfully!")
            print(f"   Directory: {result['directory_path']}")
            print(f"   Files processed: {result['files_count']}")
            print(f"   Total chunks: {result['total_chunks']}")
            print(f"   Knowledge base: {result['collection_name']}")
            
            # Display processing details
            if result.get('processing_details'):
                print(f"\n📊 Processing details:")
                for detail in result['processing_details']:
                    status = "✅" if detail['success'] else "❌"
                    print(f"   {status} {detail['file_path']} - {detail['chunks_count']} chunks")
                    if not detail['success']:
                        print(f"      Error: {detail.get('error', 'Unknown error')}")
        else:
            print(f"❌ Failed to add directory: {result.get('message', result.get('error', 'Unknown error'))}")
    except Exception as e:
        print(f"❌ Error adding directory: {str(e)}")


async def search_command(query: str, top_k: int = 5, show_scores: bool = False, 
                        collection_name: str = None):
    """Search command"""
    print(f"🔍 Searching: {query}")
    if collection_name:
        print(f"   Knowledge base: {collection_name}")
    print(f"   Return count: {top_k}")
    
    try:
        results = await KnowledgeBaseManager.search_knowledge_base(
            query, 
            top_k=top_k, 
            collection_name=collection_name
        )
        
        if results:
            print(f"\n📋 Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. 📄 {result.metadata.get('source', 'Unknown source')}")
                if show_scores:
                    print(f"   Similarity: {result.metadata.get('score', 'N/A')}")
                print(f"   Content: {result.page_content[:200]}...")
                if len(result.page_content) > 200:
                    print(f"   (Total length: {len(result.page_content)} characters)")
        else:
            print("❌ No results found")
    except Exception as e:
        print(f"❌ Search error: {str(e)}")


async def stats_command(collection_name: str = None):
    """Statistics command"""
    print("📊 Knowledge base statistics:")
    if collection_name:
        print(f"   Knowledge base: {collection_name}")
    
    try:
        stats = await KnowledgeBaseManager.get_knowledge_base_stats(collection_name)
        
        if stats:
            print(f"   Total documents: {stats.get('total_documents', 0)}")
            print(f"   Total chunks: {stats.get('total_chunks', 0)}")
            print(f"   Knowledge base name: {stats.get('collection_name', 'Unknown')}")
            
            # Display file type statistics
            if stats.get('file_types'):
                print(f"\n📁 File type distribution:")
                for file_type, count in stats['file_types'].items():
                    print(f"   {file_type}: {count} files")
        else:
            print("❌ Unable to get statistics")
    except Exception as e:
        print(f"❌ Statistics error: {str(e)}")


async def list_kb_command():
    """List knowledge bases command"""
    print("📚 Available knowledge bases:")
    
    try:
        knowledge_bases = await KnowledgeBaseManager.list_knowledge_bases()
        
        if knowledge_bases:
            for kb in knowledge_bases:
                status = "✅ Active" if kb.get('is_current', False) else "⚪ Available"
                print(f"   {status} {kb['name']}")
                if kb.get('path'):
                    print(f"      Path: {kb['path']}")
                if kb.get('description'):
                    print(f"      Description: {kb['description']}")
        else:
            print("   No knowledge bases found")
    except Exception as e:
        print(f"❌ List error: {str(e)}")


async def list_strategies_command():
    """List chunking strategies command"""
    from src.knowledge_base.chunking_strategies import ChunkingStrategyFactory
    
    print("🔧 Available chunking strategies:")
    
    strategies = ChunkingStrategyFactory.list_strategies()
    
    for strategy_name, info in strategies.items():
        print(f"\n📋 {strategy_name}")
        print(f"   Description: {info.get('description', 'No description')}")
        
        if info.get('available', True):
            print(f"   Status: Available")
            if info.get('parameters'):
                print(f"   Parameters: {', '.join(info['parameters'])}")
            if info.get('requirements'):
                requirements = [req for req in info['requirements'] if req]
                print(f"   Requirements: {', '.join(requirements)}")
        else:
            print(f"   Status: Unavailable - {info.get('description', 'Unknown error')}")
    
    print(f"\nTotal: {len(strategies)} strategies")


async def recommend_strategy_command(file_type: str = None, use_case: str = None):
    """Get strategy recommendation command"""
    from src.knowledge_base.document_processor import DocumentProcessor
    
    print("🎯 Strategy recommendations:")
    
    if file_type:
        strategy = DocumentProcessor.get_strategy_recommendation(file_type=file_type)
        print(f"   Recommended strategy for file type '{file_type}': {strategy}")
    
    if use_case:
        strategy = DocumentProcessor.get_strategy_recommendation(use_case=use_case)
        print(f"   Recommended strategy for use case '{use_case}': {strategy}")
    
    if not file_type and not use_case:
        print("   Please specify file type or use case")
        print("   Example: --file-type pdf or --use-case knowledge_base")


async def create_kb_command(collection_name: str, chunking_strategy: str = None, strategy_params: dict = None):
    """Create knowledge base command (supports specifying default chunking strategy)"""
    print(f"🚀 Creating knowledge base: {collection_name}")
    if chunking_strategy:
        print(f"   Default chunking strategy: {chunking_strategy}")
    
    result = await KnowledgeBaseManager.create_knowledge_base(
        collection_name,
        chunking_strategy=chunking_strategy or "recursive",
        strategy_params=strategy_params or {}
    )
    
    if result.get("success", False):
        print(f"✅ Knowledge base created successfully!")
        print(f"   Knowledge base name: {result['collection_name']}")
        print(f"   Storage path: {result['path']}")
    else:
        print(f"❌ Failed to create knowledge base: {result.get('message', result.get('error', 'Unknown error'))}")


async def delete_kb_command(collection_name: str, confirm: bool = False):
    """Delete knowledge base command"""
    if not confirm:
        print(f"⚠️  Are you sure you want to delete knowledge base '{collection_name}'?")
        print("   This operation will permanently delete all data!")
        print("   To confirm deletion, use: --confirm parameter")
        return
    
    print(f"🗑️  Deleting knowledge base: {collection_name}")
    result = await KnowledgeBaseManager.delete_knowledge_base(collection_name, confirm=True)
    
    if result.get("success", False):
        print(f"✅ Knowledge base deleted successfully!")
        print(f"   Deleted: {collection_name}")
    else:
        print(f"❌ Failed to delete knowledge base: {result.get('message', result.get('error', 'Unknown error'))}")


def switch_kb_command(collection_name: str):
    """Switch knowledge base command"""
    print(f"🔄 Switching knowledge base: {collection_name}")
    result = KnowledgeBaseManager.switch_knowledge_base(collection_name)
    
    if result.get("success", False):
        print(f"✅ Switch successful!")
        print(f"   Current knowledge base: {result['collection_name']}")
        if result.get("note"):
            print(f"   Note: {result['note']}")
    else:
        print(f"❌ Switch failed: {result.get('message', result.get('error', 'Unknown error'))}")


async def async_main():
    """Async main function"""
    parser = argparse.ArgumentParser(description="Knowledge Base Management Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Add global parameters
    parser.add_argument("--collection", "-c", help="Specify knowledge base name", dest="collection")
    
    # Add file command
    add_file_parser = subparsers.add_parser("add-file", help="Add a single file")
    add_file_parser.add_argument("file_path", help="File path")
    add_file_parser.add_argument("--strategy", "-s", help="Chunking strategy (recursive, token, semantic, character, code, format)")
    add_file_parser.add_argument("--chunk-size", type=int, help="Chunk size")
    add_file_parser.add_argument("--chunk-overlap", type=int, help="Chunk overlap")
    add_file_parser.add_argument("--format-type", help="File format type (for format strategy)")
    add_file_parser.add_argument("--language", help="Programming language (for code strategy)")
    
    # Add directory command
    add_dir_parser = subparsers.add_parser("add-dir", help="Add directory")
    add_dir_parser.add_argument("directory_path", help="Directory path")
    add_dir_parser.add_argument("--no-recursive", action="store_true", 
                               help="Do not recursively process subdirectories")
    add_dir_parser.add_argument("--no-auto-strategy", action="store_true",
                               help="Do not auto-select strategy, use unified strategy")
    add_dir_parser.add_argument("--strategy", "-s", help="Chunking strategy (recursive, token, semantic, character, code, format)")
    add_dir_parser.add_argument("--chunk-size", type=int, help="Chunk size")
    add_dir_parser.add_argument("--chunk-overlap", type=int, help="Chunk overlap")
    add_dir_parser.add_argument("--format-type", help="File format type (for format strategy)")
    add_dir_parser.add_argument("--language", help="Programming language (for code strategy)")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search knowledge base")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("-k", "--top-k", type=int, default=5, 
                              help="Number of results to return")
    search_parser.add_argument("--scores", action="store_true", 
                              help="Show similarity scores")
    
    # Statistics command
    subparsers.add_parser("stats", help="Show knowledge base statistics")
    
    # Knowledge base management commands
    subparsers.add_parser("list-kb", help="List all knowledge bases")
    
    create_parser = subparsers.add_parser("create-kb", help="Create new knowledge base")
    create_parser.add_argument("name", help="Knowledge base name")
    create_parser.add_argument("--strategy", "-s", help="Default chunking strategy")
    create_parser.add_argument("--chunk-size", type=int, help="Default chunk size")
    create_parser.add_argument("--chunk-overlap", type=int, help="Default chunk overlap")
    
    # Strategy management commands
    subparsers.add_parser("list-strategies", help="List all available chunking strategies")
    
    recommend_parser = subparsers.add_parser("recommend-strategy", help="Get strategy recommendations")
    recommend_parser.add_argument("--file-type", help="File type (pdf, docx, txt, md, py, js, etc.)")
    recommend_parser.add_argument("--use-case", help="Use case (general, llm_input, knowledge_base, code_analysis, fast_processing)")
    
    delete_parser = subparsers.add_parser("delete-kb", help="Delete knowledge base")
    delete_parser.add_argument("name", help="Knowledge base name")
    delete_parser.add_argument("--confirm", action="store_true", help="Confirm deletion")
    
    switch_parser = subparsers.add_parser("switch-kb", help="Switch current knowledge base")
    switch_parser.add_argument("name", help="Knowledge base name")
    
    args = parser.parse_args()
    
    # Get collection name (prioritize command line arguments)
    collection_name = getattr(args, 'collection', None)
    
    # Build strategy parameters
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
    """Main function - safely run async code"""
    if is_async_context():
        print("⚠️ Async context detected, please use await async_main() directly")
        return async_main()
    else:
        return safe_async_run(async_main())


if __name__ == "__main__":
    result = main()
    if asyncio.iscoroutine(result):
        print("Please run this script in an async environment")
        sys.exit(1)