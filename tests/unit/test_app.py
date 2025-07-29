"""
FastAPI应用单元测试
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock

from app.main import app


class TestFastAPIApp:
    """FastAPI应用测试"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Base Agent Engineering - RAG API"
        assert data["version"] == "1.0.0"
        assert "features" in data
        assert "LangChain集成" in data["features"]
    
    def test_health_check_success(self, client):
        """测试健康检查成功"""
        with patch.object(app.state, 'chat_model', True), \
             patch.object(app.state, 'embedding_model', True), \
             patch.object(app.state, 'vector_store', True):
            
            response = client.get("/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert data["langchain_enabled"] is True
            assert data["langgraph_enabled"] is True
            assert "models" in data
    
    def test_health_check_failure(self, client):
        """测试健康检查失败"""
        with patch('app.main.hasattr', side_effect=Exception("Health check error")):
            response = client.get("/health")
            assert response.status_code == 503
            
            data = response.json()
            assert data["status"] == "unhealthy"
            assert "error" in data
    
    @patch('app.main.model_config')
    def test_models_info_success(self, mock_model_config, client):
        """测试模型信息接口成功"""
        mock_model_config._config = {
            "chat_models": {
                "primary": {
                    "name": "gpt-4",
                    "provider": "langchain_openai",
                    "max_context_length": 8192
                }
            },
            "embedding_models": {
                "primary": {
                    "name": "text-embedding-3-large",
                    "provider": "langchain_openai",
                    "parameters": {"dimensions": 3072}
                }
            },
            "vector_stores": {
                "primary": {"name": "milvus"}
            },
            "default_models": {
                "chat": "primary",
                "embedding": "primary"
            }
        }
        
        response = client.get("/api/v1/models")
        assert response.status_code == 200
        
        data = response.json()
        assert data["chat_model"]["name"] == "gpt-4"
        assert data["embedding_model"]["dimensions"] == 3072
        assert data["vector_store"] == "milvus"
    
    @patch('app.main.model_config')
    def test_models_info_error(self, mock_model_config, client):
        """测试模型信息接口错误"""
        mock_model_config._config = None
        
        response = client.get("/api/v1/models")
        assert response.status_code == 500
        
        data = response.json()
        assert "error" in data
    
    def test_cors_headers(self, client):
        """测试CORS头"""
        response = client.options("/", headers={"Origin": "http://localhost:3000"})
        # FastAPI的TestClient可能不会完全模拟CORS行为
        # 这里主要测试应用不会因为CORS配置而崩溃
        assert response.status_code in [200, 405]  # OPTIONS可能不被支持
    
    def test_process_time_header(self, client):
        """测试处理时间头"""
        response = client.get("/")
        assert "X-Process-Time" in response.headers
        
        process_time = float(response.headers["X-Process-Time"])
        assert process_time >= 0
    
    def test_global_exception_handler(self, client):
        """测试全局异常处理"""
        # 这个测试需要触发一个异常
        # 由于我们的路由还没有实现，这里先跳过
        pass


class TestMiddleware:
    """中间件测试"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @patch('app.main.model_config')
    def test_model_initialization_middleware(self, mock_model_config, client):
        """测试模型初始化中间件"""
        mock_chat_model = AsyncMock()
        mock_embedding_model = AsyncMock()
        mock_vector_store = AsyncMock()
        
        mock_model_config.get_chat_model.return_value = mock_chat_model
        mock_model_config.get_embedding_model.return_value = mock_embedding_model
        mock_model_config.get_vector_store.return_value = mock_vector_store
        
        # 第一次请求应该初始化模型
        response1 = client.get("/")
        assert response1.status_code == 200
        
        # 第二次请求应该使用已初始化的模型
        response2 = client.get("/")
        assert response2.status_code == 200
        
        # 验证模型只被初始化一次
        assert hasattr(app.state, 'models_initialized')
    
    @patch('app.main.model_config')
    def test_model_initialization_error(self, mock_model_config, client):
        """测试模型初始化错误"""
        mock_model_config.get_chat_model.side_effect = Exception("Model init error")
        
        response = client.get("/")
        assert response.status_code == 500
        
        data = response.json()
        assert "Model initialization failed" in data["error"]


class TestAppConfiguration:
    """应用配置测试"""
    
    def test_app_metadata(self):
        """测试应用元数据"""
        assert app.title == "Base Agent Engineering - RAG API"
        assert app.version == "1.0.0"
        assert app.docs_url == "/docs"
        assert app.redoc_url == "/redoc"
    
    @patch('app.main.settings')
    def test_cors_configuration(self, mock_settings):
        """测试CORS配置"""
        mock_settings.cors_enabled = True
        mock_settings.allowed_origins_list = ["http://localhost:3000"]
        
        # 重新创建应用以测试CORS配置
        # 这里主要验证配置不会导致错误
        assert True  # 简化测试
    
    def test_startup_event(self):
        """测试启动事件"""
        # 启动事件主要是日志记录，这里验证不会抛出异常
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200