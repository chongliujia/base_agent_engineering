#!/usr/bin/env python3
"""
文档分块策略模块 - 模块化设计，支持多种分块策略
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from langchain_core.documents import Document
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    TokenTextSplitter,
    CharacterTextSplitter,
    SpacyTextSplitter,
    NLTKTextSplitter
)

try:
    from langchain_experimental.text_splitter import SemanticChunker
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False

from config.settings import get_model_config


class BaseChunkingStrategy(ABC):
    """分块策略基类"""
    
    def __init__(self, **kwargs):
        self.config = kwargs
    
    @abstractmethod
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """分块文档的抽象方法"""
        pass
    
    @abstractmethod
    def get_strategy_info(self) -> Dict[str, Any]:
        """获取策略信息"""
        pass
    
    def _add_chunk_metadata(self, chunks: List[Document], strategy_name: str) -> List[Document]:
        """为分块添加策略相关的元数据"""
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "chunk_id": i,
                "chunk_size": len(chunk.page_content),
                "chunking_strategy": strategy_name,
                "chunk_index": i,
                "total_chunks": len(chunks)
            })
        return chunks


class RecursiveChunkingStrategy(BaseChunkingStrategy):
    """递归字符分块策略 - 最通用的策略"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, 
                 separators: Optional[List[str]] = None, **kwargs):
        super().__init__(**kwargs)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", " ", ""]
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators
        )
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        chunks = self.splitter.split_documents(documents)
        return self._add_chunk_metadata(chunks, "recursive")
    
    def get_strategy_info(self) -> Dict[str, Any]:
        return {
            "name": "recursive",
            "description": "递归字符分块 - 按层次分隔符分块",
            "parameters": {
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
                "separators": self.separators
            },
            "suitable_for": ["通用文档", "技术文档", "小说", "报告"],
            "advantages": ["智能分割", "保持语义连贯", "适用性广"]
        }


class TokenChunkingStrategy(BaseChunkingStrategy):
    """基于Token的分块策略 - 适合LLM处理"""
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50, **kwargs):
        super().__init__(**kwargs)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = TokenTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        chunks = self.splitter.split_documents(documents)
        return self._add_chunk_metadata(chunks, "token")
    
    def get_strategy_info(self) -> Dict[str, Any]:
        return {
            "name": "token",
            "description": "基于Token分块 - 按Token数量精确分块",
            "parameters": {
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap
            },
            "suitable_for": ["LLM输入", "API调用", "成本敏感场景"],
            "advantages": ["Token精确控制", "成本可预测", "LLM友好"]
        }


class SemanticChunkingStrategy(BaseChunkingStrategy):
    """语义分块策略 - 基于语义相似度分块"""
    
    def __init__(self, breakpoint_threshold_type: str = "percentile", 
                 threshold: Optional[float] = None, **kwargs):
        super().__init__(**kwargs)
        self.breakpoint_threshold_type = breakpoint_threshold_type
        self.threshold = threshold
        
        if not SEMANTIC_AVAILABLE:
            raise ImportError("SemanticChunker需要安装langchain-experimental包")
        
        # 获取嵌入模型
        model_config = get_model_config()
        self.embedding_model = model_config.get_embedding_model()
        
        # 创建语义分块器
        params = {
            "embeddings": self.embedding_model,
            "breakpoint_threshold_type": self.breakpoint_threshold_type
        }
        if self.threshold:
            params["breakpoint_threshold_amount"] = self.threshold
            
        self.splitter = SemanticChunker(**params)
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        chunks = self.splitter.split_documents(documents)
        return self._add_chunk_metadata(chunks, "semantic")
    
    def get_strategy_info(self) -> Dict[str, Any]:
        return {
            "name": "semantic",
            "description": "语义分块 - 基于语义相似度智能分块",
            "parameters": {
                "breakpoint_threshold_type": self.breakpoint_threshold_type,
                "threshold": self.threshold
            },
            "suitable_for": ["长文档", "学术论文", "技术规范", "知识库构建"],
            "advantages": ["语义连贯", "智能断点", "高质量分块"],
            "requirements": ["需要嵌入模型", "计算开销较大"]
        }


class CharacterChunkingStrategy(BaseChunkingStrategy):
    """简单字符分块策略 - 按固定字符数分块"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, 
                 separator: str = "\n\n", **kwargs):
        super().__init__(**kwargs)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator
        self.splitter = CharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separator=self.separator
        )
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        chunks = self.splitter.split_documents(documents)
        return self._add_chunk_metadata(chunks, "character")
    
    def get_strategy_info(self) -> Dict[str, Any]:
        return {
            "name": "character",
            "description": "简单字符分块 - 按固定字符数和分隔符分块",
            "parameters": {
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
                "separator": self.separator
            },
            "suitable_for": ["结构化文档", "代码文件", "简单文本"],
            "advantages": ["处理速度快", "结果可预测", "资源消耗少"]
        }


class CodeChunkingStrategy(BaseChunkingStrategy):
    """代码文档分块策略 - 按代码结构分块"""
    
    def __init__(self, language: str = "python", chunk_size: int = 1500, 
                 chunk_overlap: int = 100, **kwargs):
        super().__init__(**kwargs)
        self.language = language
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 根据语言设置分隔符
        self.separators = self._get_language_separators(language)
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators
        )
    
    def _get_language_separators(self, language: str) -> List[str]:
        """根据编程语言获取合适的分隔符"""
        separators_map = {
            "python": ["\nclass ", "\ndef ", "\n\ndef ", "\n\n", "\n", " ", ""],
            "javascript": ["\nfunction ", "\nconst ", "\nlet ", "\nvar ", "\n\n", "\n", " ", ""],
            "java": ["\npublic class ", "\nprivate class ", "\nprotected class ", 
                    "\npublic ", "\nprivate ", "\nprotected ", "\n\n", "\n", " ", ""],
            "cpp": ["\nclass ", "\nstruct ", "\nvoid ", "\nint ", "\n\n", "\n", " ", ""],
            "markdown": ["\n# ", "\n## ", "\n### ", "\n\n", "\n", " ", ""],
            "default": ["\n\n", "\n", " ", ""]
        }
        return separators_map.get(language.lower(), separators_map["default"])
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        chunks = self.splitter.split_documents(documents)
        return self._add_chunk_metadata(chunks, f"code_{self.language}")
    
    def get_strategy_info(self) -> Dict[str, Any]:
        return {
            "name": f"code_{self.language}",
            "description": f"代码分块策略 - 针对{self.language}代码结构优化",
            "parameters": {
                "language": self.language,
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
                "separators": self.separators
            },
            "suitable_for": [f"{self.language}代码", "API文档", "技术规范"],
            "advantages": ["保持代码结构", "函数完整性", "语法感知"]
        }


class DocumentFormatStrategy(BaseChunkingStrategy):
    """文档格式特定分块策略 - 根据文档格式优化分块"""
    
    def __init__(self, format_type: str = "pdf", **kwargs):
        super().__init__(**kwargs)
        self.format_type = format_type.lower()
        self.strategy = self._create_format_strategy()
    
    def _create_format_strategy(self) -> BaseChunkingStrategy:
        """根据文档格式创建相应的分块策略"""
        format_configs = {
            "pdf": {
                "chunk_size": 1200,
                "chunk_overlap": 150,
                "separators": ["\n\n", "\n", ". ", " ", ""]
            },
            "docx": {
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "separators": ["\n\n", "\n", ". ", " ", ""]
            },
            "txt": {
                "chunk_size": 800,
                "chunk_overlap": 100,
                "separators": ["\n\n", "\n", ". ", " ", ""]
            },
            "md": {
                "chunk_size": 1000,
                "chunk_overlap": 150,
                "separators": ["\n# ", "\n## ", "\n### ", "\n\n", "\n", " ", ""]
            },
            "pptx": {
                "chunk_size": 600,
                "chunk_overlap": 100,
                "separators": ["\n\n", "\n", " ", ""]
            }
        }
        
        config = format_configs.get(self.format_type, format_configs["txt"])
        return RecursiveChunkingStrategy(**config)
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        chunks = self.strategy.chunk_documents(documents)
        # 更新分块策略名称
        for chunk in chunks:
            chunk.metadata["chunking_strategy"] = f"format_{self.format_type}"
        return chunks
    
    def get_strategy_info(self) -> Dict[str, Any]:
        base_info = self.strategy.get_strategy_info()
        base_info.update({
            "name": f"format_{self.format_type}",
            "description": f"文档格式优化分块 - 针对{self.format_type.upper()}格式优化",
            "suitable_for": [f"{self.format_type.upper()}文档"],
            "advantages": ["格式特定优化", "最佳参数配置", "高质量分块"]
        })
        return base_info


class ChunkingStrategyFactory:
    """分块策略工厂类 - 管理所有分块策略"""
    
    _strategies = {
        "recursive": RecursiveChunkingStrategy,
        "token": TokenChunkingStrategy,
        "character": CharacterChunkingStrategy,
        "code": CodeChunkingStrategy,
        "format": DocumentFormatStrategy
    }
    
    if SEMANTIC_AVAILABLE:
        _strategies["semantic"] = SemanticChunkingStrategy
    
    @classmethod
    def create_strategy(cls, strategy_name: str, **kwargs) -> BaseChunkingStrategy:
        """创建分块策略实例"""
        if strategy_name not in cls._strategies:
            available = ", ".join(cls._strategies.keys())
            raise ValueError(f"未知的分块策略: {strategy_name}。可用策略: {available}")
        
        strategy_class = cls._strategies[strategy_name]
        return strategy_class(**kwargs)
    
    @classmethod
    def list_strategies(cls) -> Dict[str, Dict[str, Any]]:
        """列出所有可用的分块策略"""
        strategies_info = {}
        
        for name, strategy_class in cls._strategies.items():
            try:
                # 创建默认实例来获取信息
                if name == "code":
                    strategy = strategy_class(language="python")
                elif name == "format":
                    strategy = strategy_class(format_type="pdf")
                else:
                    strategy = strategy_class()
                
                strategies_info[name] = strategy.get_strategy_info()
            except Exception as e:
                strategies_info[name] = {
                    "name": name,
                    "description": f"策略创建失败: {str(e)}",
                    "available": False
                }
        
        return strategies_info
    
    @classmethod
    def register_strategy(cls, name: str, strategy_class: type):
        """注册新的分块策略"""
        if not issubclass(strategy_class, BaseChunkingStrategy):
            raise ValueError("策略类必须继承自BaseChunkingStrategy")
        
        cls._strategies[name] = strategy_class
        print(f"✅ 成功注册分块策略: {name}")
    
    @classmethod
    def get_recommended_strategy(cls, file_type: str = None, 
                                use_case: str = None) -> str:
        """根据文件类型和使用场景推荐最佳策略"""
        recommendations = {
            # 文件类型推荐
            "pdf": "format",
            "docx": "format", 
            "txt": "recursive",
            "md": "format",
            "pptx": "format",
            "py": "code",
            "js": "code",
            "java": "code",
            "cpp": "code",
            
            # 使用场景推荐
            "general": "recursive",
            "llm_input": "token", 
            "knowledge_base": "semantic" if SEMANTIC_AVAILABLE else "recursive",
            "code_analysis": "code",
            "fast_processing": "character"
        }
        
        if file_type:
            return recommendations.get(file_type.lower(), "recursive")
        elif use_case:
            return recommendations.get(use_case.lower(), "recursive")
        else:
            return "recursive"


# 导出主要接口
__all__ = [
    "BaseChunkingStrategy",
    "RecursiveChunkingStrategy", 
    "TokenChunkingStrategy",
    "SemanticChunkingStrategy",
    "CharacterChunkingStrategy",
    "CodeChunkingStrategy",
    "DocumentFormatStrategy",
    "ChunkingStrategyFactory"
]