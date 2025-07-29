"""
模型连接测试 - 使用配置文件测试所有模型连接
"""

import os
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from config.settings import get_model_config, get_settings
from src.reranking.dashscope_rerank import DashScopeRerank


class TestModelConnections:
    """模型连接测试类"""
    
    @classmethod
    def setup_class(cls):
        """测试类初始化"""
        cls.model_config = get_model_config()
        cls.settings = get_settings()
        
        # 检查必要的环境变量
        cls.has_openai_key = bool(os.getenv("OPENAI_API_KEY"))
        cls.has_dashscope_key = bool(os.getenv("DASHSCOPE_API_KEY"))
    
    def test_model_config_loading(self):
        """测试模型配置加载"""
        # 测试配置文件是否正确加载
        assert self.model_config._config is not None
        assert "chat_models" in self.model_config._config
        assert "embedding_models" in self.model_config._config
        assert "reranking_models" in self.model_config._config
        assert "default_models" in self.model_config._config
        
        # 测试默认模型配置
        default_models = self.model_config._config["default_models"]
        assert default_models["chat"] == "primary"
        assert default_models["embedding"] == "primary"
        assert default_models["reranking"] == "primary"
    
    def test_chat_model_config(self):
        """测试聊天模型配置"""
        chat_models = self.model_config._config["chat_models"]
        
        # 测试primary模型配置
        assert "primary" in chat_models
        primary_config = chat_models["primary"]
        # 根据实际配置文件调整期望值
        print(f"Primary model name: {primary_config['name']}")
        assert primary_config["name"] in ["gpt-4", "qwen-plus"]  # 支持两种可能的配置
        assert primary_config["provider"] == "langchain_openai"
        # API key 字段可能是环境变量名或直接的key
        assert "api_key_env" in primary_config
        
        # 测试fallback模型配置
        assert "fallback" in chat_models
        fallback_config = chat_models["fallback"]
        print(f"Fallback model name: {fallback_config['name']}")
        assert fallback_config["name"] in ["gpt-3.5-turbo", "qwen-plus"]  # 支持两种可能的配置
        assert fallback_config["provider"] == "langchain_openai"
    
    def test_embedding_model_config(self):
        """测试嵌入模型配置"""
        embedding_models = self.model_config._config["embedding_models"]
        
        # 测试primary模型配置
        assert "primary" in embedding_models
        primary_config = embedding_models["primary"]
        print(f"Primary embedding model name: {primary_config['name']}")
        assert primary_config["name"] in ["text-embedding-3-large", "text-embedding-v4"]
        assert primary_config["provider"] == "langchain_openai"
        # 维度可能不同，检查是否为合理数值
        dimensions = primary_config["parameters"]["dimensions"]
        assert dimensions in [1536, 2048, 3072]  # 常见的嵌入维度
        
        # 测试fallback模型配置
        assert "fallback" in embedding_models
        fallback_config = embedding_models["fallback"]
        print(f"Fallback embedding model name: {fallback_config['name']}")
        assert fallback_config["name"] in ["text-embedding-3-small", "text-embedding-v4"]
        fallback_dimensions = fallback_config["parameters"]["dimensions"]
        assert fallback_dimensions in [1536, 2048, 3072]
    
    def test_reranking_model_config(self):
        """测试重排序模型配置"""
        reranking_models = self.model_config._config["reranking_models"]
        
        # 测试primary模型配置
        assert "primary" in reranking_models
        primary_config = reranking_models["primary"]
        assert primary_config["name"] == "gte-rerank-v2"
        assert primary_config["provider"] == "dashscope"
        assert primary_config["api_key_env"] == "DASHSCOPE_API_KEY"
    
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
    def test_chat_model_connection(self):
        """测试聊天模型连接"""
        try:
            # 测试primary模型
            chat_model = self.model_config.get_chat_model("primary")
            assert chat_model is not None
            
            # 简单的连接测试
            response = chat_model.invoke([{"role": "user", "content": "Hello"}])
            assert response is not None
            assert hasattr(response, 'content')
            
            print(f"✅ 聊天模型连接成功: {response.content[:50]}...")
            
        except Exception as e:
            pytest.fail(f"聊天模型连接失败: {str(e)}")
    
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
    def test_embedding_model_connection(self):
        """测试嵌入模型连接"""
        try:
            # 测试primary模型
            embedding_model = self.model_config.get_embedding_model("primary")
            assert embedding_model is not None
            
            # 简单的嵌入测试
            test_text = "这是一个测试文本"
            embeddings = embedding_model.embed_query(test_text)
            assert embeddings is not None
            assert len(embeddings) == 3072  # text-embedding-3-large的维度
            
            print(f"✅ 嵌入模型连接成功: 生成了 {len(embeddings)} 维向量")
            
        except Exception as e:
            pytest.fail(f"嵌入模型连接失败: {str(e)}")
    
    @pytest.mark.skipif(not os.getenv("DASHSCOPE_API_KEY"), reason="DASHSCOPE_API_KEY not set")
    def test_reranking_model_connection(self):
        """测试重排序模型连接"""
        try:
            # 测试primary模型
            reranking_model = self.model_config.get_reranking_model("primary")
            assert reranking_model is not None
            assert isinstance(reranking_model, DashScopeRerank)
            
            # 简单的重排序测试
            query = "什么是机器学习"
            documents = [
                "机器学习是人工智能的一个分支",
                "今天天气很好",
                "深度学习是机器学习的子领域"
            ]
            
            results = reranking_model.rerank(query, documents, top_n=3)
            assert results is not None
            assert len(results) <= 3
            assert all("relevance_score" in result for result in results)
            assert all("document" in result for result in results)
            
            print(f"✅ 重排序模型连接成功: 处理了 {len(results)} 个文档")
            for i, result in enumerate(results):
                print(f"   {i+1}. [分数: {result['relevance_score']:.4f}] {result['document'][:30]}...")
            
        except Exception as e:
            pytest.fail(f"重排序模型连接失败: {str(e)}")
    
    def test_vector_store_config(self):
        """测试向量存储配置"""
        vector_stores = self.model_config._config["vector_stores"]
        
        # 测试primary配置
        assert "primary" in vector_stores
        primary_config = vector_stores["primary"]
        assert primary_config["name"] == "milvus"
        assert primary_config["provider"] == "langchain_milvus"
        assert "connection_args" in primary_config
    
    def test_model_fallback_config(self):
        """测试模型fallback配置"""
        model_switching = self.model_config._config["model_switching"]
        
        assert model_switching["enabled"] is True
        assert "fallback_chain" in model_switching
        
        fallback_chain = model_switching["fallback_chain"]
        assert "chat" in fallback_chain
        assert "embedding" in fallback_chain
        assert fallback_chain["chat"] == ["primary", "fallback"]
        assert fallback_chain["embedding"] == ["primary", "fallback"]
    
    def test_model_with_fallback(self):
        """测试带fallback的模型获取"""
        # 测试聊天模型fallback（不需要实际API调用）
        try:
            # 这里不会真正调用API，只是测试配置加载
            available_models = self.model_config.list_available_models("chat")
            assert "chat" in available_models
            assert "primary" in available_models["chat"]
            assert "fallback" in available_models["chat"]
            
            # 测试嵌入模型
            available_models = self.model_config.list_available_models("embedding")
            assert "embedding" in available_models
            assert "primary" in available_models["embedding"]
            assert "fallback" in available_models["embedding"]
            
            print("✅ 模型fallback配置测试通过")
            
        except Exception as e:
            pytest.fail(f"模型fallback配置测试失败: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_async_reranking(self):
        """测试异步重排序功能"""
        if not os.getenv("DASHSCOPE_API_KEY"):
            pytest.skip("DASHSCOPE_API_KEY not set")
        
        try:
            reranking_model = self.model_config.get_reranking_model("primary")
            
            query = "人工智能的应用"
            documents = [
                "人工智能在医疗领域有广泛应用",
                "今天的午餐很美味",
                "机器学习算法不断发展"
            ]
            
            # 测试异步重排序
            results = await reranking_model.arerank(query, documents, top_n=2)
            assert results is not None
            assert len(results) <= 2
            
            print(f"✅ 异步重排序测试通过: 处理了 {len(results)} 个文档")
            
        except Exception as e:
            pytest.fail(f"异步重排序测试失败: {str(e)}")
    
    def test_model_info_retrieval(self):
        """测试模型信息获取"""
        try:
            # 测试获取聊天模型信息
            chat_info = self.model_config.get_model_info("chat", "primary")
            assert chat_info["name"] == "gpt-4"
            assert chat_info["provider"] == "langchain_openai"
            
            # 测试获取嵌入模型信息
            embedding_info = self.model_config.get_model_info("embedding", "primary")
            assert embedding_info["name"] == "text-embedding-3-large"
            assert embedding_info["provider"] == "langchain_openai"
            
            # 测试获取重排序模型信息
            reranking_info = self.model_config.get_model_info("reranking", "primary")
            assert reranking_info["name"] == "gte-rerank-v2"
            assert reranking_info["provider"] == "dashscope"
            
            print("✅ 模型信息获取测试通过")
            
        except Exception as e:
            pytest.fail(f"模型信息获取测试失败: {str(e)}")
    
    def test_performance_config(self):
        """测试性能配置"""
        performance_config = self.model_config.get_performance_config()
        
        assert "max_concurrent_requests" in performance_config
        assert "cache" in performance_config
        assert "batch_processing" in performance_config
        
        max_concurrent = performance_config["max_concurrent_requests"]
        assert max_concurrent["chat"] == 10
        assert max_concurrent["embedding"] == 20
        assert max_concurrent["reranking"] == 15
        
        print("✅ 性能配置测试通过")
    
    def test_monitoring_config(self):
        """测试监控配置"""
        monitoring_config = self.model_config.get_monitoring_config()
        
        assert "logging" in monitoring_config
        assert "cost_tracking" in monitoring_config
        assert "performance_tracking" in monitoring_config
        
        cost_tracking = monitoring_config["cost_tracking"]
        assert cost_tracking["enabled"] is True
        assert cost_tracking["daily_limit"] == 50.0
        
        print("✅ 监控配置测试通过")


def run_connection_tests():
    """运行连接测试的便捷函数"""
    print("🚀 开始模型连接测试...")
    print("="*60)
    
    test_instance = TestModelConnections()
    test_instance.setup_class()
    
    # 基础配置测试
    print("📋 测试配置文件加载...")
    test_instance.test_model_config_loading()
    test_instance.test_chat_model_config()
    test_instance.test_embedding_model_config()
    test_instance.test_reranking_model_config()
    print("✅ 配置文件测试通过\n")
    
    # API连接测试
    print("🔌 测试API连接...")
    
    if os.getenv("OPENAI_API_KEY"):
        print("🔑 检测到 OPENAI_API_KEY，测试OpenAI连接...")
        try:
            test_instance.test_chat_model_connection()
            test_instance.test_embedding_model_connection()
        except Exception as e:
            print(f"❌ OpenAI连接测试失败: {e}")
    else:
        print("⚠️  未设置 OPENAI_API_KEY，跳过OpenAI连接测试")
    
    if os.getenv("DASHSCOPE_API_KEY"):
        print("🔑 检测到 DASHSCOPE_API_KEY，测试DashScope连接...")
        try:
            test_instance.test_reranking_model_connection()
        except Exception as e:
            print(f"❌ DashScope连接测试失败: {e}")
    else:
        print("⚠️  未设置 DASHSCOPE_API_KEY，跳过DashScope连接测试")
    
    print("\n🎯 测试其他功能...")
    test_instance.test_vector_store_config()
    test_instance.test_model_fallback_config()
    test_instance.test_model_with_fallback()
    test_instance.test_model_info_retrieval()
    test_instance.test_performance_config()
    test_instance.test_monitoring_config()
    
    print("\n" + "="*60)
    print("🎉 模型连接测试完成！")
    
    # 显示环境变量状态
    print("\n📊 环境变量状态:")
    print(f"   OPENAI_API_KEY: {'✅ 已设置' if os.getenv('OPENAI_API_KEY') else '❌ 未设置'}")
    print(f"   DASHSCOPE_API_KEY: {'✅ 已设置' if os.getenv('DASHSCOPE_API_KEY') else '❌ 未设置'}")
    print(f"   LANGSMITH_API_KEY: {'✅ 已设置' if os.getenv('LANGSMITH_API_KEY') else '❌ 未设置'}")


if __name__ == "__main__":
    # 直接运行测试
    run_connection_tests()