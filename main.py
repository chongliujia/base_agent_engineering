"""
RAG系统主入口文件
"""

import uvicorn
from config.settings import get_settings

def main():
    """启动应用"""
    settings = get_settings()
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers if not settings.api_reload else 1,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
        access_log=True,
    )

if __name__ == "__main__":
    main()