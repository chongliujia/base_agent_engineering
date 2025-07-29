"""
pytest配置文件和共享fixtures
"""

import pytest
import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# 设置测试环境变量
os.environ["TESTING"] = "true"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["MILVUS_HOST"] = "localhost"
os.environ["MILVUS_PORT"] = "19530"


@pytest.fixture
def temp_config_dir():
    """创建临时配置目录"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        yield config_dir


@pytest.fixture
def real_models_config():
    """加载真实的模型配置文件"""
    config_path = Path(__file__).parent.parent / "config" / "models.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture
def test_models_config_file(temp_config_dir, real_models_config):
    """创建测试用的模型配置文件（基于真实配置）"""
    config_file = temp_config_dir / "models.yaml"
    
    # 为测试环境调整配置
    test_config = real_models_config.copy()
    
    # 调整聊天模型配置以适应测试
    for model_name, model_config in test_config["chat_models"].items():
        model_config["parameters"]["max_tokens"] = min(
            model_config["parameters"].get("max_tokens", 1000), 1000
        )
        model_config["parameters"]["temperature"] = 0.0  # 确保测试结果一致
    
    # 调整嵌入模型配置
    for model_name, model_config in test_config["embedding_models"].items():
        model_config["parameters"]["chunk_size"] = 100  # 减小批次大小以加快测试
    
    # 调整向量存储配置
    if "vector_stores" in test_config:
        for store_name, store_config in test_config["vector_stores"].items():
            store_config["collection_name"] = f"test_{store_config.get('collection_name', 'collection')}"
    
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(test_config, f)
    
    return config_file


@pytest.fixture
def mock_model_config(test_models_config_file):
    """模拟ModelConfig类，使用真实配置文件"""
    from config.settings import ModelConfig
    
    with patch.object(ModelConfig, '__init__', lambda self, config_path=None: None):
        mock_config = Mock(spec=ModelConfig)
        mock_config.config_path = test_models_config_file
        
        # 加载真实配置
        with open(test_models_config_file, 'r', encoding='utf-8') as f:
            mock_config._config = yaml.safe_load(f)
        
        # 模拟方法
        mock_config.load_config = Mock()
        mock_config.get_chat_model = Mock()
        mock_config.get_embedding_model = Mock()
        mock_config.get_vector_store = Mock()
        
        yield mock_config


@pytest.fixture
def mock_chat_model():
    """模拟聊天模型"""
    mock = AsyncMock()
    mock.ainvoke = AsyncMock(return_value=Mock(content="Test response"))
    mock.astream = AsyncMock()
    mock.model_name = "gpt-4"
    mock.temperature = 0.0
    return mock


@pytest.fixture
def mock_embedding_model():
    """模拟嵌入模型"""
    mock = AsyncMock()
    mock.aembed_documents = AsyncMock(return_value=[[0.1, 0.2, 0.3] * 1024])  # 模拟3072维向量
    mock.aembed_query = AsyncMock(return_value=[0.1, 0.2, 0.3] * 1024)
    mock.model = "text-embedding-3-large"
    return mock


@pytest.fixture
def mock_vector_store():
    """模拟向量存储"""
    mock = AsyncMock()
    mock.asimilarity_search = AsyncMock(return_value=[])
    mock.aadd_documents = AsyncMock()
    mock.collection_name = "test_collection"
    return mock


@pytest.fixture
def mock_document():
    """模拟文档"""
    from langchain_core.documents import Document
    return Document(
        page_content="This is test content for machine learning",
        metadata={"source": "test.txt", "page": 1, "chunk_id": "test_chunk_1"}
    )


@pytest.fixture
def mock_documents():
    """模拟多个文档"""
    from langchain_core.documents import Document
    return [
        Document(
            page_content="Machine learning is a subset of artificial intelligence",
            metadata={"source": "ml_basics.txt", "page": 1, "chunk_id": "chunk_1"}
        ),
        Document(
            page_content="Deep learning uses neural networks with multiple layers",
            metadata={"source": "dl_intro.txt", "page": 1, "chunk_id": "chunk_2"}
        ),
        Document(
            page_content="Natural language processing helps computers understand text",
            metadata={"source": "nlp_guide.txt", "page": 1, "chunk_id": "chunk_3"}
        )
    ]


@pytest.fixture
def sample_rag_state():
    """示例RAG状态"""
    from src.rag.workflow import RAGState
    return RAGState(
        query="What is machine learning?",
        metadata={"query_type": "general", "user_id": "test_user"}
    )


@pytest.fixture
def sample_rag_state_with_context():
    """带有上下文的RAG状态"""
    from src.rag.workflow import RAGState
    from langchain_core.documents import Document
    
    return RAGState(
        query="What is deep learning?",
        retrieved_docs=[
            Document(
                page_content="Deep learning is a machine learning technique",
                metadata={"source": "test.txt", "score": 0.9}
            )
        ],
        web_results=[
            {"title": "Deep Learning Guide", "content": "Deep learning explained", "url": "https://example.com"}
        ],
        context="Deep learning is a subset of machine learning that uses neural networks.",
        metadata={"query_type": "technical", "user_id": "test_user"}
    )


@pytest.fixture
def mock_settings():
    """模拟Settings配置"""
    from config.settings import Settings
    
    mock = Mock(spec=Settings)
    mock.api_host = "localhost"
    mock.api_port = 8888
    mock.debug = True
    mock.testing = True
    mock.milvus_host = "localhost"
    mock.milvus_port = 19530
    mock.default_chat_model = "primary"
    mock.default_embedding_model = "primary"
    mock.langsmith_tracing = False
    mock.allowed_origins_list = ["*"]
    mock.supported_file_types_list = ["pdf", "txt", "md", "docx"]
    
    return mock


# 异步测试支持
@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# 模拟外部服务
@pytest.fixture
def mock_web_search():
    """模拟网络搜索"""
    return AsyncMock(return_value=[
        {
            "title": "Machine Learning Basics",
            "content": "Machine learning is a method of data analysis...",
            "url": "https://example.com/ml-basics"
        },
        {
            "title": "Introduction to AI",
            "content": "Artificial intelligence encompasses machine learning...",
            "url": "https://example.com/ai-intro"
        }
    ])


@pytest.fixture
def mock_reranker():
    """模拟重排序模型"""
    mock = Mock()
    mock.rank = Mock(return_value=[
        {"corpus_id": 0, "score": 0.9},
        {"corpus_id": 1, "score": 0.7},
        {"corpus_id": 2, "score": 0.5}
    ])
    return mock


# 测试数据库连接
@pytest.fixture
def mock_milvus_connection():
    """模拟Milvus连接"""
    with patch('pymilvus.connections.connect') as mock_connect:
        mock_connect.return_value = True
        yield mock_connect


# 测试Redis连接
@pytest.fixture
def mock_redis_connection():
    """模拟Redis连接"""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=True)
    
    with patch('aioredis.from_url', return_value=mock_redis):
        yield mock_redis


# 性能测试fixtures
@pytest.fixture
def performance_test_data():
    """性能测试数据"""
    return {
        "queries": [
            "What is machine learning?",
            "How does deep learning work?",
            "What are neural networks?",
            "Explain natural language processing",
            "What is computer vision?"
        ] * 10,  # 50个查询
        "expected_response_time": 2.0,  # 2秒内响应
        "max_concurrent_requests": 10
    }