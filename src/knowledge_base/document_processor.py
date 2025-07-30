"""
文档处理器 - 支持多种文档格式的加载、分割和预处理
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
    """文档处理器 - 支持多种分块策略"""
    
    def __init__(self, chunking_strategy: str = "recursive", strategy_params: Dict[str, Any] = None):
        self.settings = get_settings()
        self.model_config = get_model_config()
        self.supported_extensions = {
            '.pdf': PyPDFLoader,
            '.txt': TextLoader,
            '.md': UnstructuredMarkdownLoader,
            '.docx': Docx2txtLoader,
            '.pptx': UnstructuredPowerPointLoader,
            # 代码文件支持
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
            # 配置和数据文件
            '.json': TextLoader,
            '.xml': TextLoader,
            '.yaml': TextLoader,
            '.yml': TextLoader,
            '.toml': TextLoader,
            '.ini': TextLoader,
            '.cfg': TextLoader,
            '.conf': TextLoader,
            '.csv': TextLoader,
            # 标记和文档文件
            '.rst': TextLoader,
            '.html': TextLoader,
            '.htm': TextLoader,
            '.css': TextLoader,
            '.scss': TextLoader,
            '.sass': TextLoader,
            '.less': TextLoader,
            # 其他文本文件
            '.log': TextLoader,
            '.readme': TextLoader,
            '.license': TextLoader,
            '.gitignore': TextLoader,
            '.env': TextLoader
        }
        
        # 初始化分块策略
        self.chunking_strategy_name = chunking_strategy
        self.strategy_params = strategy_params or {}
        
        # 创建分块策略实例
        try:
            self.chunking_strategy = ChunkingStrategyFactory.create_strategy(
                chunking_strategy, **self.strategy_params
            )
        except Exception as e:
            print(f"⚠️ 分块策略创建失败，使用默认策略: {e}")
            # 使用默认递归分块策略作为备用
            splitter_config = self.model_config.get_text_splitter_config()
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=splitter_config["parameters"]["chunk_size"],
                chunk_overlap=splitter_config["parameters"]["chunk_overlap"],
                separators=splitter_config["parameters"]["separators"]
            )
            self.chunking_strategy = None
    
    def get_file_hash(self, file_path: Union[str, Path]) -> str:
        """计算文件哈希值，用于检测文件变化"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def is_supported_file(self, file_path: Union[str, Path]) -> bool:
        """检查文件是否支持"""
        file_path = Path(file_path)
        return file_path.suffix.lower() in self.supported_extensions
    
    def load_document(self, file_path: Union[str, Path]) -> List[Document]:
        """加载单个文档"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        if not self.is_supported_file(file_path):
            raise ValueError(f"不支持的文件格式: {file_path.suffix}")
        
        # 获取对应的加载器
        loader_class = self.supported_extensions[file_path.suffix.lower()]
        loader = loader_class(str(file_path))
        
        try:
            documents = loader.load()
            
            # 添加元数据
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
            raise RuntimeError(f"加载文档失败 {file_path}: {str(e)}")
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """使用配置的分块策略分割文档"""
        try:
            if self.chunking_strategy:
                # 使用现代化的分块策略
                split_docs = self.chunking_strategy.chunk_documents(documents)
                
                # 添加策略信息到元数据
                strategy_info = self.chunking_strategy.get_strategy_info()
                for doc in split_docs:
                    doc.metadata.update({
                        "split_time": datetime.now().isoformat(),
                        "strategy_name": strategy_info.get("name", "unknown"),
                        "strategy_description": strategy_info.get("description", "")
                    })
                
                return split_docs
            else:
                # 使用传统的文本分割器作为备用
                split_docs = self.text_splitter.split_documents(documents)
                
                # 为每个分块添加额外的元数据
                for i, doc in enumerate(split_docs):
                    doc.metadata.update({
                        "chunk_id": i,
                        "chunk_size": len(doc.page_content),
                        "split_time": datetime.now().isoformat(),
                        "strategy_name": "legacy_recursive",
                        "strategy_description": "传统递归分块策略"
                    })
                
                return split_docs
            
        except Exception as e:
            raise RuntimeError(f"文档分割失败: {str(e)}")
    
    def process_file(self, file_path: Union[str, Path], chunking_strategy: str = None, strategy_params: Dict[str, Any] = None) -> List[Document]:
        """处理单个文件：加载 + 分割（支持临时指定分块策略）"""
        documents = self.load_document(file_path)
        
        # 如果指定了临时策略，创建临时处理器
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
        """处理目录中的所有支持文件（支持自动策略选择和格式特定处理）"""
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            raise FileNotFoundError(f"目录不存在: {directory_path}")
        
        if not directory_path.is_dir():
            raise ValueError(f"路径不是目录: {directory_path}")
        
        all_documents = []
        processed_files = []
        failed_files = []
        strategy_usage = {}
        
        # 获取文件列表
        if recursive:
            file_pattern = "**/*"
        else:
            file_pattern = "*"
        
        for file_path in directory_path.glob(file_pattern):
            if file_path.is_file() and self.is_supported_file(file_path):
                try:
                    # 确定使用的分块策略
                    file_strategy = chunking_strategy
                    file_strategy_params = strategy_params or {}
                    
                    if auto_strategy and not chunking_strategy:
                        # 根据文件类型自动选择最佳策略
                        file_ext = file_path.suffix.lower().lstrip('.')
                        file_strategy = ChunkingStrategyFactory.get_recommended_strategy(
                            file_type=file_ext
                        )
                        
                        # 为格式特定策略设置参数
                        if file_strategy == "format":
                            file_strategy_params = {"format_type": file_ext}
                        elif file_strategy == "code" and file_ext in ["py", "js", "java", "cpp"]:
                            file_strategy_params = {"language": file_ext}
                    
                    # 统计策略使用情况
                    strategy_usage[file_strategy] = strategy_usage.get(file_strategy, 0) + 1
                    
                    # 处理文件
                    documents = self.process_file(file_path, file_strategy, file_strategy_params)
                    all_documents.extend(documents)
                    processed_files.append(str(file_path))
                    
                    # 显示处理结果，包含策略信息
                    strategy_display = file_strategy
                    if file_strategy == "format" and "format_type" in file_strategy_params:
                        strategy_display += f"({file_strategy_params['format_type']})"
                    elif file_strategy == "code" and "language" in file_strategy_params:
                        strategy_display += f"({file_strategy_params['language']})"
                    
                    print(f"✅ 处理成功: {file_path.name} ({len(documents)} 个分块) [策略: {strategy_display}]")
                    
                except Exception as e:
                    failed_files.append((str(file_path), str(e)))
                    print(f"❌ 处理失败: {file_path.name} - {str(e)}")
        
        print(f"\n📊 处理统计:")
        print(f"  成功处理: {len(processed_files)} 个文件")
        print(f"  失败文件: {len(failed_files)} 个文件")
        print(f"  总分块数: {len(all_documents)} 个")
        
        if strategy_usage:
            print(f"\n🧠 分块策略使用统计:")
            for strategy, count in sorted(strategy_usage.items()):
                print(f"  {strategy}: {count} 个文件")
        
        return all_documents
    
    def extract_metadata_summary(self, documents: List[Document]) -> Dict[str, Any]:
        """提取文档集合的元数据摘要（包含分块策略统计）"""
        if not documents:
            return {}
        
        file_types = {}
        chunking_strategies = {}
        total_size = 0
        total_chunks = len(documents)
        sources = set()
        
        for doc in documents:
            metadata = doc.metadata
            
            # 统计文件类型
            file_type = metadata.get("file_type", "unknown")
            file_types[file_type] = file_types.get(file_type, 0) + 1
            
            # 统计分块策略
            strategy_name = metadata.get("strategy_name", "unknown")
            chunking_strategies[strategy_name] = chunking_strategies.get(strategy_name, 0) + 1
            
            # 累计文件大小
            total_size += metadata.get("file_size", 0)
            
            # 收集源文件
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
        """获取当前分块策略信息"""
        if self.chunking_strategy:
            return self.chunking_strategy.get_strategy_info()
        else:
            return {
                "name": "legacy_recursive",
                "description": "传统递归字符分块策略",
                "parameters": {
                    "chunk_size": getattr(self.text_splitter, 'chunk_size', 'unknown'),
                    "chunk_overlap": getattr(self.text_splitter, 'chunk_overlap', 'unknown')
                }
            }
    
    @staticmethod
    def list_available_strategies() -> Dict[str, Dict[str, Any]]:
        """列出所有可用的分块策略"""
        return ChunkingStrategyFactory.list_strategies()
    
    @staticmethod
    def get_strategy_recommendation(file_type: str = None, use_case: str = None) -> str:
        """获取策略推荐"""
        return ChunkingStrategyFactory.get_recommended_strategy(file_type=file_type, use_case=use_case)


class DocumentValidator:
    """文档验证器"""
    
    @staticmethod
    def validate_document_content(document: Document) -> bool:
        """验证文档内容是否有效"""
        if not document.page_content or not document.page_content.strip():
            return False
        
        # 检查内容长度
        if len(document.page_content.strip()) < 10:
            return False
        
        return True
    
    @staticmethod
    def validate_documents(documents: List[Document]) -> List[Document]:
        """验证并过滤有效文档"""
        valid_documents = []
        
        for doc in documents:
            if DocumentValidator.validate_document_content(doc):
                valid_documents.append(doc)
            else:
                print(f"⚠️  跳过无效文档块: {doc.metadata.get('source', 'unknown')}")
        
        return valid_documents


# 创建全局文档处理器实例（使用默认递归策略）
document_processor = DocumentProcessor()