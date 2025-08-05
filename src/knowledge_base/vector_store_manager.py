#!/usr/bin/env python3
"""
Vector Store Manager - Manages document vectorization and storage
"""

import asyncio
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from config.settings import model_config
from src.utils.async_utils import run_in_isolated_loop_async, run_in_thread_pool


class VectorStoreManager:
    """Vector Store Manager - Supports dynamic collections"""
    
    def __init__(self, batch_size: int = 10, collection_name: str = None):
        self.collection_name = collection_name
        self.vector_store = model_config.get_vector_store(collection_name=collection_name)
        self.batch_size = batch_size
    
    async def add_documents(self, documents: List[Document], 
                          batch_size: Optional[int] = None) -> Dict[str, Any]:
        """Batch add documents to vector store"""
        if not documents:
            return {"success": False, "message": "No documents to add"}
        
        batch_size = batch_size or self.batch_size
        total_docs = len(documents)
        added_count = 0
        failed_count = 0
        results = []
        
        print(f"🚀 Starting vectorization of {total_docs} document chunks...")
        
        # Process in batches
        for i in range(0, total_docs, batch_size):
            batch = documents[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_docs + batch_size - 1) // batch_size
            
            print(f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} chunks)")
            
            try:
                # Use isolated event loop to avoid conflicts
                success = await self._add_batch_isolated(batch)
                
                if success:
                    added_count += len(batch)
                    results.append({
                        "batch": batch_num,
                        "success": True,
                        "count": len(batch),
                        "message": f"Successfully added {len(batch)} chunks"
                    })
                    print(f"✅ Batch {batch_num} completed")
                else:
                    failed_count += len(batch)
                    results.append({
                        "batch": batch_num,
                        "success": False,
                        "count": 0,
                        "error": "Add failed",
                        "message": f"Batch {batch_num} failed"
                    })
                    print(f"❌ Batch {batch_num} failed")
                
            except Exception as e:
                failed_count += len(batch)
                error_msg = f"Batch {batch_num} failed: {str(e)}"
                
                results.append({
                    "batch": batch_num,
                    "success": False,
                    "count": 0,
                    "error": str(e),
                    "message": error_msg
                })
                
                print(f"❌ {error_msg}")
        
        success_rate = (added_count / total_docs) * 100 if total_docs > 0 else 0
        
        summary = {
            "success": failed_count == 0,
            "total_documents": total_docs,
            "added_count": added_count,
            "failed_count": failed_count,
            "success_rate": round(success_rate, 2),
            "batch_results": results,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"\n📊 Vectorization completed:")
        print(f"  Total chunks: {total_docs}")
        print(f"  Successfully added: {added_count}")
        print(f"  Failed count: {failed_count}")
        print(f"  Success rate: {success_rate:.1f}%")
        
        return summary
    
    async def _add_batch_isolated(self, batch: List[Document]) -> bool:
        """Add batch in isolated thread, prioritize sync methods to avoid event loop conflicts"""
        try:
            # Primary strategy: Use sync method directly in thread pool
            try:
                await run_in_thread_pool(self.vector_store.add_documents, batch)
                return True
            except Exception as sync_e:
                print(f"⚠️ Sync method execution failed: {sync_e}")
                
                # Fallback strategy: Check for async method and try in current loop
                if hasattr(self.vector_store, 'aadd_documents'):
                    try:
                        await self.vector_store.aadd_documents(batch)
                        return True
                    except Exception as async_e:
                        print(f"⚠️ Async method also failed: {async_e}")
                        return False
                else:
                    return False
            
        except Exception as e:
            print(f"❌ Batch add completely failed: {e}")
            return False
    
    async def search_similar(self, query: str, k: int = 5, 
                           filter_metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Search similar documents, prioritize sync methods to avoid event loop conflicts"""
        try:
            # Primary strategy: Use sync method directly in thread pool
            try:
                if filter_metadata:
                    docs = await run_in_thread_pool(
                        self.vector_store.similarity_search, 
                        query, k, filter_metadata
                    )
                else:
                    docs = await run_in_thread_pool(
                        self.vector_store.similarity_search, query, k
                    )
                return docs if docs else []
                
            except Exception as sync_e:
                print(f"⚠️ Sync search method failed: {sync_e}")
                
                # Fallback strategy: Check for async method and try in current loop
                if hasattr(self.vector_store, 'asimilarity_search'):
                    try:
                        if filter_metadata:
                            docs = await self.vector_store.asimilarity_search(
                                query, k=k, filter=filter_metadata
                            )
                        else:
                            docs = await self.vector_store.asimilarity_search(query, k=k)
                        return docs if docs else []
                    except Exception as async_e:
                        print(f"⚠️ Async search method also failed: {async_e}")
                        return []
                else:
                    return []
            
        except Exception as e:
            print(f"❌ Search completely failed: {str(e)}")
            return []
    
    async def search_with_scores(self, query: str, k: int = 5) -> List[tuple]:
        """Search similar documents and return similarity scores, prioritize sync methods to avoid event loop conflicts"""
        try:
            # Primary strategy: Use sync method directly in thread pool
            try:
                docs_with_scores = await run_in_thread_pool(
                    self.vector_store.similarity_search_with_score, query, k
                )
                return docs_with_scores if docs_with_scores else []
                
            except Exception as sync_e:
                print(f"⚠️ Sync search with scores method failed: {sync_e}")
                
                # Fallback strategy: Check for async method and try in current loop
                if hasattr(self.vector_store, 'asimilarity_search_with_score'):
                    try:
                        docs_with_scores = await self.vector_store.asimilarity_search_with_score(query, k=k)
                        return docs_with_scores if docs_with_scores else []
                    except Exception as async_e:
                        print(f"⚠️ Async search with scores method also failed: {async_e}")
                        return []
                else:
                    return []
            
        except Exception as e:
            print(f"❌ Search with scores completely failed: {str(e)}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            # Try multiple ways to get statistics
            stats = {}
            
            # Method 1: Check if there's a Milvus collection object
            if hasattr(self.vector_store, 'col') and self.vector_store.col:
                try:
                    collection = self.vector_store.col
                    stats = {
                        "collection_name": collection.name,
                        "total_entities": collection.num_entities,
                        "description": getattr(collection, 'description', 'N/A'),
                    }
                    return stats
                except Exception as e:
                    print(f"⚠️ Milvus collection stats retrieval failed: {e}")
            
            # Method 2: Check if there's a collection attribute
            if hasattr(self.vector_store, 'collection') and self.vector_store.collection:
                try:
                    collection = self.vector_store.collection
                    stats = {
                        "collection_name": getattr(collection, 'name', 'N/A'),
                        "total_entities": getattr(collection, 'num_entities', 0),
                        "description": getattr(collection, 'description', 'N/A'),
                    }
                    return stats
                except Exception as e:
                    print(f"⚠️ Collection stats retrieval failed: {e}")
            
            # Method 3: Try to estimate document count through search
            try:
                # Execute a simple search to check if there's data
                test_docs = self.vector_store.similarity_search("test", k=1)
                if test_docs:
                    # If search returns results, there's data but can't get exact count
                    stats = {
                        "collection_name": getattr(self.vector_store, 'collection_name', 'default_collection'),
                        "total_entities": "Has data but cannot get exact count",
                        "description": "Data existence verified through search",
                        "status": "Has data"
                    }
                else:
                    stats = {
                        "collection_name": getattr(self.vector_store, 'collection_name', 'default_collection'),
                        "total_entities": 0,
                        "description": "Collection is empty or inaccessible",
                        "status": "Empty collection"
                    }
                return stats
            except Exception as e:
                print(f"⚠️ Search test failed: {e}")
            
            # Method 4: Return basic information
            return {
                "collection_name": self.collection_name or getattr(self.vector_store, 'collection_name', 'N/A'),
                "total_entities": "N/A",
                "description": "Unable to get statistics",
                "error": "All statistical methods failed"
            }
                
        except Exception as e:
            return {
                "collection_name": self.collection_name or "N/A",
                "total_entities": "N/A", 
                "error": f"Failed to get statistics: {str(e)}"
            }
    
    async def delete_by_metadata(self, filter_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Delete documents by metadata, prioritize sync methods to avoid event loop conflicts"""
        try:
            # Primary strategy: Use sync method directly in thread pool
            try:
                result = await run_in_thread_pool(
                    self.vector_store.delete, filter=filter_metadata
                )
                return {
                    "success": True,
                    "message": "Delete successful",
                    "result": result
                }
                
            except Exception as sync_e:
                print(f"⚠️ Sync delete method failed: {sync_e}")
                
                # Fallback strategy: Check for async method and try in current loop
                if hasattr(self.vector_store, 'adelete'):
                    try:
                        result = await self.vector_store.adelete(filter=filter_metadata)
                        return {
                            "success": True,
                            "message": "Delete successful",
                            "result": result
                        }
                    except Exception as async_e:
                        print(f"⚠️ Async delete method also failed: {async_e}")
                        return {
                            "success": False,
                            "error": str(async_e),
                            "message": f"Delete failed: {str(async_e)}"
                        }
                else:
                    return {
                        "success": False,
                        "error": str(sync_e),
                        "message": f"Delete failed: {str(sync_e)}"
                    }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Delete failed: {str(e)}"
            }
    
    async def update_documents(self, documents: List[Document]) -> Dict[str, Any]:
        """Update documents (delete then add)"""
        try:
            # Extract source files of documents to be updated
            sources = set()
            for doc in documents:
                source = doc.metadata.get("source")
                if source:
                    sources.add(source)
            
            # Delete old versions
            for source in sources:
                await self.delete_by_metadata({"source": source})
            
            # Add new versions
            result = await self.add_documents(documents)
            
            if result["success"]:
                return {
                    "success": True,
                    "message": f"Successfully updated documents from {len(sources)} source files",
                    "updated_sources": list(sources),
                    "add_result": result
                }
            else:
                return {
                    "success": False,
                    "message": "Update failed: Error adding new documents",
                    "add_result": result
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Update failed: {str(e)}"
            }