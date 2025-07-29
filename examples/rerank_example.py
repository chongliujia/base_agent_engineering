"""
重排序模型使用示例
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import get_model_config


def test_reranking():
    """测试重排序功能"""
    
    # 获取模型配置
    model_config = get_model_config()
    
    # 获取重排序模型
    reranker = model_config.get_reranking_model()
    
    # 测试查询和文档
    query = "什么是文本排序模型"
    documents = [
        "文本排序模型广泛用于搜索引擎和推荐系统中，它们根据文本相关性对候选文本进行排序",
        "量子计算是计算科学的一个前沿领域",
        "预训练语言模型的发展给文本排序模型带来了新的进展"
    ]
    
    print(f"查询: {query}")
    print(f"原始文档: {documents}")
    print("\n" + "="*50)
    
    # 执行重排序
    results = reranker.rerank(query, documents, top_n=3)
    
    print("重排序结果:")
    for i, result in enumerate(results):
        print(f"{i+1}. [分数: {result['relevance_score']:.4f}] {result['document']}")
    
    print("\n" + "="*50)
    
    # 测试带元数据的文档重排序
    documents_with_metadata = [
        {
            "content": "文本排序模型广泛用于搜索引擎和推荐系统中，它们根据文本相关性对候选文本进行排序",
            "source": "AI教程",
            "author": "张三"
        },
        {
            "content": "量子计算是计算科学的一个前沿领域",
            "source": "科学杂志",
            "author": "李四"
        },
        {
            "content": "预训练语言模型的发展给文本排序模型带来了新的进展",
            "source": "机器学习论文",
            "author": "王五"
        }
    ]
    
    metadata_results = reranker.rerank_documents_with_metadata(
        query, 
        documents_with_metadata, 
        content_key="content",
        top_n=3
    )
    
    print("带元数据的重排序结果:")
    for i, result in enumerate(metadata_results):
        print(f"{i+1}. [分数: {result['relevance_score']:.4f}]")
        print(f"   内容: {result['content']}")
        print(f"   来源: {result['source']}")
        print(f"   作者: {result['author']}")
        print()


if __name__ == "__main__":
    # 确保设置了DASHSCOPE_API_KEY环境变量
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("请设置DASHSCOPE_API_KEY环境变量")
        sys.exit(1)
    
    test_reranking()