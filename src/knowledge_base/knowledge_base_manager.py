"""
Knowledge Base Manager - Unified management of document processing and vector storage
"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from langchain_core.documents import Document

from .document_processor import DocumentProcessor, DocumentValidator
from .vector_store_manager import VectorStoreManager
from config.settings import get_settings


class KnowledgeBaseManager:
    """Knowledge Base Manager - Supports multiple knowledge bases and various chunking strategies"""
    
    def __init__(self, collection_name: str = None, chunking_strategy: str = "recursive", strategy_params: Dict[str, Any] = None):
        self.settings = get_settings()
        self.doc_processor = DocumentProcessor(
            chunking_strategy=chunking_strategy, 
            strategy_params=strategy_params or {}
        )
        
        # Set current knowledge base name
        self.current_collection = collection_name or self.settings.current_collection_name
        self.vector_manager = VectorStoreManager(collection_name=self.current_collection)
        
        # Create knowledge base root directory
        self.knowledge_base_root = Path(self.settings.knowledge_base_path)
        self.knowledge_base_root.mkdir(exist_ok=True)
        
        # Create independent directory for each knowledge base
        self.knowledge_base_path = self.knowledge_base_root / self.current_collection
        self.knowledge_base_path.mkdir(exist_ok=True)
        
        # Create metadata storage directory
        self.metadata_path = self.knowledge_base_path / "metadata"
        self.metadata_path.mkdir(exist_ok=True)
    
    def save_processing_metadata(self, metadata: Dict[str, Any], 
                               filename: str = "processing_log.json"):
        """Save processing metadata"""
        metadata_file = self.metadata_path / filename
        
        # If file exists, load existing data
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        else:
            existing_data = {"processing_history": []}
        
        # Add new processing record
        existing_data["processing_history"].append(metadata)
        existing_data["last_updated"] = datetime.now().isoformat()
        
        # Save updated data
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
    
    def load_processing_metadata(self, filename: str = "processing_log.json") -> Dict[str, Any]:
        """Load processing metadata"""
        metadata_file = self.metadata_path / filename
        
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {"processing_history": []}
    
    async def add_file(self, file_path: Union[str, Path], chunking_strategy: str = None, strategy_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Add a single file to knowledge base (supports temporary chunking strategy specification)"""
        try:
            print(f"📄 Processing file: {file_path}")
            
            # 1. Process document (supports temporary strategy)
            documents = self.doc_processor.process_file(
                file_path, 
                chunking_strategy=chunking_strategy, 
                strategy_params=strategy_params
            )
            
            # 2. Validate documents
            valid_documents = DocumentValidator.validate_documents(documents)
            
            if not valid_documents:
                return {
                    "success": False,
                    "message": "No valid document content",
                    "file_path": str(file_path)
                }
            
            # 3. Vectorize and store
            result = await self.vector_manager.add_documents(valid_documents)
            
            # 4. Save metadata (including strategy information)
            strategy_info = self.doc_processor.get_strategy_info()
            metadata = {
                "operation": "add_file",
                "file_path": str(file_path),
                "timestamp": datetime.now().isoformat(),
                "total_chunks": len(documents),
                "valid_chunks": len(valid_documents),
                "chunking_strategy": strategy_info.get("name", "unknown"),
                "strategy_params": strategy_info.get("parameters", {}),
                "vector_result": result
            }
            
            self.save_processing_metadata(metadata)
            
            result.update({
                "file_path": str(file_path),
                "total_chunks": len(documents),
                "valid_chunks": len(valid_documents)
            })
            
            return result
            
        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "message": f"Failed to process file: {str(e)}",
                "file_path": str(file_path)
            }
            
            # Save error metadata
            strategy_info = self.doc_processor.get_strategy_info()
            error_metadata = {
                "operation": "add_file",
                "file_path": str(file_path),
                "timestamp": datetime.now().isoformat(),
                "chunking_strategy": strategy_info.get("name", "unknown"),
                "error": str(e),
                "success": False
            }
            
            self.save_processing_metadata(error_metadata)
            
            return error_result
    
    async def add_directory(self, directory_path: Union[str, Path], 
                          recursive: bool = True,
                          auto_strategy: bool = True,
                          chunking_strategy: str = None,
                          strategy_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Add all files in directory to knowledge base (supports automatic strategy selection and format-specific processing)"""
        try:
            print(f"📁 Processing directory: {directory_path}")
            
            # 1. Process all documents in directory (supports multiple strategies)
            documents = self.doc_processor.process_directory(
                directory_path, 
                recursive=recursive,
                auto_strategy=auto_strategy,
                chunking_strategy=chunking_strategy,
                strategy_params=strategy_params
            )
            
            # 2. Validate documents
            valid_documents = DocumentValidator.validate_documents(documents)
            
            if not valid_documents:
                return {
                    "success": False,
                    "message": "No valid document content in directory",
                    "directory_path": str(directory_path)
                }
            
            # 3. Extract document summary
            doc_summary = self.doc_processor.extract_metadata_summary(valid_documents)
            
            # 4. Vectorize and store
            result = await self.vector_manager.add_documents(valid_documents)
            
            # 5. Save metadata (including strategy information)
            strategy_info = self.doc_processor.get_strategy_info()
            metadata = {
                "operation": "add_directory",
                "directory_path": str(directory_path),
                "recursive": recursive,
                "auto_strategy": auto_strategy,
                "chunking_strategy": strategy_info.get("name", "unknown"),
                "strategy_params": strategy_info.get("parameters", {}),
                "timestamp": datetime.now().isoformat(),
                "document_summary": doc_summary,
                "vector_result": result
            }
            
            self.save_processing_metadata(metadata)
            
            result.update({
                "directory_path": str(directory_path),
                "document_summary": doc_summary
            })
            
            return result
            
        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "message": f"Failed to process directory: {str(e)}",
                "directory_path": str(directory_path)
            }
            
            # Save error metadata
            strategy_info = self.doc_processor.get_strategy_info()
            error_metadata = {
                "operation": "add_directory",
                "directory_path": str(directory_path),
                "timestamp": datetime.now().isoformat(),
                "chunking_strategy": strategy_info.get("name", "unknown"),
                "error": str(e),
                "success": False
            }
            
            self.save_processing_metadata(error_metadata)
            
            return error_result
    
    async def search(self, query: str, k: int = 5, 
                    include_scores: bool = False) -> Dict[str, Any]:
        """Search knowledge base"""
        try:
            if include_scores:
                results = await self.vector_manager.search_with_scores(query, k)
                return {
                    "success": True,
                    "query": query,
                    "results": [
                        {
                            "content": doc.page_content,
                            "metadata": doc.metadata,
                            "score": score
                        }
                        for doc, score in results
                    ]
                }
            else:
                results = await self.vector_manager.search_similar(query, k)
                return {
                    "success": True,
                    "query": query,
                    "results": [
                        {
                            "content": doc.page_content,
                            "metadata": doc.metadata
                        }
                        for doc in results
                    ]
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Search failed: {str(e)}",
                "query": query
            }
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        try:
            # Get vector store statistics
            vector_stats = self.vector_manager.get_collection_stats()
            
            # Get processing history
            processing_history = self.load_processing_metadata()
            
            # Calculate processing history statistics
            total_operations = len(processing_history.get("processing_history", []))
            successful_operations = sum(
                1 for op in processing_history.get("processing_history", [])
                if op.get("success", True)
            )
            
            return {
                "current_collection": self.current_collection,
                "vector_store_stats": vector_stats,
                "processing_stats": {
                    "total_operations": total_operations,
                    "successful_operations": successful_operations,
                    "success_rate": (successful_operations / total_operations * 100) 
                                  if total_operations > 0 else 0,
                    "last_updated": processing_history.get("last_updated")
                },
                "knowledge_base_path": str(self.knowledge_base_path),
                "metadata_path": str(self.metadata_path)
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "message": f"Failed to get statistics: {str(e)}"
            }
    
    @staticmethod
    def list_knowledge_bases() -> List[str]:
        """List all knowledge bases"""
        try:
            settings = get_settings()
            knowledge_base_root = Path(settings.knowledge_base_path)
            
            if not knowledge_base_root.exists():
                return []
            
            # Get all subdirectories as knowledge base list
            collections = []
            for item in knowledge_base_root.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    collections.append(item.name)
            
            return sorted(collections)
            
        except Exception as e:
            print(f"❌ Failed to get knowledge base list: {e}")
            return []
    
    @staticmethod
    async def create_knowledge_base(collection_name: str, chunking_strategy: str = "recursive", strategy_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create new knowledge base"""
        try:
            # Validate collection name
            if not collection_name or not collection_name.strip():
                return {
                    "success": False,
                    "message": "Knowledge base name cannot be empty"
                }
            
            # Clean name (remove special characters)
            import re
            clean_name = re.sub(r'[^\w\-_]', '_', collection_name.strip())
            
            if clean_name != collection_name.strip():
                print(f"⚠️ Knowledge base name cleaned: '{collection_name}' -> '{clean_name}'")
            
            # Check if already exists
            existing_collections = KnowledgeBaseManager.list_knowledge_bases()
            if clean_name in existing_collections:
                return {
                    "success": False,
                    "message": f"Knowledge base '{clean_name}' already exists"
                }
            
            # Create knowledge base directory structure
            settings = get_settings()
            kb_path = Path(settings.knowledge_base_path) / clean_name
            kb_path.mkdir(parents=True, exist_ok=True)
            
            metadata_path = kb_path / "metadata"
            metadata_path.mkdir(exist_ok=True)
            
            # Create knowledge base manager instance to initialize vector store
            kb_manager = KnowledgeBaseManager(
                collection_name=clean_name,
                chunking_strategy=chunking_strategy,
                strategy_params=strategy_params
            )
            
            # Test vector store connection
            try:
                # Try to get statistics to verify collection availability
                stats = kb_manager.vector_manager.get_collection_stats()
                print(f"✅ Knowledge base '{clean_name}' vector store initialized successfully")
            except Exception as vector_e:
                print(f"⚠️ Vector store initialization warning: {vector_e}")
            
            return {
                "success": True,
                "collection_name": clean_name,
                "message": f"Knowledge base '{clean_name}' created successfully",
                "path": str(kb_path)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create knowledge base: {str(e)}"
            }
    
    @staticmethod
    async def delete_knowledge_base(collection_name: str, confirm: bool = False) -> Dict[str, Any]:
        """Delete knowledge base"""
        try:
            if not confirm:
                return {
                    "success": False,
                    "message": "Please confirm deletion operation (set confirm=True)"
                }
            
            # Check if knowledge base exists
            existing_collections = KnowledgeBaseManager.list_knowledge_bases()
            if collection_name not in existing_collections:
                return {
                    "success": False,
                    "message": f"Knowledge base '{collection_name}' does not exist"
                }
            
            settings = get_settings()
            kb_path = Path(settings.knowledge_base_path) / collection_name
            
            # Delete Milvus collection
            try:
                from pymilvus import connections, utility
                
                # Connect to Milvus
                connections.connect(
                    alias="temp_connection",
                    host=settings.milvus_host,
                    port=settings.milvus_port,
                    user=settings.milvus_user if settings.milvus_user else None,
                    password=settings.milvus_password if settings.milvus_password else None
                )
                
                # Check and delete collection
                if utility.has_collection(collection_name, using="temp_connection"):
                    utility.drop_collection(collection_name, using="temp_connection")
                    print(f"✅ Milvus collection '{collection_name}' deleted")
                
                connections.disconnect("temp_connection")
                
            except Exception as milvus_e:
                print(f"⚠️ Warning when deleting Milvus collection: {milvus_e}")
            
            # Delete filesystem directory
            import shutil
            if kb_path.exists():
                shutil.rmtree(kb_path)
                print(f"✅ Knowledge base directory deleted: {kb_path}")
            
            return {
                "success": True,
                "message": f"Knowledge base '{collection_name}' deleted successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to delete knowledge base: {str(e)}"
            }
    
    @staticmethod
    def switch_knowledge_base(collection_name: str) -> Dict[str, Any]:
        """Switch current knowledge base"""
        try:
            # Check if knowledge base exists
            existing_collections = KnowledgeBaseManager.list_knowledge_bases()
            if collection_name not in existing_collections:
                return {
                    "success": False,
                    "message": f"Knowledge base '{collection_name}' does not exist"
                }
            
            # Update environment variable (only effective in current process)
            import os
            os.environ["CURRENT_COLLECTION_NAME"] = collection_name
            
            return {
                "success": True,
                "message": f"Switched to knowledge base '{collection_name}'",
                "collection_name": collection_name,
                "note": "This switch is only effective in the current process"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to switch knowledge base: {str(e)}"
            }
    
    async def update_file(self, file_path: Union[str, Path], chunking_strategy: str = None, strategy_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Update file in knowledge base (supports temporary chunking strategy specification)"""
        try:
            print(f"🔄 Updating file: {file_path}")
            
            # 1. Process document (supports temporary strategy)
            documents = self.doc_processor.process_file(
                file_path,
                chunking_strategy=chunking_strategy,
                strategy_params=strategy_params
            )
            
            # 2. Validate documents
            valid_documents = DocumentValidator.validate_documents(documents)
            
            if not valid_documents:
                return {
                    "success": False,
                    "message": "No valid document content",
                    "file_path": str(file_path)
                }
            
            # 3. Update vector store
            result = await self.vector_manager.update_documents(valid_documents)
            
            # 4. Save metadata (including strategy information)
            strategy_info = self.doc_processor.get_strategy_info()
            metadata = {
                "operation": "update_file",
                "file_path": str(file_path),
                "timestamp": datetime.now().isoformat(),
                "total_chunks": len(documents),
                "valid_chunks": len(valid_documents),
                "chunking_strategy": strategy_info.get("name", "unknown"),
                "strategy_params": strategy_info.get("parameters", {}),
                "vector_result": result
            }
            
            self.save_processing_metadata(metadata)
            
            result.update({
                "file_path": str(file_path),
                "total_chunks": len(documents),
                "valid_chunks": len(valid_documents)
            })
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to update file: {str(e)}",
                "file_path": str(file_path)
            }


# Create global knowledge base manager instance (using default chunking strategy)
knowledge_base_manager = KnowledgeBaseManager()


def get_knowledge_base_manager() -> KnowledgeBaseManager:
    """Get global knowledge base manager instance"""
    return knowledge_base_manager