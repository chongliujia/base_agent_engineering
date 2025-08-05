"""
RAG workflow based on LangGraph
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
    """RAG workflow state"""
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
    """RAG workflow manager"""
    
    def __init__(self):
        self.model_config = get_model_config()
        self.chat_model = self.model_config.get_chat_model()
        self.embedding_model = self.model_config.get_embedding_model()
        self.vector_store = self.model_config.get_vector_store()
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build simplified LangGraph workflow - unified parallel retrieval"""
        workflow = StateGraph(RAGState)
        
        # Add nodes - simplified version
        workflow.add_node("query_analyzer", self.analyze_query)
        workflow.add_node("parallel_retrieval", self.parallel_retrieval)
        workflow.add_node("information_fusion", self.fuse_information)
        workflow.add_node("context_builder", self.build_context)
        workflow.add_node("response_generator", self.generate_response)
        
        # Set entry point
        workflow.set_entry_point("query_analyzer")
        
        # Simplified linear flow
        workflow.add_edge("query_analyzer", "parallel_retrieval")
        workflow.add_edge("parallel_retrieval", "information_fusion")
        workflow.add_edge("information_fusion", "context_builder")
        workflow.add_edge("context_builder", "response_generator")
        workflow.add_edge("response_generator", END)
        
        return workflow.compile()
    
    async def analyze_query(self, state: RAGState) -> RAGState:
        """Analyze query intent and characteristics"""
        # Simplified query analysis, prepare for parallel retrieval
        query = state.query
        
        # Basic query feature analysis
        state.metadata.update({
            "query_length": len(query),
            "has_question_mark": "?" in query,
            "has_keywords": any(kw in query.lower() for kw in ["what", "how", "why", "when", "什么", "如何", "怎么", "为什么"]),
            "timestamp": time.time()
        })
        
        print(f"🔍 Query analysis: {query[:30]}{'...' if len(query) > 30 else ''}")
        return state
    
    async def parallel_retrieval(self, state: RAGState) -> RAGState:
        """Core parallel retrieval - execute knowledge base and web search simultaneously"""
        import asyncio
        
        print("🔄 Parallel retrieval in progress...")
        start_time = time.time()
        
        # Create parallel tasks
        knowledge_task = self._retrieve_knowledge_task(state)
        web_task = self._search_web_task(state)
        
        try:
            # Execute in parallel, allow partial failures
            knowledge_results, web_results = await asyncio.gather(
                knowledge_task, 
                web_task,
                return_exceptions=True
            )
            
            # Count successful retrieval sources
            successful_sources = []
            total_results = 0
            
            # Process knowledge base retrieval results
            if isinstance(knowledge_results, Exception):
                print(f"📚 Knowledge base: ❌ {str(knowledge_results)[:50]}...")
                state.metadata["knowledge_error"] = str(knowledge_results)
                state.metadata["knowledge_retrieved"] = 0
            else:
                state.documents.extend(knowledge_results)
                kb_count = len(knowledge_results)
                state.metadata["knowledge_retrieved"] = kb_count
                total_results += kb_count
                if kb_count > 0:
                    successful_sources.append("Knowledge Base")
                    print(f"📚 Knowledge base: ✅ {kb_count} documents")
            
            # Process web search results
            if isinstance(web_results, Exception):
                print(f"🌐 Web search: ❌ {str(web_results)[:50]}...")
                state.metadata["web_error"] = str(web_results)
                state.metadata["web_retrieved"] = 0
            else:
                state.web_results.extend(web_results)
                web_count = len(web_results)
                state.metadata["web_retrieved"] = web_count
                total_results += web_count
                if web_count > 0:
                    successful_sources.append("Web Search")
                    print(f"🌐 Web search: ✅ {web_count} results")
            
            # Record retrieval statistics
            parallel_time = time.time() - start_time
            state.metadata.update({
                "parallel_retrieval_time": round(parallel_time, 2),
                "total_results": total_results,
                "successful_sources": successful_sources,
                "retrieval_mode": self._determine_actual_mode(successful_sources)
            })
            
            # Output retrieval summary
            if successful_sources:
                sources_str = " + ".join(successful_sources)
                print(f"⚡ Retrieval completed: {sources_str} ({total_results} results, {parallel_time:.2f}s)")
            else:
                print(f"⚠️ Retrieval completed: No available results ({parallel_time:.2f}s)")
            
        except Exception as e:
            state.metadata["parallel_error"] = str(e)
            print(f"❌ Parallel retrieval system error: {e}")
        
        return state
    
    def _determine_actual_mode(self, successful_sources: list) -> str:
        """Determine execution mode based on actual retrieval results"""
        if not successful_sources:
            return "No Results"
        elif len(successful_sources) == 2:
            return "Hybrid Mode"
        elif "Knowledge Base" in successful_sources:
            return "Knowledge Base Mode"
        elif "Web Search" in successful_sources:
            return "Web Mode"
        else:
            return "Unknown Mode"
    
    async def _retrieve_knowledge_task(self, state: RAGState) -> List:
        """Knowledge base retrieval task - for parallel execution"""
        try:
            # Use knowledge base manager to avoid async loop issues
            from src.knowledge_base.knowledge_base_manager import get_knowledge_base_manager
            
            kb_manager = get_knowledge_base_manager()
            result = await kb_manager.search(state.query, k=3, include_scores=False)
            
            if result.get("success"):
                # Convert to Document objects
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
                raise Exception(result.get("message", "Knowledge base search failed"))
                
        except Exception as e:
            # Raise exception for parallel processor to catch
            raise e
    
    async def _search_web_task(self, state: RAGState) -> List:
        """Web search task - for parallel execution"""
        try:
            from src.search.web_search import search_web
            
            web_results = await search_web(
                query=state.query,
                max_results=3,  # Limit to 3 results
                search_config={
                    "search_depth": "advanced",
                    "exclude_domains": ["pinterest.com", "twitter.com", "instagram.com"]
                }
            )
            
            return web_results if web_results else []
        except Exception as e:
            # Raise exception for parallel processor to catch
            raise e
    
    async def fuse_information(self, state: RAGState) -> RAGState:
        """Fuse information"""
        # Merge knowledge base documents and web search results
        all_sources = []
        
        # Add knowledge base documents
        for doc in state.documents:
            all_sources.append({
                "content": doc.page_content,
                "source": "knowledge_base",
                "metadata": doc.metadata
            })
        
        # Add web search results
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
        """Build context"""
        sources = state.metadata.get("fused_sources", [])
        
        # Build knowledge base and web search contexts separately
        knowledge_sources = [s for s in sources if s['source'] == 'knowledge_base']
        web_sources = [s for s in sources if s['source'] == 'web_search']
        
        # Build knowledge base context
        knowledge_context = ""
        if knowledge_sources:
            kb_parts = []
            for i, source in enumerate(knowledge_sources[:3]):
                metadata = source.get('metadata', {})
                source_info = f"Document: {metadata.get('filename', 'Unknown')}"
                kb_parts.append(f"{source_info}\nContent: {source['content'][:500]}")
            knowledge_context = "\n\n".join(kb_parts)
        
        # Build web search context  
        web_context = ""
        if web_sources:
            web_parts = []
            for i, source in enumerate(web_sources[:3]):
                metadata = source.get('metadata', {})
                source_info = f"Title: {metadata.get('title', 'Unknown')}\nLink: {metadata.get('url', 'Unknown')}"
                web_parts.append(f"{source_info}\nContent: {source['content'][:500]}")
            web_context = "\n\n".join(web_parts)
        
        # Save structured context
        state.metadata["knowledge_context"] = knowledge_context
        state.metadata["web_context"] = web_context
        
        # Build complete context (backward compatibility)
        all_parts = []
        if knowledge_context:
            all_parts.append(f"=== Knowledge Base Information ===\n{knowledge_context}")
        if web_context:
            all_parts.append(f"=== Web Search Information ===\n{web_context}")
        
        state.context = "\n\n".join(all_parts)
        return state
    
    async def generate_response(self, state: RAGState, stream_callback=None) -> RAGState:
        """Intelligent response generation - select prompt based on actual retrieval results"""
        try:
            from src.prompts.prompt_manager import render_prompt, get_prompt_manager
            
            # Get prompt manager and detect language
            prompt_manager = get_prompt_manager()
            
            # Select prompt strategy based on actual retrieval mode
            retrieval_mode = state.metadata.get("retrieval_mode", "Hybrid Mode") 
            knowledge_context = state.metadata.get("knowledge_context", "")
            web_context = state.metadata.get("web_context", "")
            
            # Smart prompt selection (language adaptive)
            if retrieval_mode == "Knowledge Base Mode" and knowledge_context:
                # Knowledge base mode maintains original logic for now
                prompt = render_prompt("knowledge_only", 
                                     knowledge_context=knowledge_context,
                                     query=state.query)
                prompt_type = "knowledge_only"
            elif retrieval_mode == "Web Mode" and web_context:
                # Web mode maintains original logic for now  
                prompt = render_prompt("web_only",
                                     web_context=web_context, 
                                     query=state.query)
                prompt_type = "web_only"
            elif retrieval_mode == "Hybrid Mode":
                # Use language-adaptive RAG prompt
                adaptive_template = prompt_manager.select_adaptive_prompt(state.query)
                prompt = render_prompt(adaptive_template,
                                     knowledge_context=knowledge_context or "No relevant knowledge base information available",
                                     web_context=web_context or "No relevant web search information available", 
                                     query=state.query)
                prompt_type = adaptive_template
            else:
                # Response without retrieval results
                prompt = f"""As an AI assistant, I need to answer user questions based on existing knowledge.

User Question: {state.query}

Since no relevant knowledge base documents or web search results were found, I will answer based on knowledge from training data, but please note the information may not be up to date.

Answer:"""
                prompt_type = "fallback"

            # Generate response using chat model
            messages = [HumanMessage(content=prompt)]
            
            if stream_callback:
                # Streaming output mode
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
                # Non-streaming output mode
                response = await self.chat_model.ainvoke(messages)
                state.response = response.content
            
            state.messages.append(HumanMessage(content=state.query))
            state.messages.append(AIMessage(content=state.response))
            
            # Record generation information
            state.metadata.update({
                "prompt_type_used": prompt_type,
                "response_length": len(state.response),
                "generation_successful": True
            })
            
            print(f"💬 Response generated: {prompt_type} ({len(state.response)} characters)")
            
        except Exception as e:
            state.response = f"Sorry, an error occurred while generating the response: {str(e)}"
            state.metadata.update({
                "generation_error": str(e),
                "generation_successful": False
            })
            print(f"❌ Response generation failed: {e}")
        
        return state
    
    async def run(self, query: str, stream_callback=None) -> RAGState:
        """Run RAG workflow"""
        initial_state = RAGState(query=query)
        
        # Since LangGraph doesn't directly support streaming callbacks, we need to manually execute steps
        if stream_callback:
            # Manually execute workflow steps to support streaming output
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
            # Use standard workflow
            final_state = await self.workflow.ainvoke(initial_state)
            return final_state


# Create global workflow instance
rag_workflow = RAGWorkflow()