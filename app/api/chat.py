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

from src.rag.workflow import rag_workflow, RAGState
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
        workflow_result = await rag_workflow.run(request.query)
        
        # 处理LangGraph返回的结果格式
        if isinstance(workflow_result, dict):
            # LangGraph的ainvoke可能返回dict格式
            workflow_state = RAGState(**workflow_result)
        else:
            # 直接是RAGState对象
            workflow_state = workflow_result
        
        # 确保所有必要属性存在
        if not hasattr(workflow_state, 'documents') or workflow_state.documents is None:
            workflow_state.documents = []
        if not hasattr(workflow_state, 'web_results') or workflow_state.web_results is None:
            workflow_state.web_results = []
        if not hasattr(workflow_state, 'metadata') or workflow_state.metadata is None:
            workflow_state.metadata = {}
        if not hasattr(workflow_state, 'response') or workflow_state.response is None:
            workflow_state.response = "抱歉，无法生成回答。"
            
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
            try:
                content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
                metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                sources["knowledge_base"].append({
                    "content": content[:200] + "..." if len(content) > 200 else content,
                    "metadata": metadata,
                    "relevance_score": getattr(doc, 'score', 0.0)
                })
            except Exception as e:
                print(f"处理知识库文档时出错: {e}")
                continue
        
        # 整理网络搜索来源
        for result in workflow_state.web_results:
            try:
                content = result.get("content", "") if isinstance(result, dict) else str(result)
                sources["web_search"].append({
                    "title": result.get("title", "") if isinstance(result, dict) else "",
                    "content": content[:200] + "..." if len(content) > 200 else content,
                    "url": result.get("url", "") if isinstance(result, dict) else "",
                    "score": result.get("score", 0.0) if isinstance(result, dict) else 0.0
                })
            except Exception as e:
                print(f"处理网络搜索结果时出错: {e}")
                continue
        
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
            # 检测查询语言并选择相应的进度消息
            from src.prompts.prompt_manager import get_prompt_manager
            prompt_manager = get_prompt_manager()
            detected_lang = prompt_manager.detect_language(request.query)
            
            # 根据语言选择消息
            if detected_lang == "en":
                messages = {
                    "start": "Starting query processing...",
                    "analysis": "Analyzing query...",
                    "retrieval": "Retrieving information...",
                    "fusion": "Fusing information...",
                    "context": "Building context...",
                    "generation": "Generating response...",
                    "error_prefix": "Error occurred during processing: ",
                    "default_response": "Sorry, unable to generate response."
                }
            else:
                messages = {
                    "start": "开始处理查询...",
                    "analysis": "分析查询中...",
                    "retrieval": "检索信息中...",
                    "fusion": "融合信息中...",
                    "context": "构建上下文中...",
                    "generation": "生成回答中...",
                    "error_prefix": "处理过程中发生错误: ",
                    "default_response": "抱歉，无法生成回答。"
                }
            
            # 发送开始信号
            yield f"data: {json.dumps({'type': 'start', 'message': messages['start']}, ensure_ascii=False)}\n\n"
            
            # 定义流式回调函数
            async def stream_callback(stage: str, data: str = None):
                if stage in messages:
                    yield f"data: {json.dumps({'type': 'progress', 'stage': stage, 'message': messages[stage]}, ensure_ascii=False)}\n\n"
                elif data:
                    # 如果是生成的文本数据，逐步输出
                    yield f"data: {json.dumps({'type': 'chunk', 'content': data}, ensure_ascii=False)}\n\n"
            
            # 使用队列来实现真正的流式输出
            import asyncio
            from collections import deque
            
            stream_queue = deque()
            workflow_complete = False
            workflow_result = None
            workflow_error = None
            
            def sync_callback(stage: str, data: str = None):
                if stage in messages:
                    stream_queue.append(f"data: {json.dumps({'type': 'progress', 'stage': stage, 'message': messages[stage]}, ensure_ascii=False)}\n\n")
                elif data:
                    stream_queue.append(f"data: {json.dumps({'type': 'chunk', 'content': data}, ensure_ascii=False)}\n\n")
            
            # 创建后台任务执行工作流
            async def run_workflow():
                nonlocal workflow_complete, workflow_result, workflow_error
                try:
                    workflow_result = await rag_workflow.run(request.query, stream_callback=sync_callback)
                    workflow_complete = True
                except Exception as e:
                    workflow_error = e
                    workflow_complete = True
            
            # 启动后台工作流任务
            workflow_task = asyncio.create_task(run_workflow())
            
            # 实时输出流式数据
            while not workflow_complete:
                # 输出队列中的所有数据
                while stream_queue:
                    yield stream_queue.popleft()
                
                # 短暂等待避免CPU密集
                await asyncio.sleep(0.1)
            
            # 确保工作流任务完成
            await workflow_task
            
            # 输出剩余的队列数据
            while stream_queue:
                yield stream_queue.popleft()
            
            # 检查是否有错误
            if workflow_error:
                raise workflow_error
            
            # 处理LangGraph返回的结果格式
            if isinstance(workflow_result, dict):
                workflow_state = RAGState(**workflow_result)
            else:
                workflow_state = workflow_result
            
            # 确保所有必要属性存在
            if not hasattr(workflow_state, 'documents') or workflow_state.documents is None:
                workflow_state.documents = []
            if not hasattr(workflow_state, 'web_results') or workflow_state.web_results is None:
                workflow_state.web_results = []
            if not hasattr(workflow_state, 'response') or workflow_state.response is None:
                workflow_state.response = messages["default_response"]
            
            # 发送最终完成信号（仅包含元数据，不重复response内容）
            result = {
                "type": "complete",
                "metadata": {
                    "query": request.query,
                    "knowledge_retrieved": len(workflow_state.documents),
                    "web_retrieved": len(workflow_state.web_results),
                    "total_chunks_sent": True
                }
            }
            
            yield f"data: {json.dumps(result, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            # 使用检测到的语言显示错误消息
            try:
                from src.prompts.prompt_manager import get_prompt_manager
                prompt_manager = get_prompt_manager()
                detected_lang = prompt_manager.detect_language(request.query)
                error_prefix = "Error occurred during processing: " if detected_lang == "en" else "处理过程中发生错误: "
            except:
                error_prefix = "处理过程中发生错误: "
                
            error_msg = {
                "type": "error",
                "message": f"{error_prefix}{str(e)}"
            }
            yield f"data: {json.dumps(error_msg, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
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
