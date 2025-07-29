"""
知识库管理器 - 统一管理文档处理和向量存储
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
    """知识库管理器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.doc_processor = DocumentProcessor()
        self.vector_manager = VectorStoreManager()
        self.knowledge_base_path = Path(self.settings.knowledge_base_path)
        self.knowledge_base_path.mkdir(exist_ok=True)
        
        # 创建元数据存储目录
        self.metadata_path = self.knowledge_base_path / "metadata"
        self.metadata_path.mkdir(exist_ok=True)
    
    def save_processing_metadata(self, metadata: Dict[str, Any], 
                               filename: str = "processing_log.json"):
        """保存处理元数据"""
        metadata_file = self.metadata_path / filename
        
        # 如果文件存在，加载现有数据
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        else:
            existing_data = {"processing_history": []}
        
        # 添加新的处理记录
        existing_data["processing_history"].append(metadata)
        existing_data["last_updated"] = datetime.now().isoformat()
        
        # 保存更新后的数据
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
    
    def load_processing_metadata(self, filename: str = "processing_log.json") -> Dict[str, Any]:
        """加载处理元数据"""
        metadata_file = self.metadata_path / filename
        
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {"processing_history": []}
    
    async def add_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """添加单个文件到知识库"""
        try:
            print(f"📄 处理文件: {file_path}")
            
            # 1. 处理文档
            documents = self.doc_processor.process_file(file_path)
            
            # 2. 验证文档
            valid_documents = DocumentValidator.validate_documents(documents)
            
            if not valid_documents:
                return {
                    "success": False,
                    "message": "没有有效的文档内容",
                    "file_path": str(file_path)
                }
            
            # 3. 向量化并存储
            result = await self.vector_manager.add_documents(valid_documents)
            
            # 4. 保存元数据
            metadata = {
                "operation": "add_file",
                "file_path": str(file_path),
                "timestamp": datetime.now().isoformat(),
                "total_chunks": len(documents),
                "valid_chunks": len(valid_documents),
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
                "message": f"处理文件失败: {str(e)}",
                "file_path": str(file_path)
            }
            
            # 保存错误元数据
            error_metadata = {
                "operation": "add_file",
                "file_path": str(file_path),
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "success": False
            }
            
            self.save_processing_metadata(error_metadata)
            
            return error_result
    
    async def add_directory(self, directory_path: Union[str, Path], 
                          recursive: bool = True) -> Dict[str, Any]:
        """添加目录中的所有文件到知识库"""
        try:
            print(f"📁 处理目录: {directory_path}")
            
            # 1. 处理目录中的所有文档
            documents = self.doc_processor.process_directory(directory_path, recursive)
            
            # 2. 验证文档
            valid_documents = DocumentValidator.validate_documents(documents)
            
            if not valid_documents:
                return {
                    "success": False,
                    "message": "目录中没有有效的文档内容",
                    "directory_path": str(directory_path)
                }
            
            # 3. 获取文档摘要
            doc_summary = self.doc_processor.extract_metadata_summary(valid_documents)
            
            # 4. 向量化并存储
            result = await self.vector_manager.add_documents(valid_documents)
            
            # 5. 保存元数据
            metadata = {
                "operation": "add_directory",
                "directory_path": str(directory_path),
                "recursive": recursive,
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
                "message": f"处理目录失败: {str(e)}",
                "directory_path": str(directory_path)
            }
            
            # 保存错误元数据
            error_metadata = {
                "operation": "add_directory",
                "directory_path": str(directory_path),
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "success": False
            }
            
            self.save_processing_metadata(error_metadata)
            
            return error_result
    
    async def search(self, query: str, k: int = 5, 
                    include_scores: bool = False) -> Dict[str, Any]:
        """搜索知识库"""
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
                "message": f"搜索失败: {str(e)}",
                "query": query
            }
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        try:
            # 获取向量存储统计
            vector_stats = self.vector_manager.get_collection_stats()
            
            # 获取处理历史
            processing_history = self.load_processing_metadata()
            
            # 统计处理历史
            total_operations = len(processing_history.get("processing_history", []))
            successful_operations = sum(
                1 for op in processing_history.get("processing_history", [])
                if op.get("success", True)
            )
            
            return {
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
                "message": f"获取统计信息失败: {str(e)}"
            }
    
    async def update_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """更新知识库中的文件"""
        try:
            print(f"🔄 更新文件: {file_path}")
            
            # 1. 处理文档
            documents = self.doc_processor.process_file(file_path)
            
            # 2. 验证文档
            valid_documents = DocumentValidator.validate_documents(documents)
            
            if not valid_documents:
                return {
                    "success": False,
                    "message": "没有有效的文档内容",
                    "file_path": str(file_path)
                }
            
            # 3. 更新向量存储
            result = await self.vector_manager.update_documents(valid_documents)
            
            # 4. 保存元数据
            metadata = {
                "operation": "update_file",
                "file_path": str(file_path),
                "timestamp": datetime.now().isoformat(),
                "total_chunks": len(documents),
                "valid_chunks": len(valid_documents),
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
                "message": f"更新文件失败: {str(e)}",
                "file_path": str(file_path)
            }


# 创建全局知识库管理器实例
knowledge_base_manager = KnowledgeBaseManager()