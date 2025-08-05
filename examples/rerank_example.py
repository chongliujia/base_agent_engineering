"""
Reranking model usage example
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import get_model_config


def test_reranking():
    """Test reranking functionality"""
    
    # Get model configuration
    model_config = get_model_config()
    
    # Get reranking model
    reranker = model_config.get_reranking_model()
    
    # Test query and documents
    query = "What is a text ranking model"
    documents = [
        "Text ranking models are widely used in search engines and recommendation systems, they rank candidate texts based on text relevance",
        "Quantum computing is a frontier field in computational science",
        "The development of pre-trained language models has brought new advances to text ranking models"
    ]
    
    print(f"Query: {query}")
    print(f"Original documents: {documents}")
    print("\n" + "="*50)
    
    # Execute reranking
    results = reranker.rerank(query, documents, top_n=3)
    
    print("Reranking results:")
    for i, result in enumerate(results):
        print(f"{i+1}. [Score: {result['relevance_score']:.4f}] {result['document']}")
    
    print("\n" + "="*50)
    
    # Test document reranking with metadata
    documents_with_metadata = [
        {
            "content": "Text ranking models are widely used in search engines and recommendation systems, they rank candidate texts based on text relevance",
            "source": "AI Tutorial",
            "author": "Zhang San"
        },
        {
            "content": "Quantum computing is a frontier field in computational science",
            "source": "Science Journal",
            "author": "Li Si"
        },
        {
            "content": "The development of pre-trained language models has brought new advances to text ranking models",
            "source": "Machine Learning Paper",
            "author": "Wang Wu"
        }
    ]
    
    metadata_results = reranker.rerank_documents_with_metadata(
        query, 
        documents_with_metadata, 
        content_key="content",
        top_n=3
    )
    
    print("Reranking results with metadata:")
    for i, result in enumerate(metadata_results):
        print(f"{i+1}. [Score: {result['relevance_score']:.4f}]")
        print(f"   Content: {result['content']}")
        print(f"   Source: {result['source']}")
        print(f"   Author: {result['author']}")
        print()


if __name__ == "__main__":
    # Ensure DASHSCOPE_API_KEY environment variable is set
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("Please set DASHSCOPE_API_KEY environment variable")
        sys.exit(1)
    
    test_reranking()