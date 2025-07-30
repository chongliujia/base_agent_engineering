"""
FastAPI应用主文件 - 集成LangChain和LangGraph
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging
import os

from config.settings import get_settings, get_model_config
from app.api import knowledge_base, chat  # API模块

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 获取配置
settings = get_settings()
model_config = get_model_config()

# 设置LangSmith追踪（如果启用）
if settings.langsmith_tracing and settings.langsmith_api_key:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
    logger.info("LangSmith tracing enabled")

# 创建FastAPI应用
app = FastAPI(
    title="Base Agent Engineering - RAG API",
    description="智能RAG系统API - 基于LangChain和LangGraph的检索增强生成",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS中间件
if settings.cors_enabled:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 请求时间中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# LangChain模型初始化中间件
@app.middleware("http")
async def initialize_models(request: Request, call_next):
    """确保LangChain模型已初始化"""
    try:
        # 预热模型（可选）
        if not hasattr(app.state, "models_initialized"):
            logger.info("Initializing LangChain models...")
            
            # 初始化默认模型
            chat_model = model_config.get_chat_model()
            embedding_model = model_config.get_embedding_model()
            vector_store = model_config.get_vector_store()
            
            app.state.chat_model = chat_model
            app.state.embedding_model = embedding_model
            app.state.vector_store = vector_store
            app.state.models_initialized = True
            
            logger.info("LangChain models initialized successfully")
        
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Model initialization error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Model initialization failed", "message": str(e)}
        )

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查接口"""
    try:
        # 检查模型状态
        models_status = {
            "chat_model": hasattr(app.state, "chat_model"),
            "embedding_model": hasattr(app.state, "embedding_model"),
            "vector_store": hasattr(app.state, "vector_store"),
        }
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0",
            "models": models_status,
            "langchain_enabled": True,
            "langgraph_enabled": True,
            "langsmith_tracing": settings.langsmith_tracing
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
        )

# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Base Agent Engineering - RAG API",
        "description": "基于LangChain和LangGraph的智能检索增强生成系统",
        "version": "1.0.0",
        "features": [
            "LangChain集成",
            "LangGraph工作流",
            "混合检索策略",
            "智能上下文工程",
            "流式响应",
            "模型fallback",
            "知识库管理",
            "联网搜索",
            "AI咨询助手",
            "可配置提示词"
        ],
        "docs": "/docs",
        "health": "/health",
        "apis": {
            "knowledge_base": "/api/v1/knowledge-base",
            "chat": "/api/v1/chat",
            "prompts": "/api/v1/prompts"
        }
    }

# 模型信息接口
@app.get("/api/v1/models")
async def get_models_info():
    """获取当前加载的模型信息"""
    try:
        chat_config = model_config._config["chat_models"][model_config._config["default_models"]["chat"]]
        embedding_config = model_config._config["embedding_models"][model_config._config["default_models"]["embedding"]]
        
        return {
            "chat_model": {
                "name": chat_config["name"],
                "provider": chat_config["provider"],
                "max_context_length": chat_config["max_context_length"]
            },
            "embedding_model": {
                "name": embedding_config["name"],
                "provider": embedding_config["provider"],
                "dimensions": embedding_config["parameters"]["dimensions"]
            },
            "vector_store": model_config._config["vector_stores"]["primary"]["name"],
            "langsmith_enabled": settings.langsmith_tracing
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to get model info", "message": str(e)}
        )

# 注册API路由
app.include_router(knowledge_base.router, prefix="/api/v1/knowledge-base", tags=["knowledge_base"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])

# 注册其他路由（预留）
# app.include_router(search.router, prefix="/api/v1", tags=["search"])
# app.include_router(admin.router, prefix="/api/v1", tags=["admin"])

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.debug else "An error occurred",
            "type": type(exc).__name__
        }
    )

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    logger.info("Starting Base Agent Engineering RAG API...")
    logger.info(f"LangSmith tracing: {settings.langsmith_tracing}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info("Available APIs:")
    logger.info("  - Knowledge Base: /api/v1/knowledge-base")
    logger.info("  - AI Chat: /api/v1/chat")
    logger.info("  - Prompts: /api/v1/prompts")
    
    # 初始化搜索连接
    try:
        from src.search.web_search import web_search_manager
        logger.info(f"Web search enabled: {bool(settings.tavily_api_key)}")
    except Exception as e:
        logger.warning(f"Web search initialization failed: {e}")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    logger.info("Shutting down Base Agent Engineering RAG API...")
    
    # 关闭搜索连接
    try:
        from src.search.web_search import close_search_connections
        await close_search_connections()
        logger.info("Web search connections closed")
    except Exception as e:
        logger.warning(f"Error closing web search connections: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )