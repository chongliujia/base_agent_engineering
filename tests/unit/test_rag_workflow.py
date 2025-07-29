"""
RAG工作流单元测试
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.documents import Document

from src.rag.workflow import RAGState, RAGWorkflow


class TestRAGState:
    """RAG状态测试"""
    
    def test_rag_state_creation(self):
        """测试RAG状态创建"""
        state = RAGState(query="test query")
        assert state.query == "test query"
        assert state.messages == []
        assert state.documents == []
        assert state.web_results == []
        assert state.context == ""
        assert state.response == ""
        assert state.metadata == {}
    
    def test_rag_state_with_data(self):
        """测试带数据的RAG状态"""
        messages = [HumanMessage(content="hello")]
        documents = [Document(page_content="test", metadata={})]
        
        state = RAGState(
            query="test",
            messages=messages,
            documents=documents,
            metadata={"key": "value"}
        )
        
        assert state.messages == messages
        assert state.documents == documents
        assert state.metadata["key"] == "value"


class TestRAGWorkflow:
    """RAG工作流测试"""
    
    @pytest.fixture
    def mock_workflow(self):
        """模拟工作流"""
        with patch('src.rag.workflow.get_model_config') as mock_config:
            mock_model_config = Mock()
            mock_model_config.get_chat_model.return_value = AsyncMock()
            mock_model_config.get_embedding_model.return_value = AsyncMock()
            mock_model_config.get_vector_store.return_value = AsyncMock()
            mock_config.return_value = mock_model_config
            
            workflow = RAGWorkflow()
            return workflow
    
    @pytest.mark.asyncio
    async def test_analyze_query(self, mock_workflow, sample_rag_state):
        """测试查询分析"""
        result = await mock_workflow.analyze_query(sample_rag_state)
        
        assert "query_type" in result.metadata
        assert "needs_realtime" in result.metadata
        assert "complexity" in result.metadata
        assert result.metadata["query_type"] == "general"
    
    @pytest.mark.asyncio
    async def test_route_retrieval_general(self, mock_workflow):
        """测试一般查询的检索路由"""
        state = RAGState(
            query="What is AI?",
            metadata={"query_type": "general", "needs_realtime": False}
        )
        
        result = await mock_workflow.route_retrieval(state)
        assert result.metadata["retrieval_strategy"] == "both"
    
    @pytest.mark.asyncio
    async def test_route_retrieval_realtime(self, mock_workflow):
        """测试实时查询的检索路由"""
        state = RAGState(
            query="What's the weather today?",
            metadata={"query_type": "realtime", "needs_realtime": True}
        )
        
        result = await mock_workflow.route_retrieval(state)
        assert result.metadata["retrieval_strategy"] == "web_only"
    
    @pytest.mark.asyncio
    async def test_route_retrieval_knowledge_base(self, mock_workflow):
        """测试知识库查询的检索路由"""
        state = RAGState(
            query="查询知识库中的文档",
            metadata={"query_type": "knowledge", "needs_realtime": False}
        )
        
        result = await mock_workflow.route_retrieval(state)
        assert result.metadata["retrieval_strategy"] == "knowledge_only"
    
    def test_decide_retrieval_strategy(self, mock_workflow):
        """测试检索策略决策"""
        state = RAGState(
            query="test",
            metadata={"retrieval_strategy": "both"}
        )
        
        strategy = mock_workflow.decide_retrieval_strategy(state)
        assert strategy == "both"
        
        # 测试默认策略
        state_no_strategy = RAGState(query="test")
        default_strategy = mock_workflow.decide_retrieval_strategy(state_no_strategy)
        assert default_strategy == "both"
    
    @pytest.mark.asyncio
    async def test_retrieve_knowledge_success(self, mock_workflow):
        """测试成功的知识库检索"""
        mock_docs = [
            Document(page_content="Test content 1", metadata={"source": "doc1"}),
            Document(page_content="Test content 2", metadata={"source": "doc2"})
        ]
        
        mock_workflow.vector_store.asimilarity_search = AsyncMock(return_value=mock_docs)
        
        state = RAGState(query="test query")
        result = await mock_workflow.retrieve_knowledge(state)
        
        assert len(result.documents) == 2
        assert result.metadata["knowledge_retrieved"] == 2
        mock_workflow.vector_store.asimilarity_search.assert_called_once_with("test query", k=5)
    
    @pytest.mark.asyncio
    async def test_retrieve_knowledge_error(self, mock_workflow):
        """测试知识库检索错误"""
        mock_workflow.vector_store.asimilarity_search = AsyncMock(
            side_effect=Exception("Vector store error")
        )
        
        state = RAGState(query="test query")
        result = await mock_workflow.retrieve_knowledge(state)
        
        assert "knowledge_error" in result.metadata
        assert result.metadata["knowledge_error"] == "Vector store error"
    
    @pytest.mark.asyncio
    async def test_search_web(self, mock_workflow):
        """测试网络搜索"""
        state = RAGState(query="test query")
        result = await mock_workflow.search_web(state)
        
        assert len(result.web_results) > 0
        assert result.metadata["web_retrieved"] > 0
        assert result.web_results[0]["title"] == "示例搜索结果"
    
    @pytest.mark.asyncio
    async def test_fuse_information(self, mock_workflow):
        """测试信息融合"""
        documents = [Document(page_content="Doc content", metadata={"source": "doc.txt"})]
        web_results = [{"content": "Web content", "url": "http://example.com", "title": "Example"}]
        
        state = RAGState(
            query="test",
            documents=documents,
            web_results=web_results
        )
        
        result = await mock_workflow.fuse_information(state)
        
        assert result.metadata["total_sources"] == 2
        assert len(result.metadata["fused_sources"]) == 2
        
        sources = result.metadata["fused_sources"]
        assert sources[0]["source"] == "knowledge_base"
        assert sources[1]["source"] == "web_search"
    
    @pytest.mark.asyncio
    async def test_build_context(self, mock_workflow):
        """测试上下文构建"""
        fused_sources = [
            {"content": "Content 1", "source": "knowledge_base"},
            {"content": "Content 2", "source": "web_search"}
        ]
        
        state = RAGState(
            query="test",
            metadata={"fused_sources": fused_sources}
        )
        
        result = await mock_workflow.build_context(state)
        
        assert result.context != ""
        assert "Content 1" in result.context
        assert "Content 2" in result.context
        assert "来源1" in result.context
        assert "来源2" in result.context
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, mock_workflow):
        """测试成功生成回答"""
        mock_response = Mock()
        mock_response.content = "This is a test response"
        mock_workflow.chat_model.ainvoke = AsyncMock(return_value=mock_response)
        
        state = RAGState(
            query="test query",
            context="test context"
        )
        
        result = await mock_workflow.generate_response(state)
        
        assert result.response == "This is a test response"
        assert len(result.messages) == 2
        assert isinstance(result.messages[0], HumanMessage)
        assert isinstance(result.messages[1], AIMessage)
        mock_workflow.chat_model.ainvoke.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_response_error(self, mock_workflow):
        """测试生成回答错误"""
        mock_workflow.chat_model.ainvoke = AsyncMock(
            side_effect=Exception("Model error")
        )
        
        state = RAGState(
            query="test query",
            context="test context"
        )
        
        result = await mock_workflow.generate_response(state)
        
        assert "抱歉，生成回答时出现错误" in result.response
        assert "generation_error" in result.metadata
        assert result.metadata["generation_error"] == "Model error"
    
    @pytest.mark.asyncio
    async def test_run_workflow(self, mock_workflow):
        """测试完整工作流运行"""
        # 模拟工作流的ainvoke方法
        mock_final_state = RAGState(
            query="test query",
            response="Final response",
            metadata={"completed": True}
        )
        
        mock_workflow.workflow = AsyncMock()
        mock_workflow.workflow.ainvoke = AsyncMock(return_value=mock_final_state)
        
        result = await mock_workflow.run("test query")
        
        assert result.query == "test query"
        assert result.response == "Final response"
        assert result.metadata["completed"] is True
        mock_workflow.workflow.ainvoke.assert_called_once()


class TestRAGWorkflowIntegration:
    """RAG工作流集成测试"""
    
    @pytest.mark.asyncio
    async def test_workflow_state_flow(self, mock_workflow):
        """测试工作流状态流转"""
        initial_state = RAGState(query="What is machine learning?")
        
        # 测试查询分析
        analyzed_state = await mock_workflow.analyze_query(initial_state)
        assert "query_type" in analyzed_state.metadata
        
        # 测试检索路由
        routed_state = await mock_workflow.route_retrieval(analyzed_state)
        assert "retrieval_strategy" in routed_state.metadata
        
        # 测试信息融合
        fused_state = await mock_workflow.fuse_information(routed_state)
        assert "total_sources" in fused_state.metadata
        
        # 测试上下文构建
        context_state = await mock_workflow.build_context(fused_state)
        assert context_state.context is not None