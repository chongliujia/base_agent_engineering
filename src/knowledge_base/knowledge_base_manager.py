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
    """知识库管理器 - 支持多知识库和多种分块策略"""
    
    def __init__(self, collection_name: str = None, chunking_strategy: str = "recursive", strategy_params: Dict[str, Any] = None):
        self.settings = get_settings()
        self.doc_processor = DocumentProcessor(
            chunking_strategy=chunking_strategy, 
            strategy_params=strategy_params or {}
        )
        
        # 设置当前知识库名称
        self.current_collection = collection_name or self.settings.current_collection_name
        self.vector_manager = VectorStoreManager(collection_name=self.current_collection)
        
        # 创建知识库根目录
        self.knowledge_base_root = Path(self.settings.knowledge_base_path)
        self.knowledge_base_root.mkdir(exist_ok=True)
        
        # 为每个知识库创建独立的目录
        self.knowledge_base_path = self.knowledge_base_root / self.current_collection
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
    
    async def add_file(self, file_path: Union[str, Path], chunking_strategy: str = None, strategy_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """添加单个文件到知识库（支持临时指定分块策略）"""
        try:
            print(f"📄 处理文件: {file_path}")
            
            # 1. 处理文档（支持临时策略）
            documents = self.doc_processor.process_file(
                file_path, 
                chunking_strategy=chunking_strategy, 
                strategy_params=strategy_params
            )
            
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
            
            # 4. 保存元数据（包含策略信息）
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
                "message": f"处理文件失败: {str(e)}",
                "file_path": str(file_path)
            }
            
            # 保存错误元数据
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
        """添加目录中的所有文件到知识库（支持自动策略选择和格式特定处理）"""
        try:
            print(f"📁 处理目录: {directory_path}")
            
            # 1. 处理目录中的所有文档（支持多种策略）
            documents = self.doc_processor.process_directory(
                directory_path, 
                recursive=recursive,
                auto_strategy=auto_strategy,
                chunking_strategy=chunking_strategy,
                strategy_params=strategy_params
            )
            
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
            
            # 5. 保存元数据（包含策略信息）
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
                "message": f"处理目录失败: {str(e)}",
                "directory_path": str(directory_path)
            }
            
            # 保存错误元数据
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
                "message": f"获取统计信息失败: {str(e)}"
            }
    
    @staticmethod
    def list_knowledge_bases() -> List[str]:
        """列出所有知识库"""
        try:
            settings = get_settings()
            knowledge_base_root = Path(settings.knowledge_base_path)
            
            if not knowledge_base_root.exists():
                return []
            
            # 获取所有子目录作为知识库列表
            collections = []
            for item in knowledge_base_root.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    collections.append(item.name)
            
            return sorted(collections)
            
        except Exception as e:
            print(f"❌ 获取知识库列表失败: {e}")
            return []
    
    @staticmethod
    async def create_knowledge_base(collection_name: str, chunking_strategy: str = "recursive", strategy_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """创建新的知识库"""
        try:
            # 验证集合名称
            if not collection_name or not collection_name.strip():
                return {
                    "success": False,
                    "message": "知识库名称不能为空"
                }
            
            # 清理名称（移除特殊字符）
            import re
            clean_name = re.sub(r'[^\w\-_]', '_', collection_name.strip())
            
            if clean_name != collection_name.strip():
                print(f"⚠️ 知识库名称已清理: '{collection_name}' -> '{clean_name}'")
            
            # 检查是否已存在
            existing_collections = KnowledgeBaseManager.list_knowledge_bases()
            if clean_name in existing_collections:
                return {
                    "success": False,
                    "message": f"知识库 '{clean_name}' 已存在"
                }
            
            # 创建知识库目录结构
            settings = get_settings()
            kb_path = Path(settings.knowledge_base_path) / clean_name
            kb_path.mkdir(parents=True, exist_ok=True)
            
            metadata_path = kb_path / "metadata"
            metadata_path.mkdir(exist_ok=True)
            
            # 创建知识库管理器实例来初始化向量存储
            kb_manager = KnowledgeBaseManager(
                collection_name=clean_name,
                chunking_strategy=chunking_strategy,
                strategy_params=strategy_params
            )
            
            # 测试向量存储连接
            try:
                # 尝试获取统计信息来验证集合是否可用
                stats = kb_manager.vector_manager.get_collection_stats()
                print(f"✅ 知识库 '{clean_name}' 向量存储初始化成功")
            except Exception as vector_e:
                print(f"⚠️ 向量存储初始化警告: {vector_e}")
            
            return {
                "success": True,
                "collection_name": clean_name,
                "message": f"知识库 '{clean_name}' 创建成功",
                "path": str(kb_path)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"创建知识库失败: {str(e)}"
            }
    
    @staticmethod
    async def delete_knowledge_base(collection_name: str, confirm: bool = False) -> Dict[str, Any]:
        """删除知识库"""
        try:
            if not confirm:
                return {
                    "success": False,
                    "message": "请确认删除操作（设置 confirm=True）"
                }
            
            # 检查知识库是否存在
            existing_collections = KnowledgeBaseManager.list_knowledge_bases()
            if collection_name not in existing_collections:
                return {
                    "success": False,
                    "message": f"知识库 '{collection_name}' 不存在"
                }
            
            settings = get_settings()
            kb_path = Path(settings.knowledge_base_path) / collection_name
            
            # 删除Milvus集合
            try:
                from pymilvus import connections, utility
                
                # 连接到Milvus
                connections.connect(
                    alias="temp_connection",
                    host=settings.milvus_host,
                    port=settings.milvus_port,
                    user=settings.milvus_user if settings.milvus_user else None,
                    password=settings.milvus_password if settings.milvus_password else None
                )
                
                # 检查并删除集合
                if utility.has_collection(collection_name, using="temp_connection"):
                    utility.drop_collection(collection_name, using="temp_connection")
                    print(f"✅ Milvus集合 '{collection_name}' 已删除")
                
                connections.disconnect("temp_connection")
                
            except Exception as milvus_e:
                print(f"⚠️ 删除Milvus集合时出现警告: {milvus_e}")
            
            # 删除文件系统目录
            import shutil
            if kb_path.exists():
                shutil.rmtree(kb_path)
                print(f"✅ 知识库目录已删除: {kb_path}")
            
            return {
                "success": True,
                "message": f"知识库 '{collection_name}' 删除成功"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"删除知识库失败: {str(e)}"
            }
    
    @staticmethod
    def switch_knowledge_base(collection_name: str) -> Dict[str, Any]:
        """切换当前知识库"""
        try:
            # 检查知识库是否存在
            existing_collections = KnowledgeBaseManager.list_knowledge_bases()
            if collection_name not in existing_collections:
                return {
                    "success": False,
                    "message": f"知识库 '{collection_name}' 不存在"
                }
            
            # 更新环境变量（仅在当前进程中有效）
            import os
            os.environ["CURRENT_COLLECTION_NAME"] = collection_name
            
            return {
                "success": True,
                "message": f"已切换到知识库 '{collection_name}'",
                "collection_name": collection_name,
                "note": "此切换仅在当前进程中有效"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"切换知识库失败: {str(e)}"
            }
    
    async def update_file(self, file_path: Union[str, Path], chunking_strategy: str = None, strategy_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """更新知识库中的文件（支持临时指定分块策略）"""
        try:
            print(f"🔄 更新文件: {file_path}")
            
            # 1. 处理文档（支持临时策略）
            documents = self.doc_processor.process_file(
                file_path,
                chunking_strategy=chunking_strategy,
                strategy_params=strategy_params
            )
            
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
            
            # 4. 保存元数据（包含策略信息）
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
                "message": f"更新文件失败: {str(e)}",
                "file_path": str(file_path)
            }


# 创建全局知识库管理器实例（使用默认分块策略）
knowledge_base_manager = KnowledgeBaseManager()


def get_knowledge_base_manager() -> KnowledgeBaseManager:
    """获取全局知识库管理器实例"""
    return knowledge_base_manager