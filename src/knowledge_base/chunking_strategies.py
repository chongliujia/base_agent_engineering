#!/usr/bin/env python3
"""
Document Chunking Strategy Module - Modular design supporting multiple chunking strategies
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
    """Base class for chunking strategies"""
    
    def __init__(self, **kwargs):
        self.config = kwargs
    
    @abstractmethod
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Abstract method for chunking documents"""
        pass
    
    @abstractmethod
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        pass
    
    def _add_chunk_metadata(self, chunks: List[Document], strategy_name: str) -> List[Document]:
        """Add strategy-related metadata to chunks"""
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
    """Recursive character chunking strategy - Most versatile strategy"""
    
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
            "description": "Recursive character chunking - Chunks by hierarchical separators",
            "parameters": {
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
                "separators": self.separators
            },
            "suitable_for": ["General documents", "Technical documents", "Novels", "Reports"],
            "advantages": ["Smart splitting", "Maintains semantic coherence", "Wide applicability"]
        }


class TokenChunkingStrategy(BaseChunkingStrategy):
    """Token-based chunking strategy - Suitable for LLM processing"""
    
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
            "description": "Token-based chunking - Precise chunking by token count",
            "parameters": {
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap
            },
            "suitable_for": ["LLM input", "API calls", "Cost-sensitive scenarios"],
            "advantages": ["Precise token control", "Predictable costs", "LLM-friendly"]
        }


class SemanticChunkingStrategy(BaseChunkingStrategy):
    """Semantic chunking strategy - Chunks based on semantic similarity"""
    
    def __init__(self, breakpoint_threshold_type: str = "percentile", 
                 threshold: Optional[float] = None, **kwargs):
        super().__init__(**kwargs)
        self.breakpoint_threshold_type = breakpoint_threshold_type
        self.threshold = threshold
        
        if not SEMANTIC_AVAILABLE:
            raise ImportError("SemanticChunker requires langchain-experimental package")
        
        # Get embedding model
        model_config = get_model_config()
        self.embedding_model = model_config.get_embedding_model()
        
        # Create semantic chunker
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
            "description": "Semantic chunking - Smart chunking based on semantic similarity",
            "parameters": {
                "breakpoint_threshold_type": self.breakpoint_threshold_type,
                "threshold": self.threshold
            },
            "suitable_for": ["Long documents", "Academic papers", "Technical specifications", "Knowledge base construction"],
            "advantages": ["Semantic coherence", "Smart breakpoints", "High-quality chunks"],
            "requirements": ["Requires embedding model", "Higher computational overhead"]
        }


class CharacterChunkingStrategy(BaseChunkingStrategy):
    """Simple character chunking strategy - Chunks by fixed character count"""
    
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
            "description": "Simple character chunking - Chunks by fixed character count and separator",
            "parameters": {
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
                "separator": self.separator
            },
            "suitable_for": ["Structured documents", "Code files", "Simple text"],
            "advantages": ["Fast processing", "Predictable results", "Low resource consumption"]
        }


class CodeChunkingStrategy(BaseChunkingStrategy):
    """Code document chunking strategy - Chunks by code structure"""
    
    def __init__(self, language: str = "python", chunk_size: int = 1500, 
                 chunk_overlap: int = 100, **kwargs):
        super().__init__(**kwargs)
        self.language = language
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Set separators based on language
        self.separators = self._get_language_separators(language)
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators
        )
    
    def _get_language_separators(self, language: str) -> List[str]:
        """Get appropriate separators based on programming language"""
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
            "description": f"Code chunking strategy - Optimized for {self.language} code structure",
            "parameters": {
                "language": self.language,
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
                "separators": self.separators
            },
            "suitable_for": [f"{self.language} code", "API documentation", "Technical specifications"],
            "advantages": ["Preserves code structure", "Function integrity", "Syntax awareness"]
        }


class DocumentFormatStrategy(BaseChunkingStrategy):
    """Document format-specific chunking strategy - Optimizes chunking based on document format"""
    
    def __init__(self, format_type: str = "pdf", **kwargs):
        super().__init__(**kwargs)
        self.format_type = format_type.lower()
        self.strategy = self._create_format_strategy()
    
    def _create_format_strategy(self) -> BaseChunkingStrategy:
        """Create appropriate chunking strategy based on document format"""
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
        # Update chunking strategy name
        for chunk in chunks:
            chunk.metadata["chunking_strategy"] = f"format_{self.format_type}"
        return chunks
    
    def get_strategy_info(self) -> Dict[str, Any]:
        base_info = self.strategy.get_strategy_info()
        base_info.update({
            "name": f"format_{self.format_type}",
            "description": f"Document format optimized chunking - Optimized for {self.format_type.upper()} format",
            "suitable_for": [f"{self.format_type.upper()} documents"],
            "advantages": ["Format-specific optimization", "Optimal parameter configuration", "High-quality chunks"]
        })
        return base_info


class ChunkingStrategyFactory:
    """Chunking strategy factory class - Manages all chunking strategies"""
    
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
        """Create chunking strategy instance"""
        if strategy_name not in cls._strategies:
            available = ", ".join(cls._strategies.keys())
            raise ValueError(f"Unknown chunking strategy: {strategy_name}. Available strategies: {available}")
        
        strategy_class = cls._strategies[strategy_name]
        return strategy_class(**kwargs)
    
    @classmethod
    def list_strategies(cls) -> Dict[str, Dict[str, Any]]:
        """List all available chunking strategies"""
        strategies_info = {}
        
        for name, strategy_class in cls._strategies.items():
            try:
                # Create default instance to get information
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
                    "description": f"Strategy creation failed: {str(e)}",
                    "available": False
                }
        
        return strategies_info
    
    @classmethod
    def register_strategy(cls, name: str, strategy_class: type):
        """Register new chunking strategy"""
        if not issubclass(strategy_class, BaseChunkingStrategy):
            raise ValueError("Strategy class must inherit from BaseChunkingStrategy")
        
        cls._strategies[name] = strategy_class
        print(f"✅ Successfully registered chunking strategy: {name}")
    
    @classmethod
    def get_recommended_strategy(cls, file_type: str = None, 
                                use_case: str = None) -> str:
        """Recommend best strategy based on file type and use case"""
        recommendations = {
            # File type recommendations
            "pdf": "format",
            "docx": "format", 
            "txt": "recursive",
            "md": "format",
            "pptx": "format",
            "py": "code",
            "js": "code",
            "java": "code",
            "cpp": "code",
            
            # Use case recommendations
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


# Export main interfaces
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