"""
基于LangGraph的RAG工作流
"""

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
        """构建LangGraph工作流"""
        workflow = StateGraph(RAGState)
        
        # 添加节点
        workflow.add_node("query_analyzer", self.analyze_query)
        workflow.add_node("retrieval_router", self.route_retrieval)
        workflow.add_node("knowledge_retriever", self.retrieve_knowledge)
        workflow.add_node("web_searcher", self.search_web)
        workflow.add_node("information_fusion", self.fuse_information)
        workflow.add_node("context_builder", self.build_context)
        workflow.add_node("response_generator", self.generate_response)
        
        # 设置入口点
        workflow.set_entry_point("query_analyzer")
        
        # 添加边
        workflow.add_edge("query_analyzer", "retrieval_router")
        
        # 条件路由
        workflow.add_conditional_edges(
            "retrieval_router",
            self.decide_retrieval_strategy,
            {
                "knowledge_only": "knowledge_retriever",
                "web_only": "web_searcher", 
                "both": "knowledge_retriever",  # 先执行知识库检索
                "none": "context_builder"
            }
        )
        
        workflow.add_edge("knowledge_retriever", "information_fusion")
        workflow.add_edge("web_searcher", "information_fusion")
        workflow.add_edge("information_fusion", "context_builder")
        workflow.add_edge("context_builder", "response_generator")
        workflow.add_edge("response_generator", END)
        
        return workflow.compile()
    
    async def analyze_query(self, state: RAGState) -> RAGState:
        """分析查询意图"""
        # 这里可以添加查询分析逻辑
        # 例如：分类查询类型、提取关键词、判断是否需要实时信息等
        
        state.metadata["query_type"] = "general"  # 简化示例
        state.metadata["needs_realtime"] = False
        state.metadata["complexity"] = "medium"
        
        return state
    
    async def route_retrieval(self, state: RAGState) -> RAGState:
        """路由检索策略"""
        # 根据查询分析结果决定检索策略
        query_type = state.metadata.get("query_type", "general")
        needs_realtime = state.metadata.get("needs_realtime", False)
        
        if needs_realtime:
            state.metadata["retrieval_strategy"] = "web_only"
        elif "知识库" in state.query or "文档" in state.query:
            state.metadata["retrieval_strategy"] = "knowledge_only"
        else:
            state.metadata["retrieval_strategy"] = "both"
        
        return state
    
    def decide_retrieval_strategy(self, state: RAGState) -> str:
        """决定检索策略的条件函数"""
        return state.metadata.get("retrieval_strategy", "both")
    
    async def retrieve_knowledge(self, state: RAGState) -> RAGState:
        """从知识库检索"""
        try:
            # 使用向量存储检索相关文档
            docs = await self.vector_store.asimilarity_search(
                state.query, 
                k=5
            )
            state.documents.extend(docs)
            state.metadata["knowledge_retrieved"] = len(docs)
            
            # 如果策略是both，继续执行web搜索
            if state.metadata.get("retrieval_strategy") == "both":
                return await self.search_web(state)
            
        except Exception as e:
            state.metadata["knowledge_error"] = str(e)
        
        return state
    
    async def search_web(self, state: RAGState) -> RAGState:
        """网络搜索"""
        try:
            # 这里应该集成实际的网络搜索API
            # 暂时使用模拟数据
            web_results = [
                {
                    "title": "示例搜索结果",
                    "content": "这是一个示例搜索结果内容",
                    "url": "https://example.com",
                    "score": 0.9
                }
            ]
            state.web_results.extend(web_results)
            state.metadata["web_retrieved"] = len(web_results)
            
        except Exception as e:
            state.metadata["web_error"] = str(e)
        
        return state
    
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
        
        # 构建上下文字符串
        context_parts = []
        for i, source in enumerate(sources[:5]):  # 限制最多5个源
            context_parts.append(f"来源{i+1} ({source['source']}):\n{source['content']}")
        
        state.context = "\n\n".join(context_parts)
        return state
    
    async def generate_response(self, state: RAGState) -> RAGState:
        """生成回答"""
        try:
            # 构建提示词
            prompt = f"""基于以下上下文信息回答用户问题。

上下文信息：
{state.context}

用户问题：{state.query}

请提供准确、有用的回答，并在适当时引用来源。"""

            # 使用聊天模型生成回答
            messages = [HumanMessage(content=prompt)]
            response = await self.chat_model.ainvoke(messages)
            
            state.response = response.content
            state.messages.append(HumanMessage(content=state.query))
            state.messages.append(AIMessage(content=response.content))
            
        except Exception as e:
            state.response = f"抱歉，生成回答时出现错误：{str(e)}"
            state.metadata["generation_error"] = str(e)
        
        return state
    
    async def run(self, query: str) -> RAGState:
        """运行RAG工作流"""
        initial_state = RAGState(query=query)
        final_state = await self.workflow.ainvoke(initial_state)
        return final_state


# 创建全局工作流实例
rag_workflow = RAGWorkflow()