"""
AI咨询助手API - 支持联网搜索和知识库检索的智能问答
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Body, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json

from src.rag.workflow import rag_workflow
from src.prompts.prompt_manager import get_prompt_manager
from src.knowledge_base.knowledge_base_manager import get_knowledge_base_manager
from config.settings import get_settings

router = APIRouter()


class ChatRequest(BaseModel):
    """聊天请求模型"""
    query: str = Field(..., min_length=1, max_length=1000, description="用户问题")
    collection_name: Optional[str] = Field(None, description="指定知识库集合名称")
    search_strategy: Optional[str] = Field("both", description="检索策略: knowledge_only, web_only, both")
    prompt_template: Optional[str] = Field(None, description="自定义提示词模板名称")
    stream: bool = Field(False, description="是否流式响应")
    max_web_results: int = Field(5, ge=1, le=10, description="最大网络搜索结果数")
    max_kb_results: int = Field(5, ge=1, le=10, description="最大知识库检索结果数")


class ChatResponse(BaseModel):
    """聊天响应模型"""
    query: str
    response: str
    sources: Dict[str, List[Dict[str, Any]]]
    metadata: Dict[str, Any]
    timestamp: str
    processing_time: float


class KnowledgeBaseInfo(BaseModel):
    """知识库信息模型"""
    name: str
    description: str
    document_count: int
    collection_name: str
    last_updated: str


@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(request: ChatRequest) -> ChatResponse:
    """
    与AI咨询助手对话
    
    支持功能：
    - 知识库检索
    - 联网搜索
    - 智能策略选择
    - 自定义提示词
    """
    start_time = datetime.now()
    
    try:
        # 切换知识库（如果指定）
        if request.collection_name:
            kb_manager = get_knowledge_base_manager()
            available_kbs = kb_manager.list_knowledge_bases()
            
            if request.collection_name not in available_kbs:
                raise HTTPException(
                    status_code=404,
                    detail=f"知识库 '{request.collection_name}' 不存在"
                )
            
            # 临时切换知识库
            original_collection = get_settings().current_collection_name
            get_settings().current_collection_name = request.collection_name
        
        # 设置工作流参数
        workflow_state = await rag_workflow.run(request.query)
        
        # 手动设置检索策略（如果指定）
        if request.search_strategy != "both":
            workflow_state.metadata["retrieval_strategy"] = request.search_strategy
        
        # 构建响应
        sources = {
            "knowledge_base": [],
            "web_search": []
        }
        
        # 整理知识库来源
        for doc in workflow_state.documents:
            sources["knowledge_base"].append({
                "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                "metadata": doc.metadata,
                "relevance_score": getattr(doc, 'score', 0.0)
            })
        
        # 整理网络搜索来源
        for result in workflow_state.web_results:
            sources["web_search"].append({
                "title": result.get("title", ""),
                "content": result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", ""),
                "url": result.get("url", ""),
                "score": result.get("score", 0.0)
            })
        
        # 计算处理时间
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 构建元数据
        metadata = {
            **workflow_state.metadata,
            "collection_used": request.collection_name or get_settings().current_collection_name,
            "search_strategy": request.search_strategy,
            "knowledge_retrieved": len(workflow_state.documents),
            "web_retrieved": len(workflow_state.web_results),
            "processing_time": processing_time
        }
        
        # 恢复原始知识库设置
        if request.collection_name:
            get_settings().current_collection_name = original_collection
        
        return ChatResponse(
            query=request.query,
            response=workflow_state.response,
            sources=sources,
            metadata=metadata,
            timestamp=datetime.now().isoformat(),
            processing_time=processing_time
        )
        
    except Exception as e:
        # 恢复原始知识库设置（错误情况）
        if request.collection_name:
            get_settings().current_collection_name = original_collection
            
        raise HTTPException(status_code=500, detail=f"处理请求时发生错误: {str(e)}")


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    流式对话接口
    """
    async def generate_stream():
        try:
            # 发送开始信号
            yield f"data: {json.dumps({'type': 'start', 'message': '开始处理查询...'}, ensure_ascii=False)}\n\n"
            
            # 执行工作流
            workflow_state = await rag_workflow.run(request.query)
            
            # 发送进度更新
            yield f"data: {json.dumps({'type': 'progress', 'message': '检索完成，生成回答中...'}, ensure_ascii=False)}\n\n"
            
            # 发送最终结果
            result = {
                "type": "complete",
                "query": request.query,
                "response": workflow_state.response,
                "metadata": {
                    "knowledge_retrieved": len(workflow_state.documents),
                    "web_retrieved": len(workflow_state.web_results)
                }
            }
            
            yield f"data: {json.dumps(result, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            error_msg = {
                "type": "error",
                "message": f"处理过程中发生错误: {str(e)}"
            }
            yield f"data: {json.dumps(error_msg, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )


@router.get("/knowledge-bases", response_model=List[KnowledgeBaseInfo])
async def list_knowledge_bases():
    """获取所有可用的知识库"""
    try:
        kb_manager = get_knowledge_base_manager()
        knowledge_bases = kb_manager.list_knowledge_bases()
        
        result = []
        for kb_name in knowledge_bases:
            try:
                stats = kb_manager.get_knowledge_base_stats(kb_name)
                result.append(KnowledgeBaseInfo(
                    name=kb_name,
                    description=f"知识库 {kb_name}",
                    document_count=stats.get("total_documents", 0),
                    collection_name=kb_name,
                    last_updated=stats.get("last_updated", "")
                ))
            except Exception as e:
                # 如果获取统计信息失败，仍然返回基本信息
                result.append(KnowledgeBaseInfo(
                    name=kb_name,
                    description=f"知识库 {kb_name}",
                    document_count=0,
                    collection_name=kb_name,
                    last_updated=""
                ))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识库列表失败: {str(e)}")


@router.post("/switch-kb/{collection_name}")
async def switch_knowledge_base(collection_name: str):
    """切换当前知识库"""
    try:
        kb_manager = get_knowledge_base_manager()
        available_kbs = kb_manager.list_knowledge_bases()
        
        if collection_name not in available_kbs:
            raise HTTPException(
                status_code=404,
                detail=f"知识库 '{collection_name}' 不存在"
            )
        
        # 切换知识库
        get_settings().current_collection_name = collection_name
        
        return {
            "message": f"已切换到知识库: {collection_name}",
            "current_kb": collection_name,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"切换知识库失败: {str(e)}")


@router.get("/prompts")
async def list_prompts(category: Optional[str] = Query(None, description="提示词类别")):
    """获取可用的提示词模板"""
    try:
        prompt_manager = get_prompt_manager()
        prompts = prompt_manager.list_prompts(category=category)
        
        return {
            "prompts": prompts,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取提示词列表失败: {str(e)}")


@router.post("/prompts/{prompt_name}")
async def add_custom_prompt(
    prompt_name: str,
    prompt_data: Dict[str, Any] = Body(...)
):
    """添加自定义提示词"""
    try:
        from src.prompts.prompt_manager import PromptTemplate
        
        prompt_manager = get_prompt_manager()
        
        # 创建提示词模板
        template = PromptTemplate(
            name=prompt_name,
            version=prompt_data.get("version", "1.0"),
            description=prompt_data.get("description", ""),
            template=prompt_data.get("template", ""),
            variables=prompt_data.get("variables", []),
            category=prompt_data.get("category", "custom")
        )
        
        success = prompt_manager.add_custom_prompt(template)
        
        if success:
            return {
                "message": f"提示词 '{prompt_name}' 添加成功",
                "prompt_name": prompt_name,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="保存提示词失败")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加提示词失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 检查核心组件状态
        settings = get_settings()
        
        status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "rag_workflow": "ok",
                "knowledge_base": "ok",
                "web_search": "ok" if settings.tavily_api_key else "not_configured",
                "prompt_manager": "ok"
            },
            "current_kb": settings.current_collection_name
        }
        
        return status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }