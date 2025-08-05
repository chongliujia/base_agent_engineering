#!/usr/bin/env python3
"""
Add test documents to knowledge base
"""
import os
import sys
import asyncio
from pathlib import Path

# Add project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.knowledge_base.knowledge_base_manager import KnowledgeBaseManager
from src.utils.async_utils import safe_async_run, is_async_context

def create_test_documents():
    """Create some test documents"""
    test_docs_dir = project_root / "test_documents"
    test_docs_dir.mkdir(exist_ok=True)
    
    # Create test text files
    test_files = [
        {
            "name": "ai_introduction.txt",
            "content": """
Introduction to Artificial Intelligence

Artificial Intelligence (AI) is a branch of computer science that aims to create systems capable of performing tasks that typically require human intelligence.

Main areas include:
1. Machine Learning - Enabling computers to learn from data
2. Natural Language Processing - Understanding and generating human language
3. Computer Vision - Understanding and analyzing images
4. Robotics - Creating systems that can interact with the physical world

AI has a wide range of applications, including search engines, recommendation systems, autonomous vehicles, medical diagnosis, and more.
            """
        },
        {
            "name": "machine_learning.txt", 
            "content": """
Machine Learning Fundamentals

Machine learning is a subfield of artificial intelligence that focuses on developing algorithms that can learn and improve from data.

Main types:
1. Supervised Learning - Training using labeled data
2. Unsupervised Learning - Discovering patterns from unlabeled data
3. Reinforcement Learning - Learning optimal strategies through interaction with environment

Common algorithms:
- Linear Regression
- Decision Trees
- Neural Networks
- Support Vector Machines
- Random Forest

Machine learning has wide applications in image recognition, speech recognition, natural language processing, and other fields.
            """
        },
        {
            "name": "deep_learning.txt",
            "content": """
Deep Learning Overview

Deep learning is a subset of machine learning that uses multi-layer neural networks to learn complex patterns in data.

Key concepts:
1. Neural Networks - Computational models that simulate brain neurons
2. Backpropagation - Core algorithm for training neural networks
3. Activation Functions - Mathematical functions that introduce non-linearity
4. Gradient Descent - Method for optimizing network parameters

Main architectures:
- Convolutional Neural Networks (CNN) - For image processing
- Recurrent Neural Networks (RNN) - For sequential data
- Transformers - For natural language processing
- Generative Adversarial Networks (GAN) - For generating new data

Deep learning has driven major breakthroughs in AI, including image recognition, speech recognition, and natural language understanding.
            """
        },
        {
            "name": "langchain_guide.txt",
            "content": """
LangChain Usage Guide

LangChain is a framework for building applications based on Large Language Models (LLMs).

Core components:
1. Models - Language model interfaces
2. Prompts - Prompt template management
3. Chains - Linking components together
4. Agents - Intelligent agents that use tools
5. Memory - Conversation memory management
6. Vector Stores - Vector database integration

Main features:
- Model Agnostic - Supports multiple LLM providers
- Modular Design - Composable components
- Built-in Tools - Rich set of pre-built tools
- Vector Retrieval - RAG application support

LangChain enables developers to quickly build complex AI applications such as chatbots, Q&A systems, document analysis tools, and more.
            """
        }
    ]
    
    for file_info in test_files:
        file_path = test_docs_dir / file_info["name"]
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_info["content"].strip())
        print(f"✅ Created test file: {file_path}")
    
    return test_docs_dir

async def async_main():
    """Async main function"""
    try:
        print("📝 Creating test documents...")
        test_docs_dir = create_test_documents()
        
        print("\n📚 Initializing knowledge base manager...")
        kb_manager = KnowledgeBaseManager()
        
        print(f"\n📁 Adding test document directory: {test_docs_dir}")
        result = await kb_manager.add_directory(str(test_docs_dir))
        
        print(f"\n✅ Processing results:")
        if result.get('success', False):
            print(f"   Successful files: {result.get('success_count', 'N/A')}")
            print(f"   Failed files: {result.get('error_count', 'N/A')}")
            print(f"   Total documents: {result.get('total_documents', 'N/A')}")
            
            if 'document_summary' in result:
                summary = result['document_summary']
                print(f"   Processed files: {summary.get('total_files', 'N/A')}")
                print(f"   Document chunks: {summary.get('total_chunks', 'N/A')}")
        else:
            print(f"   Processing failed: {result.get('message', result.get('error', 'Unknown error'))}")
        
        if result.get('errors'):
            print(f"\n❌ Error messages:")
            for error in result['errors']:
                print(f"   {error}")
        
        print(f"\n📊 Knowledge base statistics:")
        stats = kb_manager.get_knowledge_base_stats()
        
        if "error" not in stats:
            vector_stats = stats.get("vector_store_stats", {})
            processing_stats = stats.get("processing_stats", {})
            
            print(f"   Vector store:")
            print(f"     Collection name: {vector_stats.get('collection_name', 'N/A')}")
            print(f"     Document count: {vector_stats.get('total_entities', 'N/A')}")
            
            print(f"   Processing statistics:")
            print(f"     Total operations: {processing_stats.get('total_operations', 0)}")
            print(f"     Successful operations: {processing_stats.get('successful_operations', 0)}")
            print(f"     Success rate: {processing_stats.get('success_rate', 0):.1f}%")
            print(f"     Last updated: {processing_stats.get('last_updated', 'None')}")
        else:
            print(f"❌ Failed to get statistics: {stats.get('message', 'Unknown error')}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

def main():
    """Main function - safely run async code"""
    if is_async_context():
        # If already in async context, return coroutine directly
        print("⚠️ Async context detected, please use await async_main() directly")
        return async_main()
    else:
        # Not in async context, run safely
        return safe_async_run(async_main())

if __name__ == "__main__":
    result = main()
    if asyncio.iscoroutine(result):
        # If returned coroutine, means in async context
        print("Please run this script in an async environment")
        sys.exit(1)
    else:
        sys.exit(result)