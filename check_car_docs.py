#!/usr/bin/env python3
"""
Check car_docs collection data
"""
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.knowledge_base.knowledge_base_manager import KnowledgeBaseManager
from config.settings import get_settings

async def check_car_docs():
    """Check car_docs collection data"""
    print("🔍 Checking car_docs collection...")
    
    try:
        # Create knowledge base manager for car_docs
        kb_manager = KnowledgeBaseManager(collection_name="car_docs")
        
        # Get statistics
        stats = kb_manager.get_knowledge_base_stats()
        print(f"📊 Knowledge base statistics:")
        print(f"   Collection: {stats.get('current_collection')}")
        print(f"   Vector store stats: {stats.get('vector_store_stats')}")
        print(f"   Processing stats: {stats.get('processing_stats')}")
        
        # Try a simple search
        print("\n🔍 Testing search functionality...")
        search_result = await kb_manager.search("汽车", k=3)
        
        if search_result.get("success"):
            results = search_result.get("results", [])
            print(f"✅ Search successful! Found {len(results)} results")
            for i, result in enumerate(results[:2], 1):
                content = result.get("content", "")
                metadata = result.get("metadata", {})
                print(f"   {i}. {content[:100]}...")
                print(f"      Source: {metadata.get('source', 'N/A')}")
        else:
            print(f"❌ Search failed: {search_result.get('error')}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error checking car_docs: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(check_car_docs())