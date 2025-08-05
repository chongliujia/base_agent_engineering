"""
AI Consultation Assistant API - Intelligent Q&A supporting web search and knowledge base retrieval
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
    """Chat request model"""
    query: str = Field(..., min_length=1, max_length=1000, description="User question")
    collection_name: Optional[str] = Field(None, description="Specify knowledge base collection name")
    search_strategy: Optional[str] = Field("both", description="Retrieval strategy: knowledge_only, web_only, both")
    prompt_template: Optional[str] = Field(None, description="Custom prompt template name")
    stream: bool = Field(False, description="Whether to use streaming response")
    max_web_results: int = Field(5, ge=1, le=10, description="Maximum web search results")
    max_kb_results: int = Field(5, ge=1, le=10, description="Maximum knowledge base retrieval results")


class ChatResponse(BaseModel):
    """Chat response model"""
    query: str
    response: str
    sources: Dict[str, List[Dict[str, Any]]]
    metadata: Dict[str, Any]
    timestamp: str
    processing_time: float


class KnowledgeBaseInfo(BaseModel):
    """Knowledge base information model"""
    name: str
    description: str
    document_count: int
    collection_name: str
    last_updated: str


@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(request: ChatRequest) -> ChatResponse:
    """
    Chat with AI consultation assistant
    
    Supported features:
    - Knowledge base retrieval
    - Web search
    - Intelligent strategy selection
    - Custom prompts
    """
    start_time = datetime.now()
    
    try:
        # Switch knowledge base (if specified)
        if request.collection_name:
            kb_manager = get_knowledge_base_manager()
            available_kbs = kb_manager.list_knowledge_bases()
            
            if request.collection_name not in available_kbs:
                raise HTTPException(
                    status_code=404,
                    detail=f"Knowledge base '{request.collection_name}' does not exist"
                )
            
            # Temporarily switch knowledge base
            original_collection = get_settings().current_collection_name
            get_settings().current_collection_name = request.collection_name
        
        # Set workflow parameters
        workflow_result = await rag_workflow.run(request.query)
        
        # Handle LangGraph return result format
        if isinstance(workflow_result, dict):
            # LangGraph's ainvoke may return dict format
            workflow_state = RAGState(**workflow_result)
        else:
            # Direct RAGState object
            workflow_state = workflow_result
        
        # Ensure all necessary attributes exist
        if not hasattr(workflow_state, 'documents') or workflow_state.documents is None:
            workflow_state.documents = []
        if not hasattr(workflow_state, 'web_results') or workflow_state.web_results is None:
            workflow_state.web_results = []
        if not hasattr(workflow_state, 'metadata') or workflow_state.metadata is None:
            workflow_state.metadata = {}
        if not hasattr(workflow_state, 'response') or workflow_state.response is None:
            workflow_state.response = "Sorry, unable to generate response."
            
        # Manually set retrieval strategy (if specified)
        if request.search_strategy != "both":
            workflow_state.metadata["retrieval_strategy"] = request.search_strategy
        
        # 构建响应
        sources = {
            "knowledge_base": [],
            "web_search": []
        }
        
        # Organize knowledge base sources
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
                print(f"Error processing knowledge base document: {e}")
                continue
        
        # Organize web search sources
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
                print(f"Error processing web search result: {e}")
                continue
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Build metadata
        metadata = {
            **workflow_state.metadata,
            "collection_used": request.collection_name or get_settings().current_collection_name,
            "search_strategy": request.search_strategy,
            "knowledge_retrieved": len(workflow_state.documents),
            "web_retrieved": len(workflow_state.web_results),
            "processing_time": processing_time
        }
        
        # Restore original knowledge base settings
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
        # Restore original knowledge base settings (error case)
        if request.collection_name:
            get_settings().current_collection_name = original_collection
            
        raise HTTPException(status_code=500, detail=f"Error occurred while processing request: {str(e)}")


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat interface
    """
    async def generate_stream():
        try:
            # Detect query language and select corresponding progress messages
            from src.prompts.prompt_manager import get_prompt_manager
            prompt_manager = get_prompt_manager()
            detected_lang = prompt_manager.detect_language(request.query)
            
            # Select messages based on language
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
                    "start": "Starting query processing...",
                    "analysis": "Analyzing query...",
                    "retrieval": "Retrieving information...",
                    "fusion": "Fusing information...",
                    "context": "Building context...",
                    "generation": "Generating response...",
                    "error_prefix": "Error occurred during processing: ",
                    "default_response": "Sorry, unable to generate response."
                }
            
            # Send start signal
            yield f"data: {json.dumps({'type': 'start', 'message': messages['start']}, ensure_ascii=False)}\n\n"
            
            # Define streaming callback function
            async def stream_callback(stage: str, data: str = None):
                if stage in messages:
                    yield f"data: {json.dumps({'type': 'progress', 'stage': stage, 'message': messages[stage]}, ensure_ascii=False)}\n\n"
                elif data:
                    # If it's generated text data, output progressively
                    yield f"data: {json.dumps({'type': 'chunk', 'content': data}, ensure_ascii=False)}\n\n"
            
            # Use queue to implement true streaming output
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
            
            # Create background task to execute workflow
            async def run_workflow():
                nonlocal workflow_complete, workflow_result, workflow_error
                try:
                    workflow_result = await rag_workflow.run(request.query, stream_callback=sync_callback)
                    workflow_complete = True
                except Exception as e:
                    workflow_error = e
                    workflow_complete = True
            
            # Start background workflow task
            workflow_task = asyncio.create_task(run_workflow())
            
            # Output streaming data in real-time
            while not workflow_complete:
                # Output all data in queue
                while stream_queue:
                    yield stream_queue.popleft()
                
                # Brief wait to avoid CPU intensive
                await asyncio.sleep(0.1)
            
            # Ensure workflow task completion
            await workflow_task
            
            # Output remaining queue data
            while stream_queue:
                yield stream_queue.popleft()
            
            # Check for errors
            if workflow_error:
                raise workflow_error
            
            # Handle LangGraph return result format
            if isinstance(workflow_result, dict):
                workflow_state = RAGState(**workflow_result)
            else:
                workflow_state = workflow_result
            
            # Ensure all necessary attributes exist
            if not hasattr(workflow_state, 'documents') or workflow_state.documents is None:
                workflow_state.documents = []
            if not hasattr(workflow_state, 'web_results') or workflow_state.web_results is None:
                workflow_state.web_results = []
            if not hasattr(workflow_state, 'response') or workflow_state.response is None:
                workflow_state.response = messages["default_response"]
            
            # Send final completion signal (only includes metadata, no duplicate response content)
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
            # Use detected language to display error message
            try:
                from src.prompts.prompt_manager import get_prompt_manager
                prompt_manager = get_prompt_manager()
                detected_lang = prompt_manager.detect_language(request.query)
                error_prefix = "Error occurred during processing: " if detected_lang == "en" else "Error occurred during processing: "
            except:
                error_prefix = "Error occurred during processing: "
                
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
    """Get all available knowledge bases"""
    try:
        kb_manager = get_knowledge_base_manager()
        knowledge_bases = kb_manager.list_knowledge_bases()
        
        result = []
        for kb_name in knowledge_bases:
            try:
                stats = kb_manager.get_knowledge_base_stats(kb_name)
                result.append(KnowledgeBaseInfo(
                    name=kb_name,
                    description=f"Knowledge Base {kb_name}",
                    document_count=stats.get("total_documents", 0),
                    collection_name=kb_name,
                    last_updated=stats.get("last_updated", "")
                ))
            except Exception as e:
                # If getting statistics fails, still return basic information
                result.append(KnowledgeBaseInfo(
                    name=kb_name,
                    description=f"Knowledge Base {kb_name}",
                    document_count=0,
                    collection_name=kb_name,
                    last_updated=""
                ))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get knowledge base list: {str(e)}")


@router.post("/switch-kb/{collection_name}")
async def switch_knowledge_base(collection_name: str):
    """Switch current knowledge base"""
    try:
        kb_manager = get_knowledge_base_manager()
        available_kbs = kb_manager.list_knowledge_bases()
        
        if collection_name not in available_kbs:
            raise HTTPException(
                status_code=404,
                detail=f"Knowledge base '{collection_name}' does not exist"
            )
        
        # Switch knowledge base
        get_settings().current_collection_name = collection_name
        
        return {
            "message": f"Switched to knowledge base: {collection_name}",
            "current_kb": collection_name,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to switch knowledge base: {str(e)}")


@router.get("/prompts")
async def list_prompts(category: Optional[str] = Query(None, description="Prompt category")):
    """Get available prompt templates"""
    try:
        prompt_manager = get_prompt_manager()
        prompts = prompt_manager.list_prompts(category=category)
        
        return {
            "prompts": prompts,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get prompt list: {str(e)}")


@router.post("/prompts/{prompt_name}")
async def add_custom_prompt(
    prompt_name: str,
    prompt_data: Dict[str, Any] = Body(...)
):
    """Add custom prompt"""
    try:
        from src.prompts.prompt_manager import PromptTemplate
        
        prompt_manager = get_prompt_manager()
        
        # Create prompt template
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
                "message": f"Prompt '{prompt_name}' added successfully",
                "prompt_name": prompt_name,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save prompt")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add prompt: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check"""
    try:
        # Check core component status
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
