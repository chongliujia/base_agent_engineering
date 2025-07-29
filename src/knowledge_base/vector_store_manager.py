#!/usr/bin/env python3
"""
向量存储管理器 - 管理文档的向量化和存储
"""

import asyncio
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from config.settings import model_config
from src.utils.async_utils import run_in_isolated_loop_async, run_in_thread_pool


class VectorStoreManager:
    """向量存储管理器"""
    
    def __init__(self, batch_size: int = 10):
        self.vector_store = model_config.get_vector_store()
        self.batch_size = batch_size
    
    async def add_documents(self, documents: List[Document], 
                          batch_size: Optional[int] = None) -> Dict[str, Any]:
        """批量添加文档到向量存储"""
        if not documents:
            return {"success": False, "message": "没有文档需要添加"}
        
        batch_size = batch_size or self.batch_size
        total_docs = len(documents)
        added_count = 0
        failed_count = 0
        results = []
        
        print(f"🚀 开始向量化 {total_docs} 个文档分块...")
        
        # 分批处理
        for i in range(0, total_docs, batch_size):
            batch = documents[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_docs + batch_size - 1) // batch_size
            
            print(f"📦 处理批次 {batch_num}/{total_batches} ({len(batch)} 个分块)")
            
            try:
                # 使用隔离的事件循环来避免冲突
                success = await self._add_batch_isolated(batch)
                
                if success:
                    added_count += len(batch)
                    results.append({
                        "batch": batch_num,
                        "success": True,
                        "count": len(batch),
                        "message": f"成功添加 {len(batch)} 个分块"
                    })
                    print(f"✅ 批次 {batch_num} 完成")
                else:
                    failed_count += len(batch)
                    results.append({
                        "batch": batch_num,
                        "success": False,
                        "count": 0,
                        "error": "添加失败",
                        "message": f"批次 {batch_num} 失败"
                    })
                    print(f"❌ 批次 {batch_num} 失败")
                
            except Exception as e:
                failed_count += len(batch)
                error_msg = f"批次 {batch_num} 失败: {str(e)}"
                
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
        
        print(f"\n📊 向量化完成:")
        print(f"  总分块数: {total_docs}")
        print(f"  成功添加: {added_count}")
        print(f"  失败数量: {failed_count}")
        print(f"  成功率: {success_rate:.1f}%")
        
        return summary
    
    async def _add_batch_isolated(self, batch: List[Document]) -> bool:
        """在隔离的线程中添加批次，优先使用同步方法避免事件循环冲突"""
        try:
            # 优先策略：直接在线程池中使用同步方法
            try:
                await run_in_thread_pool(self.vector_store.add_documents, batch)
                return True
            except Exception as sync_e:
                print(f"⚠️ 同步方法执行失败: {sync_e}")
                
                # 回退策略：检查是否有异步方法并尝试在当前循环中执行
                if hasattr(self.vector_store, 'aadd_documents'):
                    try:
                        await self.vector_store.aadd_documents(batch)
                        return True
                    except Exception as async_e:
                        print(f"⚠️ 异步方法也失败: {async_e}")
                        return False
                else:
                    return False
            
        except Exception as e:
            print(f"❌ 批次添加完全失败: {e}")
            return False
    
    async def search_similar(self, query: str, k: int = 5, 
                           filter_metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        """搜索相似文档，优先使用同步方法避免事件循环冲突"""
        try:
            # 优先策略：直接在线程池中使用同步方法
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
                print(f"⚠️ 同步搜索方法失败: {sync_e}")
                
                # 回退策略：检查是否有异步方法并尝试在当前循环中执行
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
                        print(f"⚠️ 异步搜索方法也失败: {async_e}")
                        return []
                else:
                    return []
            
        except Exception as e:
            print(f"❌ 搜索完全失败: {str(e)}")
            return []
    
    async def search_with_scores(self, query: str, k: int = 5) -> List[tuple]:
        """搜索相似文档并返回相似度分数，优先使用同步方法避免事件循环冲突"""
        try:
            # 优先策略：直接在线程池中使用同步方法
            try:
                docs_with_scores = await run_in_thread_pool(
                    self.vector_store.similarity_search_with_score, query, k
                )
                return docs_with_scores if docs_with_scores else []
                
            except Exception as sync_e:
                print(f"⚠️ 同步带分数搜索方法失败: {sync_e}")
                
                # 回退策略：检查是否有异步方法并尝试在当前循环中执行
                if hasattr(self.vector_store, 'asimilarity_search_with_score'):
                    try:
                        docs_with_scores = await self.vector_store.asimilarity_search_with_score(query, k=k)
                        return docs_with_scores if docs_with_scores else []
                    except Exception as async_e:
                        print(f"⚠️ 异步带分数搜索方法也失败: {async_e}")
                        return []
                else:
                    return []
            
        except Exception as e:
            print(f"❌ 带分数搜索完全失败: {str(e)}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        try:
            # 这里需要根据具体的向量存储实现来获取统计信息
            # Milvus的示例
            if hasattr(self.vector_store, 'col'):
                collection = self.vector_store.col
                stats = {
                    "collection_name": collection.name,
                    "total_entities": collection.num_entities,
                    "description": collection.description,
                    "schema": str(collection.schema)
                }
                return stats
            else:
                return {"message": "统计信息不可用"}
                
        except Exception as e:
            return {"error": f"获取统计信息失败: {str(e)}"}
    
    async def delete_by_metadata(self, filter_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """根据元数据删除文档，优先使用同步方法避免事件循环冲突"""
        try:
            # 优先策略：直接在线程池中使用同步方法
            try:
                result = await run_in_thread_pool(
                    self.vector_store.delete, filter=filter_metadata
                )
                return {
                    "success": True,
                    "message": "删除成功",
                    "result": result
                }
                
            except Exception as sync_e:
                print(f"⚠️ 同步删除方法失败: {sync_e}")
                
                # 回退策略：检查是否有异步方法并尝试在当前循环中执行
                if hasattr(self.vector_store, 'adelete'):
                    try:
                        result = await self.vector_store.adelete(filter=filter_metadata)
                        return {
                            "success": True,
                            "message": "删除成功",
                            "result": result
                        }
                    except Exception as async_e:
                        print(f"⚠️ 异步删除方法也失败: {async_e}")
                        return {
                            "success": False,
                            "error": str(async_e),
                            "message": f"删除失败: {str(async_e)}"
                        }
                else:
                    return {
                        "success": False,
                        "error": str(sync_e),
                        "message": f"删除失败: {str(sync_e)}"
                    }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"删除失败: {str(e)}"
            }
    
    async def update_documents(self, documents: List[Document]) -> Dict[str, Any]:
        """更新文档（先删除再添加）"""
        try:
            # 提取需要更新的文档的源文件
            sources = set()
            for doc in documents:
                source = doc.metadata.get("source")
                if source:
                    sources.add(source)
            
            # 删除旧版本
            for source in sources:
                await self.delete_by_metadata({"source": source})
            
            # 添加新版本
            result = await self.add_documents(documents)
            
            if result["success"]:
                return {
                    "success": True,
                    "message": f"成功更新 {len(sources)} 个源文件的文档",
                    "updated_sources": list(sources),
                    "add_result": result
                }
            else:
                return {
                    "success": False,
                    "message": "更新失败：添加新文档时出错",
                    "add_result": result
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"更新失败: {str(e)}"
            }