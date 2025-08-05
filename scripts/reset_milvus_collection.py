#!/usr/bin/env python3
"""
Reset Milvus collection to resolve schema issues
"""

import os
import sys
from pathlib import Path

# Add project root directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import get_settings
from pymilvus import connections, utility, Collection

def reset_milvus_collection():
    """Reset Milvus collection"""
    print("🔄 Starting Milvus collection reset...")
    
    settings = get_settings()
    
    try:
        # Connect to Milvus
        print("🔗 Connecting to Milvus...")
        connections.connect(
            alias="default",
            host=settings.milvus_host,
            port=settings.milvus_port,
            user=settings.milvus_user if settings.milvus_user else None,
            password=settings.milvus_password if settings.milvus_password else None
        )
        print("✅ Milvus connection successful")
        
        # Check existing collections
        collection_name = "knowledge_base"
        collections = utility.list_collections()
        print(f"📋 Existing collections: {collections}")
        
        if collection_name in collections:
            print(f"🗑️ Dropping existing collection: {collection_name}")
            utility.drop_collection(collection_name)
            print("✅ Collection dropped successfully")
        else:
            print(f"ℹ️ Collection {collection_name} does not exist, no need to drop")
        
        print("🎉 Milvus collection reset completed!")
        print("\n💡 You can now run test scripts, new collection will use dynamic field schema")
        
        return True
        
    except Exception as e:
        print(f"❌ Reset failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Disconnect
        try:
            connections.disconnect("default")
            print("🔌 Disconnected from Milvus")
        except:
            pass

def main():
    """Main function"""
    success = reset_milvus_collection()
    
    if success:
        print("\n🚀 Next steps:")
        print("   1. Run: python test_milvus_schema_fix.py")
        print("   2. If successful, run: python scripts/add_test_documents.py")
    else:
        print("\n❌ Reset failed, please check:")
        print("   1. Whether Milvus service is running normally")
        print("   2. Whether connection configuration is correct")

if __name__ == "__main__":
    main()