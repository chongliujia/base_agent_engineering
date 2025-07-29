"""
应用配置管理 - 集成LangChain和LangGraph，支持多厂商模型
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Type
from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv

# 加载项目环境变量（优先级高于系统环境变量）
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file, override=True)

# LangChain导入
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
# 使用新的 langchain-milvus 包替代弃用的导入
from langchain_milvus import Milvus
from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore

# 导入自定义重排序模型
from src.reranking.dashscope_rerank import DashScopeRerank


class Settings(BaseSettings):
    """应用配置类"""
    
    # API服务配置
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8888, env="API_PORT")
    api_workers: int = Field(default=4, env="API_WORKERS")
    api_reload: bool = Field(default=False, env="API_RELOAD")
    
    # 数据库配置
    milvus_host: str = Field(default="localhost", env="MILVUS_HOST")
    milvus_port: int = Field(default=19530, env="MILVUS_PORT")
    milvus_user: str = Field(default="", env="MILVUS_USER")
    milvus_password: str = Field(default="", env="MILVUS_PASSWORD")
    
    # Redis配置
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_password: str = Field(default="", env="REDIS_PASSWORD")
    
    # 管理界面
    attu_port: int = Field(default=8889, env="ATTU_PORT")
    
    # API密钥
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    dashscope_api_key: str = Field(default="", env="DASHSCOPE_API_KEY")
    tavily_api_key: str = Field(default="", env="TAVILY_API_KEY")
    langsmith_api_key: str = Field(default="", env="LANGSMITH_API_KEY")
    
    # 模型配置
    default_chat_model: str = Field(default="primary", env="DEFAULT_CHAT_MODEL")
    default_embedding_model: str = Field(default="primary", env="DEFAULT_EMBEDDING_MODEL")
    default_reranking_model: str = Field(default="primary", env="DEFAULT_RERANKING_MODEL")
    
    # LangSmith配置
    langsmith_project: str = Field(default="base-agent-engineering", env="LANGSMITH_PROJECT")
    langsmith_tracing: bool = Field(default=False, env="LANGSMITH_TRACING")
    
    # 日志配置
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    log_file: str = Field(default="logs/app.log", env="LOG_FILE")
    
    # 安全配置
    api_key_header: str = Field(default="X-API-Key", env="API_KEY_HEADER")
    allowed_origins: str = Field(default="*", env="ALLOWED_ORIGINS")
    cors_enabled: bool = Field(default=True, env="CORS_ENABLED")
    
    # 性能配置
    max_concurrent_requests: int = Field(default=50, env="MAX_CONCURRENT_REQUESTS")
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")
    embedding_batch_size: int = Field(default=100, env="EMBEDDING_BATCH_SIZE")
    reranking_batch_size: int = Field(default=32, env="RERANKING_BATCH_SIZE")
    
    # 存储配置
    knowledge_base_path: str = Field(default="./knowledge_base", env="KNOWLEDGE_BASE_PATH")
    upload_max_size: str = Field(default="100MB", env="UPLOAD_MAX_SIZE")
    supported_file_types: str = Field(default="pdf,txt,md,docx,pptx", env="SUPPORTED_FILE_TYPES")
    
    # 监控配置
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    
    # 开发配置
    debug: bool = Field(default=False, env="DEBUG")
    testing: bool = Field(default=False, env="TESTING")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def model_post_init(self, __context: Any) -> None:
        """初始化后设置环境变量"""
        if self.langsmith_tracing and self.langsmith_api_key:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = self.langsmith_api_key
            os.environ["LANGCHAIN_PROJECT"] = self.langsmith_project
    
    @property
    def allowed_origins_list(self) -> list:
        """获取允许的CORS源列表"""
        if self.allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    @property
    def supported_file_types_list(self) -> list:
        """获取支持的文件类型列表"""
        return [ft.strip() for ft in self.supported_file_types.split(",")]


class ModelConfig:
    """LangChain模型配置管理器 - 支持多厂商模型"""
    
    def __init__(self, config_path: str = "config/models.yaml"):
        self.config_path = Path(config_path)
        self._config: Optional[Dict[str, Any]] = None
        self._chat_models: Dict[str, BaseChatModel] = {}
        self._embedding_models: Dict[str, Embeddings] = {}
        self._vector_stores: Dict[str, VectorStore] = {}
        self._reranking_models: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """加载模型配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"模型配置文件未找到: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"模型配置文件格式错误: {e}")
    
    def _resolve_env_vars(self, value: str) -> str:
        """解析环境变量"""
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            if ":" in env_var:
                # 支持默认值: ${VAR:default}
                var_name, default = env_var.split(":", 1)
                return os.getenv(var_name, default)
            else:
                return os.getenv(env_var, "")
        return value
    
    def _build_headers(self, model_config: Dict[str, Any]) -> Dict[str, str]:
        """构建请求头"""
        headers = {}
        if "extra_headers" in model_config:
            headers.update(model_config["extra_headers"])
        return headers
    
    def get_chat_model(self, model_name: str = None) -> BaseChatModel:
        """获取LangChain聊天模型实例"""
        if model_name is None:
            model_name = self._config["default_models"]["chat"]
        
        # 如果已经创建过，直接返回
        if model_name in self._chat_models:
            return self._chat_models[model_name]
        
        if model_name not in self._config["chat_models"]:
            raise ValueError(f"聊天模型 '{model_name}' 未找到")
        
        model_config = self._config["chat_models"][model_name]
        provider = model_config["provider"]
        
        # 根据provider创建对应的LangChain模型
        if provider == "langchain_openai":
            # OpenAI或兼容接口
            chat_params = {
                "model": model_config["name"],
                "api_key": os.getenv(model_config["api_key_env"]),
                **model_config["parameters"]
            }
            
            # 如果配置了base_url，添加到参数中
            if model_config.get("base_url"):
                chat_params["base_url"] = model_config["base_url"]
            
            model = ChatOpenAI(**chat_params)
        else:
            raise ValueError(f"不支持的聊天模型provider: {provider}")
        
        self._chat_models[model_name] = model
        return model
    
    def get_embedding_model(self, model_name: str = None) -> Embeddings:
        """获取LangChain嵌入模型实例"""
        if model_name is None:
            model_name = self._config["default_models"]["embedding"]
        
        if model_name in self._embedding_models:
            return self._embedding_models[model_name]
        
        if model_name not in self._config["embedding_models"]:
            raise ValueError(f"嵌入模型 '{model_name}' 未找到")
        
        model_config = self._config["embedding_models"][model_name]
        provider = model_config["provider"]
        
        if provider == "langchain_openai":
            # 构建嵌入模型参数
            embedding_params = {
                "api_key": os.getenv(model_config["api_key_env"]),
                "model": model_config["parameters"]["model"],  # 明确指定模型名称
            }
            
            # 添加base_url（如果配置了）
            if "base_url" in model_config:
                embedding_params["base_url"] = model_config["base_url"]
            
            # 添加其他参数（排除model参数避免重复）
            for key, value in model_config["parameters"].items():
                if key != "model":  # 避免重复添加model参数
                    embedding_params[key] = value
            
            model = OpenAIEmbeddings(**embedding_params)
        elif provider == "langchain_community":
            # DashScope嵌入模型
            from langchain_community.embeddings import DashScopeEmbeddings
            
            embedding_params = {
                "model": model_config["parameters"]["model"],
                "dashscope_api_key": os.getenv(model_config["api_key_env"])
            }
            
            model = DashScopeEmbeddings(**embedding_params)
        else:
            raise ValueError(f"不支持的嵌入模型provider: {provider}")
        
        self._embedding_models[model_name] = model
        return model
    
    def get_vector_store(self, store_name: str = None) -> VectorStore:
        """获取LangChain向量存储实例"""
        if store_name is None:
            store_name = self._config["default_models"]["vector_store"]
        
        if store_name in self._vector_stores:
            return self._vector_stores[store_name]
        
        if store_name not in self._config["vector_stores"]:
            raise ValueError(f"向量存储 '{store_name}' 未找到")
        
        store_config = self._config["vector_stores"][store_name]
        embedding_model = self.get_embedding_model()
        
        if store_config["provider"] == "langchain_milvus":
            # 替换环境变量
            connection_args = {}
            for key, value in store_config["connection_args"].items():
                connection_args[key] = self._resolve_env_vars(value)
            
            # 构建 Milvus 参数
            milvus_params = {
                "embedding_function": embedding_model,
                "connection_args": connection_args,
                "collection_name": store_config["collection_name"],
                "enable_dynamic_field": store_config.get("enable_dynamic_field", True),
                "auto_id": store_config.get("auto_id", True),
                "drop_old": store_config.get("drop_old", False)
            }
            
            store = Milvus(**milvus_params)
        else:
            raise ValueError(f"不支持的向量存储provider: {store_config['provider']}")
        
        self._vector_stores[store_name] = store
        return store
    
    def get_reranking_model(self, model_name: str = None) -> Any:
        """获取重排序模型实例"""
        if model_name is None:
            model_name = self._config["default_models"]["reranking"]
        
        # 如果已经创建过，直接返回
        if model_name in self._reranking_models:
            return self._reranking_models[model_name]
        
        if model_name not in self._config["reranking_models"]:
            raise ValueError(f"重排序模型 '{model_name}' 未找到")
        
        model_config = self._config["reranking_models"][model_name]
        provider = model_config["provider"]
        
        if provider == "dashscope":
            # DashScope重排序模型
            model = DashScopeRerank(
                model=model_config["parameters"]["model"],
                api_key=os.getenv(model_config["api_key_env"]),
                top_n=model_config["parameters"]["top_n"],
                return_documents=model_config["parameters"]["return_documents"]
            )
        else:
            raise ValueError(f"不支持的重排序模型provider: {provider}")
        
        self._reranking_models[model_name] = model
        return model
    
    def get_model_with_fallback(self, model_type: str, model_name: str = None) -> Any:
        """获取带fallback的模型"""
        fallback_config = self._config.get("model_switching", {})
        if not fallback_config.get("enabled", False):
            # 如果没有启用fallback，直接返回指定模型
            if model_type == "chat":
                return self.get_chat_model(model_name)
            elif model_type == "embedding":
                return self.get_embedding_model(model_name)
            elif model_type == "reranking":
                return self.get_reranking_model(model_name)
            else:
                raise ValueError(f"不支持的模型类型: {model_type}")
        
        # 获取fallback链
        fallback_chain = fallback_config.get("fallback_chain", {}).get(model_type, [])
        if model_name and model_name not in fallback_chain:
            fallback_chain = [model_name] + fallback_chain
        
        # 尝试按顺序创建模型
        for model_name_in_chain in fallback_chain:
            try:
                if model_type == "chat":
                    return self.get_chat_model(model_name_in_chain)
                elif model_type == "embedding":
                    return self.get_embedding_model(model_name_in_chain)
                elif model_type == "reranking":
                    return self.get_reranking_model(model_name_in_chain)
            except Exception as e:
                print(f"模型 {model_name_in_chain} 创建失败: {e}")
                continue
        
        raise ValueError(f"所有 {model_type} 模型都创建失败")
    
    def get_text_splitter_config(self, splitter_name: str = None) -> Dict[str, Any]:
        """获取文本分割器配置"""
        if splitter_name is None:
            splitter_name = self._config["default_models"]["text_splitter"]
        
        if splitter_name not in self._config["text_splitters"]:
            raise ValueError(f"文本分割器 '{splitter_name}' 未找到")
        
        return self._config["text_splitters"][splitter_name]
    
    def get_document_loader_config(self, file_type: str) -> Dict[str, Any]:
        """根据文件类型获取文档加载器配置"""
        if file_type not in self._config["document_loaders"]:
            raise ValueError(f"不支持的文件类型: {file_type}")
        
        return self._config["document_loaders"][file_type]
    
    def get_langgraph_config(self) -> Dict[str, Any]:
        """获取LangGraph工作流配置"""
        return self._config.get("langgraph", {})
    
    def get_model_switching_config(self) -> Dict[str, Any]:
        """获取模型切换策略配置"""
        return self._config.get("model_switching", {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """获取性能配置"""
        return self._config.get("performance", {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """获取监控配置"""
        return self._config.get("monitoring", {})
    
    def list_available_models(self, model_type: str = None) -> Dict[str, list]:
        """列出可用的模型"""
        result = {}
        if model_type is None or model_type == "chat":
            result["chat"] = list(self._config.get("chat_models", {}).keys())
        if model_type is None or model_type == "embedding":
            result["embedding"] = list(self._config.get("embedding_models", {}).keys())
        if model_type is None or model_type == "reranking":
            result["reranking"] = list(self._config.get("reranking_models", {}).keys())
        return result
    
    def get_model_info(self, model_type: str, model_name: str) -> Dict[str, Any]:
        """获取模型详细信息"""
        config_key = f"{model_type}_models"
        if config_key not in self._config:
            raise ValueError(f"不支持的模型类型: {model_type}")
        
        if model_name not in self._config[config_key]:
            raise ValueError(f"模型 '{model_name}' 未找到")
        
        return self._config[config_key][model_name]


@lru_cache()
def get_settings() -> Settings:
    """获取应用配置实例（单例）"""
    return Settings()


@lru_cache()
def get_model_config() -> ModelConfig:
    """获取模型配置实例（单例）"""
    return ModelConfig()


# 导出配置实例
settings = get_settings()
model_config = get_model_config()