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

from config.settings import get_model_config, get_settings


class DocumentProcessor:
    """文档处理器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.model_config = get_model_config()
        self.supported_extensions = {
            '.pdf': PyPDFLoader,
            '.txt': TextLoader,
            '.md': UnstructuredMarkdownLoader,
            '.docx': Docx2txtLoader,
            '.pptx': UnstructuredPowerPointLoader
        }
        
        # 初始化文本分割器
        splitter_config = self.model_config.get_text_splitter_config()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=splitter_config["parameters"]["chunk_size"],
            chunk_overlap=splitter_config["parameters"]["chunk_overlap"],
            separators=splitter_config["parameters"]["separators"]
        )
    
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
        """分割文档为小块"""
        try:
            split_docs = self.text_splitter.split_documents(documents)
            
            # 为每个分块添加额外的元数据
            for i, doc in enumerate(split_docs):
                doc.metadata.update({
                    "chunk_id": i,
                    "chunk_size": len(doc.page_content),
                    "split_time": datetime.now().isoformat()
                })
            
            return split_docs
            
        except Exception as e:
            raise RuntimeError(f"文档分割失败: {str(e)}")
    
    def process_file(self, file_path: Union[str, Path]) -> List[Document]:
        """处理单个文件：加载 + 分割"""
        documents = self.load_document(file_path)
        split_documents = self.split_documents(documents)
        return split_documents
    
    def process_directory(self, directory_path: Union[str, Path], 
                         recursive: bool = True) -> List[Document]:
        """处理目录中的所有支持文件"""
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            raise FileNotFoundError(f"目录不存在: {directory_path}")
        
        if not directory_path.is_dir():
            raise ValueError(f"路径不是目录: {directory_path}")
        
        all_documents = []
        processed_files = []
        failed_files = []
        
        # 获取文件列表
        if recursive:
            file_pattern = "**/*"
        else:
            file_pattern = "*"
        
        for file_path in directory_path.glob(file_pattern):
            if file_path.is_file() and self.is_supported_file(file_path):
                try:
                    documents = self.process_file(file_path)
                    all_documents.extend(documents)
                    processed_files.append(str(file_path))
                    print(f"✅ 处理成功: {file_path.name} ({len(documents)} 个分块)")
                    
                except Exception as e:
                    failed_files.append((str(file_path), str(e)))
                    print(f"❌ 处理失败: {file_path.name} - {str(e)}")
        
        print(f"\n📊 处理统计:")
        print(f"  成功处理: {len(processed_files)} 个文件")
        print(f"  失败文件: {len(failed_files)} 个文件")
        print(f"  总分块数: {len(all_documents)} 个")
        
        return all_documents
    
    def extract_metadata_summary(self, documents: List[Document]) -> Dict[str, Any]:
        """提取文档集合的元数据摘要"""
        if not documents:
            return {}
        
        file_types = {}
        total_size = 0
        total_chunks = len(documents)
        sources = set()
        
        for doc in documents:
            metadata = doc.metadata
            
            # 统计文件类型
            file_type = metadata.get("file_type", "unknown")
            file_types[file_type] = file_types.get(file_type, 0) + 1
            
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
            "sources": list(sources)
        }


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


# 创建全局文档处理器实例
document_processor = DocumentProcessor()