"""
DashScope Reranking Model Implementation
"""

import dashscope
from http import HTTPStatus
from typing import List, Dict, Any, Optional, Tuple
import os
import logging

logger = logging.getLogger(__name__)


class DashScopeRerank:
    """DashScope reranking model wrapper class"""
    
    def __init__(
        self,
        model: str = "gte-rerank-v2",
        api_key: Optional[str] = None,
        top_n: int = 10,
        return_documents: bool = True,
        **kwargs
    ):
        """
        Initialize DashScope reranking model
        
        Args:
            model: Model name, default is gte-rerank-v2
            api_key: API key, if not provided will get from environment variable
            top_n: Number of documents to return
            return_documents: Whether to return document content
        """
        self.model = model
        self.top_n = top_n
        self.return_documents = return_documents
        
        # Set API key
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
        Rerank documents
        
        Args:
            query: Query text
            documents: List of documents
            top_n: Number of documents to return, if not specified will use initialization value
            
        Returns:
            Reranked document list containing document content and relevance scores
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
                        # If document content is not returned, get from original document list
                        result["document"] = documents[item.index]
                    
                    results.append(result)
                
                logger.info(f"Successfully reranked {len(results)} documents")
                return results
            else:
                logger.error(f"DashScope rerank failed: {resp.code} - {resp.message}")
                # If reranking fails, return original documents (in original order)
                return [
                    {
                        "index": i,
                        "document": doc,
                        "relevance_score": 1.0 - (i * 0.1)  # Simple descending scores
                    }
                    for i, doc in enumerate(documents[:top_n])
                ]
                
        except Exception as e:
            logger.error(f"DashScope rerank error: {str(e)}")
            # Return original documents on error
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
        Rerank documents with metadata
        
        Args:
            query: Query text
            documents: List of documents, each document is a dictionary containing content and metadata
            content_key: Key name for document content in the dictionary
            top_n: Number of documents to return
            
        Returns:
            Reranked document list containing original metadata and relevance scores
        """
        if not documents:
            return []
            
        # Extract document content
        doc_contents = [doc.get(content_key, "") for doc in documents]
        
        # Perform reranking
        rerank_results = self.rerank(query, doc_contents, top_n)
        
        # Merge results with original document metadata
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
        Asynchronous version of reranking method
        Note: DashScope Python SDK currently does not support async calls, using sync method here
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
        Asynchronous version of document reranking with metadata method
        """
        return self.rerank_documents_with_metadata(query, documents, content_key, top_n)


def create_dashscope_reranker(config: Dict[str, Any]) -> DashScopeRerank:
    """
    Create DashScope reranker instance based on configuration
    
    Args:
        config: Configuration dictionary containing model parameters
        
    Returns:
        DashScopeRerank instance
    """
    api_key = os.getenv(config.get("api_key_env", "DASHSCOPE_API_KEY"))
    parameters = config.get("parameters", {})
    
    return DashScopeRerank(
        model=parameters.get("model", "gte-rerank-v2"),
        api_key=api_key,
        top_n=parameters.get("top_n", 10),
        return_documents=parameters.get("return_documents", True)
    )