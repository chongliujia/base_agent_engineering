"""
Document Processor - Supports loading, splitting and preprocessing of multiple document formats
"""

import os
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
    UnstructuredMarkdownLoader,
    UnstructuredPowerPointLoader
)
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    TokenTextSplitter
)

from .chunking_strategies import ChunkingStrategyFactory, BaseChunkingStrategy

from config.settings import get_model_config, get_settings


class DocumentProcessor:
    """Document Processor - Supports multiple chunking strategies"""
    
    def __init__(self, chunking_strategy: str = "recursive", strategy_params: Dict[str, Any] = None):
        self.settings = get_settings()
        self.model_config = get_model_config()
        self.supported_extensions = {
            '.pdf': PyPDFLoader,
            '.txt': TextLoader,
            '.md': UnstructuredMarkdownLoader,
            '.docx': Docx2txtLoader,
            '.pptx': UnstructuredPowerPointLoader,
            # Code file support
            '.py': TextLoader,
            '.js': TextLoader,
            '.ts': TextLoader,
            '.java': TextLoader,
            '.cpp': TextLoader,
            '.c': TextLoader,
            '.h': TextLoader,
            '.hpp': TextLoader,
            '.go': TextLoader,
            '.rs': TextLoader,
            '.php': TextLoader,
            '.rb': TextLoader,
            '.swift': TextLoader,
            '.kotlin': TextLoader,
            '.scala': TextLoader,
            '.r': TextLoader,
            '.sql': TextLoader,
            '.sh': TextLoader,
            '.bat': TextLoader,
            '.ps1': TextLoader,
            # Configuration and data files
            '.json': TextLoader,
            '.xml': TextLoader,
            '.yaml': TextLoader,
            '.yml': TextLoader,
            '.toml': TextLoader,
            '.ini': TextLoader,
            '.cfg': TextLoader,
            '.conf': TextLoader,
            '.csv': TextLoader,
            # Markup and documentation files
            '.rst': TextLoader,
            '.html': TextLoader,
            '.htm': TextLoader,
            '.css': TextLoader,
            '.scss': TextLoader,
            '.sass': TextLoader,
            '.less': TextLoader,
            # Other text files
            '.log': TextLoader,
            '.readme': TextLoader,
            '.license': TextLoader,
            '.gitignore': TextLoader,
            '.env': TextLoader
        }
        
        # Initialize chunking strategy
        self.chunking_strategy_name = chunking_strategy
        self.strategy_params = strategy_params or {}
        
        # Create chunking strategy instance
        try:
            self.chunking_strategy = ChunkingStrategyFactory.create_strategy(
                chunking_strategy, **self.strategy_params
            )
        except Exception as e:
            print(f"Failed to create chunking strategy, using default strategy: {e}")
            # Use default recursive chunking strategy as fallback
            splitter_config = self.model_config.get_text_splitter_config()
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=splitter_config["parameters"]["chunk_size"],
                chunk_overlap=splitter_config["parameters"]["chunk_overlap"],
                separators=splitter_config["parameters"]["separators"]
            )
            self.chunking_strategy = None
    
    def get_file_hash(self, file_path: Union[str, Path]) -> str:
        """Calculate file hash for detecting file changes"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def is_supported_file(self, file_path: Union[str, Path]) -> bool:
        """Check if file is supported"""
        file_path = Path(file_path)
        return file_path.suffix.lower() in self.supported_extensions
    
    def load_document(self, file_path: Union[str, Path]) -> List[Document]:
        """Load a single document"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File does not exist: {file_path}")
        
        if not self.is_supported_file(file_path):
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        # Get corresponding loader
        loader_class = self.supported_extensions[file_path.suffix.lower()]
        loader = loader_class(str(file_path))
        
        try:
            documents = loader.load()
            
            # Add metadata
            file_hash = self.get_file_hash(file_path)
            file_stats = file_path.stat()
            
            for doc in documents:
                doc.metadata.update({
                    "source": str(file_path),
                    "filename": file_path.name,
                    "file_type": file_path.suffix.lower(),
                    "file_size": file_stats.st_size,
                    "file_hash": file_hash,
                    "created_time": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                    "modified_time": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                    "processed_time": datetime.now().isoformat()
                })
            
            return documents
            
        except Exception as e:
            raise RuntimeError(f"Failed to load document {file_path}: {str(e)}")
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents using configured chunking strategy"""
        try:
            if self.chunking_strategy:
                # Use modern chunking strategy
                split_docs = self.chunking_strategy.chunk_documents(documents)
                
                # Add strategy information to metadata
                strategy_info = self.chunking_strategy.get_strategy_info()
                for doc in split_docs:
                    doc.metadata.update({
                        "split_time": datetime.now().isoformat(),
                        "strategy_name": strategy_info.get("name", "unknown"),
                        "strategy_description": strategy_info.get("description", "")
                    })
                
                return split_docs
            else:
                # Use traditional text splitter as fallback
                split_docs = self.text_splitter.split_documents(documents)
                
                # Add additional metadata for each chunk
                for i, doc in enumerate(split_docs):
                    doc.metadata.update({
                        "chunk_id": i,
                        "chunk_size": len(doc.page_content),
                        "split_time": datetime.now().isoformat(),
                        "strategy_name": "legacy_recursive",
                        "strategy_description": "Legacy recursive chunking strategy"
                    })
                
                return split_docs
            
        except Exception as e:
            raise RuntimeError(f"Document splitting failed: {str(e)}")
    
    def process_file(self, file_path: Union[str, Path], chunking_strategy: str = None, strategy_params: Dict[str, Any] = None) -> List[Document]:
        """Process a single file: load + split (supports temporary chunking strategy specification)"""
        documents = self.load_document(file_path)
        
        # If temporary strategy is specified, create temporary processor
        if chunking_strategy and chunking_strategy != self.chunking_strategy_name:
            temp_processor = DocumentProcessor(chunking_strategy, strategy_params or {})
            split_documents = temp_processor.split_documents(documents)
        else:
            split_documents = self.split_documents(documents)
        
        return split_documents
    
    def process_directory(self, directory_path: Union[str, Path], 
                         recursive: bool = True, 
                         auto_strategy: bool = True,
                         chunking_strategy: str = None,
                         strategy_params: Dict[str, Any] = None) -> List[Document]:
        """Process all supported files in directory (supports automatic strategy selection and format-specific processing)"""
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory does not exist: {directory_path}")
        
        if not directory_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory_path}")
        
        all_documents = []
        processed_files = []
        failed_files = []
        strategy_usage = {}
        
        # Get file list
        if recursive:
            file_pattern = "**/*"
        else:
            file_pattern = "*"
        
        for file_path in directory_path.glob(file_pattern):
            if file_path.is_file() and self.is_supported_file(file_path):
                try:
                    # Determine chunking strategy to use
                    file_strategy = chunking_strategy
                    file_strategy_params = strategy_params or {}
                    
                    if auto_strategy and not chunking_strategy:
                        # Automatically select best strategy based on file type
                        file_ext = file_path.suffix.lower().lstrip('.')
                        file_strategy = ChunkingStrategyFactory.get_recommended_strategy(
                            file_type=file_ext
                        )
                        
                        # Set parameters for format-specific strategies
                        if file_strategy == "format":
                            file_strategy_params = {"format_type": file_ext}
                        elif file_strategy == "code" and file_ext in ["py", "js", "java", "cpp"]:
                            file_strategy_params = {"language": file_ext}
                    
                    # Track strategy usage
                    strategy_usage[file_strategy] = strategy_usage.get(file_strategy, 0) + 1
                    
                    # Process file
                    documents = self.process_file(file_path, file_strategy, file_strategy_params)
                    all_documents.extend(documents)
                    processed_files.append(str(file_path))
                    
                    # Display processing result with strategy information
                    strategy_display = file_strategy
                    if file_strategy == "format" and "format_type" in file_strategy_params:
                        strategy_display += f"({file_strategy_params['format_type']})"
                    elif file_strategy == "code" and "language" in file_strategy_params:
                        strategy_display += f"({file_strategy_params['language']})"
                    
                    print(f"Processing successful: {file_path.name} ({len(documents)} chunks) [Strategy: {strategy_display}]")
                    
                except Exception as e:
                    failed_files.append((str(file_path), str(e)))
                    print(f"Processing failed: {file_path.name} - {str(e)}")
        
        print(f"\nProcessing Statistics:")
        print(f"  Successfully processed: {len(processed_files)} files")
        print(f"  Failed files: {len(failed_files)} files")
        print(f"  Total chunks: {len(all_documents)} chunks")
        
        if strategy_usage:
            print(f"\nChunking Strategy Usage Statistics:")
            for strategy, count in sorted(strategy_usage.items()):
                print(f"  {strategy}: {count} files")
        
        return all_documents
    
    def extract_metadata_summary(self, documents: List[Document]) -> Dict[str, Any]:
        """Extract metadata summary from document collection (includes chunking strategy statistics)"""
        if not documents:
            return {}
        
        file_types = {}
        chunking_strategies = {}
        total_size = 0
        total_chunks = len(documents)
        sources = set()
        
        for doc in documents:
            metadata = doc.metadata
            
            # Count file types
            file_type = metadata.get("file_type", "unknown")
            file_types[file_type] = file_types.get(file_type, 0) + 1
            
            # Count chunking strategies
            strategy_name = metadata.get("strategy_name", "unknown")
            chunking_strategies[strategy_name] = chunking_strategies.get(strategy_name, 0) + 1
            
            # Accumulate file size
            total_size += metadata.get("file_size", 0)
            
            # Collect source files
            source = metadata.get("source")
            if source:
                sources.add(source)
        
        return {
            "total_documents": len(sources),
            "total_chunks": total_chunks,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_types": file_types,
            "chunking_strategies": chunking_strategies,
            "sources": list(sources)
        }
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get current chunking strategy information"""
        if self.chunking_strategy:
            return self.chunking_strategy.get_strategy_info()
        else:
            return {
                "name": "legacy_recursive",
                "description": "Legacy recursive character chunking strategy",
                "parameters": {
                    "chunk_size": getattr(self.text_splitter, 'chunk_size', 'unknown'),
                    "chunk_overlap": getattr(self.text_splitter, 'chunk_overlap', 'unknown')
                }
            }
    
    @staticmethod
    def list_available_strategies() -> Dict[str, Dict[str, Any]]:
        """List all available chunking strategies"""
        return ChunkingStrategyFactory.list_strategies()
    
    @staticmethod
    def get_strategy_recommendation(file_type: str = None, use_case: str = None) -> str:
        """Get strategy recommendation"""
        return ChunkingStrategyFactory.get_recommended_strategy(file_type=file_type, use_case=use_case)


class DocumentValidator:
    """Document Validator"""
    
    @staticmethod
    def validate_document_content(document: Document) -> bool:
        """Validate if document content is valid"""
        if not document.page_content or not document.page_content.strip():
            return False
        
        # Check content length
        if len(document.page_content.strip()) < 10:
            return False
        
        return True
    
    @staticmethod
    def validate_documents(documents: List[Document]) -> List[Document]:
        """Validate and filter valid documents"""
        valid_documents = []
        
        for doc in documents:
            if DocumentValidator.validate_document_content(doc):
                valid_documents.append(doc)
            else:
                print(f"Skipping invalid document chunk: {doc.metadata.get('source', 'unknown')}")
        
        return valid_documents


# Create global document processor instance (using default recursive strategy)
document_processor = DocumentProcessor()