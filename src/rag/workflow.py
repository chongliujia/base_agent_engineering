"""
基于LangGraph的RAG工作流
"""

import time
import asyncio
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.documents import Document
from pydantic import BaseModel

from config.settings import get_model_config


class RAGState(BaseModel):
    """RAG工作流状态"""
    query: str
    messages: List[BaseMessage] = []
    documents: List[Document] = []
    web_results: List[Dict[str, Any]] = []
    context: str = ""
    response: str = ""
    metadata: Dict[str, Any] = {}
    
    class Config:
        arbitrary_types_allowed = True


class RAGWorkflow:
    """RAG工作流管理器"""
    
    def __init__(self):
        self.model_config = get_model_config()
        self.chat_model = self.model_config.get_chat_model()
        self.embedding_model = self.model_config.get_embedding_model()
        self.vector_store = self.model_config.get_vector_store()
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """构建简化的LangGraph工作流 - 统一并行检索"""
        workflow = StateGraph(RAGState)
        
        # 添加节点 - 简化版本
        workflow.add_node("query_analyzer", self.analyze_query)
        workflow.add_node("parallel_retrieval", self.parallel_retrieval)
        workflow.add_node("information_fusion", self.fuse_information)
        workflow.add_node("context_builder", self.build_context)
        workflow.add_node("response_generator", self.generate_response)
        
        # 设置入口点
        workflow.set_entry_point("query_analyzer")
        
        # 简化的线性流程
        workflow.add_edge("query_analyzer", "parallel_retrieval")
        workflow.add_edge("parallel_retrieval", "information_fusion")
        workflow.add_edge("information_fusion", "context_builder")
        workflow.add_edge("context_builder", "response_generator")
        workflow.add_edge("response_generator", END)
        
        return workflow.compile()
    
    async def analyze_query(self, state: RAGState) -> RAGState:
        """分析查询意图和特征"""
        # 简化的查询分析，为并行检索做准备
        query = state.query
        
        # 基础查询特征分析
        state.metadata.update({
            "query_length": len(query),
            "has_question_mark": "?" in query,
            "has_keywords": any(kw in query.lower() for kw in ["什么", "如何", "怎么", "为什么"]),
            "timestamp": time.time()
        })
        
        print(f"🔍 查询分析: {query[:30]}{'...' if len(query) > 30 else ''}")
        return state
    
    async def parallel_retrieval(self, state: RAGState) -> RAGState:
        """核心并行检索 - 同时执行知识库和网络搜索"""
        import asyncio
        
        print("🔄 并行检索中...")
        start_time = time.time()
        
        # 创建并行任务
        knowledge_task = self._retrieve_knowledge_task(state)
        web_task = self._search_web_task(state)
        
        try:
            # 并行执行，允许部分失败
            knowledge_results, web_results = await asyncio.gather(
                knowledge_task, 
                web_task,
                return_exceptions=True
            )
            
            # 统计成功的检索源
            successful_sources = []
            total_results = 0
            
            # 处理知识库检索结果
            if isinstance(knowledge_results, Exception):
                print(f"📚 知识库: ❌ {str(knowledge_results)[:50]}...")
                state.metadata["knowledge_error"] = str(knowledge_results)
                state.metadata["knowledge_retrieved"] = 0
            else:
                state.documents.extend(knowledge_results)
                kb_count = len(knowledge_results)
                state.metadata["knowledge_retrieved"] = kb_count
                total_results += kb_count
                if kb_count > 0:
                    successful_sources.append("知识库")
                    print(f"📚 知识库: ✅ {kb_count}个文档")
            
            # 处理网络搜索结果
            if isinstance(web_results, Exception):
                print(f"🌐 网络搜索: ❌ {str(web_results)[:50]}...")
                state.metadata["web_error"] = str(web_results)
                state.metadata["web_retrieved"] = 0
            else:
                state.web_results.extend(web_results)
                web_count = len(web_results)
                state.metadata["web_retrieved"] = web_count
                total_results += web_count
                if web_count > 0:
                    successful_sources.append("网络搜索")
                    print(f"🌐 网络搜索: ✅ {web_count}个结果")
            
            # 记录检索统计
            parallel_time = time.time() - start_time
            state.metadata.update({
                "parallel_retrieval_time": round(parallel_time, 2),
                "total_results": total_results,
                "successful_sources": successful_sources,
                "retrieval_mode": self._determine_actual_mode(successful_sources)
            })
            
            # 输出检索摘要
            if successful_sources:
                sources_str = " + ".join(successful_sources)
                print(f"⚡ 检索完成: {sources_str} ({total_results}个结果, {parallel_time:.2f}s)")
            else:
                print(f"⚠️ 检索完成: 无可用结果 ({parallel_time:.2f}s)")
            
        except Exception as e:
            state.metadata["parallel_error"] = str(e)
            print(f"❌ 并行检索系统错误: {e}")
        
        return state
    
    def _determine_actual_mode(self, successful_sources: list) -> str:
        """根据实际检索结果确定执行模式"""
        if not successful_sources:
            return "无结果"
        elif len(successful_sources) == 2:
            return "混合模式"
        elif "知识库" in successful_sources:
            return "知识库模式"
        elif "网络搜索" in successful_sources:
            return "网络模式"
        else:
            return "未知模式"
    
    async def _retrieve_knowledge_task(self, state: RAGState) -> List:
        """知识库检索任务 - 用于并行执行"""
        try:
            # 使用知识库管理器来避免异步循环问题
            from src.knowledge_base.knowledge_base_manager import get_knowledge_base_manager
            
            kb_manager = get_knowledge_base_manager()
            result = await kb_manager.search(state.query, k=3, include_scores=False)
            
            if result.get("success"):
                # 转换为Document对象
                docs = []
                for item in result.get("results", []):
                    from langchain_core.documents import Document
                    doc = Document(
                        page_content=item["content"], 
                        metadata=item["metadata"]
                    )
                    docs.append(doc)
                return docs
            else:
                raise Exception(result.get("message", "知识库搜索失败"))
                
        except Exception as e:
            # 抛出异常供并行处理器捕获
            raise e
    
    async def _search_web_task(self, state: RAGState) -> List:
        """网络搜索任务 - 用于并行执行"""
        try:
            from src.search.web_search import search_web
            
            web_results = await search_web(
                query=state.query,
                max_results=3,  # 限制为3个结果
                search_config={
                    "search_depth": "advanced",
                    "exclude_domains": ["pinterest.com", "twitter.com", "instagram.com"]
                }
            )
            
            return web_results if web_results else []
        except Exception as e:
            # 抛出异常供并行处理器捕获
            raise e
    
    async def fuse_information(self, state: RAGState) -> RAGState:
        """融合信息"""
        # 合并知识库文档和网络搜索结果
        all_sources = []
        
        # 添加知识库文档
        for doc in state.documents:
            all_sources.append({
                "content": doc.page_content,
                "source": "knowledge_base",
                "metadata": doc.metadata
            })
        
        # 添加网络搜索结果
        for result in state.web_results:
            all_sources.append({
                "content": result["content"],
                "source": "web_search",
                "metadata": {"url": result["url"], "title": result["title"]}
            })
        
        state.metadata["total_sources"] = len(all_sources)
        state.metadata["fused_sources"] = all_sources
        
        return state
    
    async def build_context(self, state: RAGState) -> RAGState:
        """构建上下文"""
        sources = state.metadata.get("fused_sources", [])
        
        # 分别构建知识库和网络搜索上下文
        knowledge_sources = [s for s in sources if s['source'] == 'knowledge_base']
        web_sources = [s for s in sources if s['source'] == 'web_search']
        
        # 构建知识库上下文
        knowledge_context = ""
        if knowledge_sources:
            kb_parts = []
            for i, source in enumerate(knowledge_sources[:3]):
                metadata = source.get('metadata', {})
                source_info = f"文档: {metadata.get('filename', '未知')}"
                kb_parts.append(f"{source_info}\n内容: {source['content'][:500]}")
            knowledge_context = "\n\n".join(kb_parts)
        
        # 构建网络搜索上下文  
        web_context = ""
        if web_sources:
            web_parts = []
            for i, source in enumerate(web_sources[:3]):
                metadata = source.get('metadata', {})
                source_info = f"标题: {metadata.get('title', '未知')}\n链接: {metadata.get('url', '未知')}"
                web_parts.append(f"{source_info}\n内容: {source['content'][:500]}")
            web_context = "\n\n".join(web_parts)
        
        # 保存结构化上下文
        state.metadata["knowledge_context"] = knowledge_context
        state.metadata["web_context"] = web_context
        
        # 构建完整上下文（向后兼容）
        all_parts = []
        if knowledge_context:
            all_parts.append(f"=== 知识库信息 ===\n{knowledge_context}")
        if web_context:
            all_parts.append(f"=== 网络搜索信息 ===\n{web_context}")
        
        state.context = "\n\n".join(all_parts)
        return state
    
    async def generate_response(self, state: RAGState, stream_callback=None) -> RAGState:
        """智能回答生成 - 基于实际检索结果选择提示词"""
        try:
            from src.prompts.prompt_manager import render_prompt, get_prompt_manager
            
            # 获取提示词管理器并检测语言
            prompt_manager = get_prompt_manager()
            
            # 根据实际检索模式选择提示词策略
            retrieval_mode = state.metadata.get("retrieval_mode", "混合模式") 
            knowledge_context = state.metadata.get("knowledge_context", "")
            web_context = state.metadata.get("web_context", "")
            
            # 智能提示词选择（语言自适应）
            if retrieval_mode == "知识库模式" and knowledge_context:
                # 知识库模式暂时保持原有逻辑
                prompt = render_prompt("knowledge_only", 
                                     knowledge_context=knowledge_context,
                                     query=state.query)
                prompt_type = "knowledge_only"
            elif retrieval_mode == "网络模式" and web_context:
                # 网络模式暂时保持原有逻辑  
                prompt = render_prompt("web_only",
                                     web_context=web_context, 
                                     query=state.query)
                prompt_type = "web_only"
            elif retrieval_mode == "混合模式":
                # 使用语言自适应的RAG提示词
                adaptive_template = prompt_manager.select_adaptive_prompt(state.query)
                prompt = render_prompt(adaptive_template,
                                     knowledge_context=knowledge_context or "No relevant knowledge base information available",
                                     web_context=web_context or "No relevant web search information available", 
                                     query=state.query)
                prompt_type = adaptive_template
            else:
                # 无检索结果的回答
                prompt = f"""作为AI助手，我需要基于现有知识回答用户问题。

用户问题：{state.query}

由于当前没有找到相关的知识库文档或网络搜索结果，我将基于训练数据中的知识来回答，但请注意信息可能不是最新的。

回答："""
                prompt_type = "fallback"

            # 使用聊天模型生成回答
            messages = [HumanMessage(content=prompt)]
            
            if stream_callback:
                # 流式输出模式
                full_response = ""
                async for chunk in self.chat_model.astream(messages):
                    if hasattr(chunk, 'content') and chunk.content:
                        full_response += chunk.content
                        if stream_callback:
                            if asyncio.iscoroutinefunction(stream_callback):
                                await stream_callback(chunk.content)
                            else:
                                stream_callback("chunk", chunk.content)
                
                state.response = full_response
            else:
                # 非流式输出模式
                response = await self.chat_model.ainvoke(messages)
                state.response = response.content
            
            state.messages.append(HumanMessage(content=state.query))
            state.messages.append(AIMessage(content=state.response))
            
            # 记录生成信息
            state.metadata.update({
                "prompt_type_used": prompt_type,
                "response_length": len(state.response),
                "generation_successful": True
            })
            
            print(f"💬 回答生成: {prompt_type} ({len(state.response)}字符)")
            
        except Exception as e:
            state.response = f"抱歉，生成回答时出现错误：{str(e)}"
            state.metadata.update({
                "generation_error": str(e),
                "generation_successful": False
            })
            print(f"❌ 回答生成失败: {e}")
        
        return state
    
    async def run(self, query: str, stream_callback=None) -> RAGState:
        """运行RAG工作流"""
        initial_state = RAGState(query=query)
        
        # 由于LangGraph不直接支持流式回调，我们需要手动执行步骤
        if stream_callback:
            # 手动执行工作流步骤以支持流式输出
            if callable(stream_callback):
                stream_callback("analysis")
            state = await self.analyze_query(initial_state)
            
            if callable(stream_callback):
                stream_callback("retrieval")
            state = await self.parallel_retrieval(state)
            
            if callable(stream_callback):
                stream_callback("fusion")
            state = await self.fuse_information(state)
            
            if callable(stream_callback):
                stream_callback("context")
            state = await self.build_context(state)
            
            if callable(stream_callback):
                stream_callback("generation")
            state = await self.generate_response(state, stream_callback)
            return state
        else:
            # 使用标准工作流
            final_state = await self.workflow.ainvoke(initial_state)
            return final_state


# 创建全局工作流实例
rag_workflow = RAGWorkflow()