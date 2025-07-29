"""
配置模块单元测试
"""

import pytest
import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, Mock

from config.settings import Settings, ModelConfig


class TestSettings:
    """Settings类测试"""
    
    def test_default_values(self):
        """测试默认配置值"""
        settings = Settings()
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8888
        assert settings.debug is False
        assert settings.cors_enabled is True
    
    def test_env_override(self):
        """测试环境变量覆盖"""
        with patch.dict(os.environ, {
            "API_PORT": "9000",
            "DEBUG": "true",
            "LOG_LEVEL": "DEBUG"
        }):
            settings = Settings()
            assert settings.api_port == 9000
            assert settings.debug is True
            assert settings.log_level == "DEBUG"
    
    def test_allowed_origins_list(self):
        """测试CORS源列表解析"""
        settings = Settings(allowed_origins="http://localhost:3000,http://localhost:8080")
        expected = ["http://localhost:3000", "http://localhost:8080"]
        assert settings.allowed_origins_list == expected
        
        settings_wildcard = Settings(allowed_origins="*")
        assert settings_wildcard.allowed_origins_list == ["*"]
    
    def test_supported_file_types_list(self):
        """测试支持文件类型列表解析"""
        settings = Settings(supported_file_types="pdf,txt,md,docx")
        expected = ["pdf", "txt", "md", "docx"]
        assert settings.supported_file_types_list == expected
    
    def test_langsmith_config(self):
        """测试LangSmith配置"""
        with patch.dict(os.environ, {
            "LANGSMITH_TRACING": "true",
            "LANGSMITH_API_KEY": "test-key"
        }):
            settings = Settings()
            assert settings.langsmith_tracing is True
            assert settings.langsmith_api_key == "test-key"


class TestModelConfig:
    """ModelConfig类测试"""
    
    def test_load_config_success(self, models_config_file):
        """测试成功加载配置"""
        config = ModelConfig(config_path=str(models_config_file))
        assert config._config is not None
        assert "chat_models" in config._config
        assert "embedding_models" in config._config
    
    def test_load_config_file_not_found(self):
        """测试配置文件不存在"""
        with pytest.raises(FileNotFoundError, match="模型配置文件未找到"):
            ModelConfig(config_path="nonexistent.yaml")
    
    def test_load_config_invalid_yaml(self, temp_config_dir):
        """测试无效YAML格式"""
        invalid_file = temp_config_dir / "invalid.yaml"
        with open(invalid_file, 'w') as f:
            f.write("invalid: yaml: content:")
        
        with pytest.raises(ValueError, match="模型配置文件格式错误"):
            ModelConfig(config_path=str(invalid_file))
    
    @patch('config.settings.ChatOpenAI')
    def test_get_chat_model_primary(self, mock_chat_openai, models_config_file):
        """测试获取主聊天模型"""
        mock_instance = Mock()
        mock_chat_openai.return_value = mock_instance
        
        config = ModelConfig(config_path=str(models_config_file))
        model = config.get_chat_model("primary")
        
        assert model == mock_instance
        mock_chat_openai.assert_called_once()
    
    @patch('config.settings.ChatOpenAI')
    def test_get_chat_model_default(self, mock_chat_openai, models_config_file):
        """测试获取默认聊天模型"""
        mock_instance = Mock()
        mock_chat_openai.return_value = mock_instance
        
        config = ModelConfig(config_path=str(models_config_file))
        model = config.get_chat_model()  # 不指定模型名
        
        assert model == mock_instance
    
    def test_get_chat_model_not_found(self, models_config_file):
        """测试获取不存在的聊天模型"""
        config = ModelConfig(config_path=str(models_config_file))
        
        with pytest.raises(ValueError, match="聊天模型 'nonexistent' 未找到"):
            config.get_chat_model("nonexistent")
    
    @patch('config.settings.OpenAIEmbeddings')
    def test_get_embedding_model(self, mock_embeddings, models_config_file):
        """测试获取嵌入模型"""
        mock_instance = Mock()
        mock_embeddings.return_value = mock_instance
        
        config = ModelConfig(config_path=str(models_config_file))
        model = config.get_embedding_model("primary")
        
        assert model == mock_instance
        mock_embeddings.assert_called_once()
    
    def test_get_embedding_model_not_found(self, models_config_file):
        """测试获取不存在的嵌入模型"""
        config = ModelConfig(config_path=str(models_config_file))
        
        with pytest.raises(ValueError, match="嵌入模型 'nonexistent' 未找到"):
            config.get_embedding_model("nonexistent")
    
    @patch('config.settings.Milvus')
    @patch('config.settings.OpenAIEmbeddings')
    def test_get_vector_store(self, mock_embeddings, mock_milvus, models_config_file):
        """测试获取向量存储"""
        mock_embedding_instance = Mock()
        mock_embeddings.return_value = mock_embedding_instance
        mock_vector_instance = Mock()
        mock_milvus.return_value = mock_vector_instance
        
        config = ModelConfig(config_path=str(models_config_file))
        store = config.get_vector_store("primary")
        
        assert store == mock_vector_instance
        mock_milvus.assert_called_once()
    
    def test_get_text_splitter_config(self, models_config_file):
        """测试获取文本分割器配置"""
        config = ModelConfig(config_path=str(models_config_file))
        splitter_config = config.get_text_splitter_config("recursive")
        
        assert splitter_config["class"] == "RecursiveCharacterTextSplitter"
        assert splitter_config["provider"] == "langchain_core"
        assert "parameters" in splitter_config
    
    def test_get_text_splitter_config_not_found(self, models_config_file):
        """测试获取不存在的文本分割器配置"""
        config = ModelConfig(config_path=str(models_config_file))
        
        with pytest.raises(ValueError, match="文本分割器 'nonexistent' 未找到"):
            config.get_text_splitter_config("nonexistent")
    
    def test_get_fallback_strategy(self, models_config_file):
        """测试获取fallback策略"""
        config = ModelConfig(config_path=str(models_config_file))
        strategy = config.get_fallback_strategy()
        
        assert strategy["enabled"] is True
        assert strategy["max_retries"] == 3
        assert strategy["retry_delay"] == 1.0
    
    def test_get_performance_config(self, models_config_file):
        """测试获取性能配置"""
        config = ModelConfig(config_path=str(models_config_file))
        performance = config.get_performance_config()
        
        assert "max_concurrent_requests" in performance
        assert "cache" in performance
        assert performance["cache"]["enabled"] is True
    
    def test_model_caching(self, models_config_file):
        """测试模型实例缓存"""
        with patch('config.settings.ChatOpenAI') as mock_chat:
            mock_instance = Mock()
            mock_chat.return_value = mock_instance
            
            config = ModelConfig(config_path=str(models_config_file))
            
            # 第一次调用
            model1 = config.get_chat_model("primary")
            # 第二次调用
            model2 = config.get_chat_model("primary")
            
            # 应该返回同一个实例
            assert model1 == model2
            # ChatOpenAI只应该被调用一次
            assert mock_chat.call_count == 1


class TestConfigSingletons:
    """测试配置单例"""
    
    def test_get_settings_singleton(self):
        """测试Settings单例"""
        from config.settings import get_settings
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2
    
    @patch('config.settings.ModelConfig')
    def test_get_model_config_singleton(self, mock_model_config):
        """测试ModelConfig单例"""
        from config.settings import get_model_config
        
        mock_instance = Mock()
        mock_model_config.return_value = mock_instance
        
        config1 = get_model_config()
        config2 = get_model_config()
        
        assert config1 is config2
        # ModelConfig只应该被实例化一次
        assert mock_model_config.call_count == 1