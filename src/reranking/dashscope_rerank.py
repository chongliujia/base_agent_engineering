"""
DashScope重排序模型实现
"""

import dashscope
from http import HTTPStatus
from typing import List, Dict, Any, Optional, Tuple
import os
import logging

logger = logging.getLogger(__name__)


class DashScopeRerank:
    """DashScope重排序模型封装类"""
    
    def __init__(
        self,
        model: str = "gte-rerank-v2",
        api_key: Optional[str] = None,
        top_n: int = 10,
        return_documents: bool = True,
        **kwargs
    ):
        """
        初始化DashScope重排序模型
        
        Args:
            model: 模型名称，默认为gte-rerank-v2
            api_key: API密钥，如果未提供则从环境变量获取
            top_n: 返回的文档数量
            return_documents: 是否返回文档内容
        """
        self.model = model
        self.top_n = top_n
        self.return_documents = return_documents
        
        # 设置API密钥
        if api_key:
            dashscope.api_key = api_key
        elif os.getenv("DASHSCOPE_API_KEY"):
            dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
        else:
            raise ValueError("DashScope API key not found. Please set DASHSCOPE_API_KEY environment variable or pass api_key parameter.")
    
    def rerank(
        self, 
        query: str, 
        documents: List[str], 
        top_n: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        对文档进行重排序
        
        Args:
            query: 查询文本
            documents: 文档列表
            top_n: 返回的文档数量，如果未指定则使用初始化时的值
            
        Returns:
            重排序后的文档列表，包含文档内容和相关性分数
        """
        if top_n is None:
            top_n = self.top_n
            
        try:
            resp = dashscope.TextReRank.call(
                model=self.model,
                query=query,
                documents=documents,
                top_n=min(top_n, len(documents)),
                return_documents=self.return_documents
            )
            
            if resp.status_code == HTTPStatus.OK:
                results = []
                for item in resp.output.results:
                    result = {
                        "index": item.index,
                        "relevance_score": item.relevance_score
                    }
                    if self.return_documents and hasattr(item, 'document') and item.document is not None:
                        result["document"] = item.document.text
                    else:
                        # 如果没有返回文档内容，从原始文档列表中获取
                        result["document"] = documents[item.index]
                    
                    results.append(result)
                
                logger.info(f"Successfully reranked {len(results)} documents")
                return results
            else:
                logger.error(f"DashScope rerank failed: {resp.code} - {resp.message}")
                # 如果重排序失败，返回原始文档（按原顺序）
                return [
                    {
                        "index": i,
                        "document": doc,
                        "relevance_score": 1.0 - (i * 0.1)  # 简单的降序分数
                    }
                    for i, doc in enumerate(documents[:top_n])
                ]
                
        except Exception as e:
            logger.error(f"DashScope rerank error: {str(e)}")
            # 出错时返回原始文档
            return [
                {
                    "index": i,
                    "document": doc,
                    "relevance_score": 1.0 - (i * 0.1)
                }
                for i, doc in enumerate(documents[:top_n])
            ]
    
    def rerank_documents_with_metadata(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        content_key: str = "content",
        top_n: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        对带元数据的文档进行重排序
        
        Args:
            query: 查询文本
            documents: 文档列表，每个文档是包含内容和元数据的字典
            content_key: 文档内容在字典中的键名
            top_n: 返回的文档数量
            
        Returns:
            重排序后的文档列表，包含原始元数据和相关性分数
        """
        if not documents:
            return []
            
        # 提取文档内容
        doc_contents = [doc.get(content_key, "") for doc in documents]
        
        # 进行重排序
        rerank_results = self.rerank(query, doc_contents, top_n)
        
        # 将结果与原始文档元数据合并
        final_results = []
        for result in rerank_results:
            original_doc = documents[result["index"]].copy()
            original_doc["relevance_score"] = result["relevance_score"]
            original_doc["rerank_index"] = result["index"]
            final_results.append(original_doc)
        
        return final_results
    
    async def arerank(
        self, 
        query: str, 
        documents: List[str], 
        top_n: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        异步版本的重排序方法
        注意：DashScope Python SDK目前不支持异步调用，这里使用同步方法
        """
        return self.rerank(query, documents, top_n)
    
    async def arerank_documents_with_metadata(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        content_key: str = "content",
        top_n: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        异步版本的带元数据文档重排序方法
        """
        return self.rerank_documents_with_metadata(query, documents, content_key, top_n)


def create_dashscope_reranker(config: Dict[str, Any]) -> DashScopeRerank:
    """
    根据配置创建DashScope重排序器实例
    
    Args:
        config: 配置字典，包含模型参数
        
    Returns:
        DashScopeRerank实例
    """
    api_key = os.getenv(config.get("api_key_env", "DASHSCOPE_API_KEY"))
    parameters = config.get("parameters", {})
    
    return DashScopeRerank(
        model=parameters.get("model", "gte-rerank-v2"),
        api_key=api_key,
        top_n=parameters.get("top_n", 10),
        return_documents=parameters.get("return_documents", True)
    )