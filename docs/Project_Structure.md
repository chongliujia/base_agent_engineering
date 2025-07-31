# RAG System Project Structure

This document provides a detailed description of the RAG system project's actual directory structure and module functionality. The project implements multi-knowledge base management, intelligent chunking strategies, and asynchronous processing architecture.

## 🏢 Actual Project Structure

```
base_agent_engineering/
├── 📁 app/                          # FastAPI application main directory
│   ├── 📁 api/                      # API routing modules
│   │   └── knowledge_base.py        # Knowledge base API endpoints
│   └── main.py                      # FastAPI application entry point
├── 📁 config/                       # Configuration management
│   ├── settings.py                  # Core configuration and model management
│   └── models.yaml                  # Model configuration file
├── 📁 src/                          # Core source code modules
│   ├── 📁 knowledge_base/           # Knowledge base core module ⭐
│   │   ├── chunking_strategies.py   # 🧠 Modular chunking strategy system
│   │   ├── document_processor.py    # 📄 Intelligent document processor
│   │   ├── knowledge_base_manager.py # 📚 Multi-knowledge base manager
│   │   └── vector_store_manager.py  # 🔍 Vector storage manager
│   ├── 📁 rag/                      # RAG workflow module
│   │   └── workflow.py              # 🔄 LangGraph workflow definition
│   ├── 📁 reranking/                # Reranking module
│   │   └── dashscope_rerank.py      # 🎯 DashScope reranking implementation
│   └── 📁 utils/                    # Utility modules
│       └── async_utils.py           # ⚙️ Asynchronous loop manager
├── 📁 scripts/                      # CLI tools and scripts
│   ├── knowledge_base_cli.py        # 🖥️ Enhanced CLI management tool
│   ├── add_test_documents.py        # 📄 Test document addition script
│   ├── test_connections.py          # 🔗 Connection testing script
│   └── reset_milvus_collection.py   # 🗑️ Milvus collection reset script
├── 📁 knowledge_base/               # Multi-knowledge base data storage ⭐
│   ├── 📁 knowledge_base/           # Default knowledge base
│   ├── 📁 ai_research/              # AI research knowledge base
│   └── 📁 [other_knowledge_bases]/  # Dynamically created knowledge bases
├── 📁 tests/                        # Testing modules
│   ├── 📁 unit/                     # Unit tests
│   └── [various_test_files]         # Async, integration tests, etc.
├── 📁 test_documents/               # Test document samples
├── 📁 examples/                     # Usage examples
└── 📁 docs/                         # Project documentation
```

## 📋 Core Module Functionality

### 🔧 Configuration Management (config/)
- **settings.py**: Unified configuration management supporting multi-knowledge bases, model configuration, vector storage, etc.
- **models.yaml**: Detailed configuration parameters for AI models

### 🤖 Core Source Code (src/)

#### Knowledge Base Core Module (knowledge_base/) ⭐
- **chunking_strategies.py**: 🧠 **Modular Chunking Strategy System**
  - 6 professional chunking strategies: Recursive, Token, Semantic, Character, Code, Format-specific
  - Factory pattern management with automatic strategy recommendation
  - Strategy registration and extension mechanisms
- **document_processor.py**: 📄 **Intelligent Document Processor**
  - Support for multiple document format loading
  - Automatic strategy selection and format-aware processing
  - Temporary strategy switching and parameter optimization
- **knowledge_base_manager.py**: 📚 **Multi-Knowledge Base Manager**
  - Create, delete, switch multiple independent knowledge bases
  - Support for chunking strategy configuration and metadata tracking
  - Complete lifecycle management
- **vector_store_manager.py**: 🔍 **Vector Storage Manager**
  - Asynchronous vector operation optimization
  - Thread pool fallback mechanisms
  - Batch processing and performance monitoring

#### RAG Workflow Module (rag/)
- **workflow.py**: 🔄 **LangGraph Asynchronous Workflow**
  - State machine-driven RAG processes
  - Asynchronous nodes and conditional routing
  - Extensible workflow architecture

#### Reranking Module (reranking/)
- **dashscope_rerank.py**: 🎯 **Intelligent Result Reranking**
  - DashScope API integration
  - Asynchronous reranking processing
  - Performance optimization strategies

#### Async Utility Module (utils/)
- **async_utils.py**: ⚙️ **Asynchronous Loop Manager**
  - Unified event loop management
  - Thread pool execution strategies
  - Asynchronous context detection

### 🖥️ CLI Tool System (scripts/)
- **knowledge_base_cli.py**: **Enhanced CLI Management Tool** ⭐
  ```bash
  # Knowledge base management
  python scripts/knowledge_base_cli.py create-kb <name>
  python scripts/knowledge_base_cli.py list-kb
  python scripts/knowledge_base_cli.py delete-kb <name> --confirm
  
  # Strategy management 🆕
  python scripts/knowledge_base_cli.py list-strategies
  python scripts/knowledge_base_cli.py recommend-strategy --file-type pdf
  
  # Document processing (with strategy selection) 🆕
  python scripts/knowledge_base_cli.py add-file doc.pdf --strategy format
  python scripts/knowledge_base_cli.py add-dir docs/ --strategy semantic
  ```

### 🗄️ Multi-Knowledge Base Storage (knowledge_base/) ⭐
- **Dynamic Knowledge Base Directories**: Each knowledge base has independent directories and metadata
- **Metadata Management**: Each knowledge base contains a `metadata/` subdirectory
- **Data Isolation**: Data from different knowledge bases is completely isolated

### 🧪 Testing System (tests/)
- **Asynchronous Testing**: Specialized asynchronous processing tests
- **Integration Testing**: Complete functional pipeline tests
- **Unit Testing**: Core module unit tests

## 🆕 Latest Features

### 🧠 Intelligent Chunking Strategy System
- **6 Professional Strategies**: Recursive, Token, Semantic, Character, Code, Format-specific
- **Automatic Strategy Recommendation**: Intelligently recommend optimal strategy based on file type
- **Format-Aware Processing**: Specialized optimization for PDF, code, Markdown, and other formats
- **Strategy Factory Pattern**: Support for dynamic registration and extension of new strategies

### 📚 Multi-Knowledge Base Architecture
- **Independent Knowledge Bases**: Each knowledge base has independent vector storage and metadata
- **Lifecycle Management**: Complete create, delete, switch, and list functionality
- **Data Isolation**: Complete data isolation between different knowledge bases
- **Concurrent Support**: Support for concurrent operations across multiple knowledge bases

### ⚡ Asynchronous Processing Optimization
- **Thread Pool Priority Strategy**: Avoid gRPC event loop conflicts
- **Intelligent Fallback Mechanism**: Automatically fallback to synchronous methods when async fails
- **Batch Processing Optimization**: Batch vectorization processing for large documents
- **Concurrency Control**: Reasonable concurrency limits and resource management

### 🖥️ Enhanced CLI Tools
- **Strategy Management Commands**: `list-strategies`, `recommend-strategy`
- **Parameterized Configuration**: Support for rich parameters like `--strategy`, `--chunk-size`
- **Automatic Mode**: Automatically select optimal strategy when processing directories
- **Detailed Feedback**: Complete processing progress and error information

## 🚀 Quick Navigation

### 🔧 Developing New Features
- **Add New Chunking Strategy** → `src/knowledge_base/chunking_strategies.py`
- **Extend Document Processing** → `src/knowledge_base/document_processor.py`
- **Enhance Knowledge Base Management** → `src/knowledge_base/knowledge_base_manager.py`
- **Add New API Endpoints** → `app/api/knowledge_base.py`
- **Extend CLI Tools** → `scripts/knowledge_base_cli.py`

### ⚙️ Configuration Modifications
- **Model and Vector Storage Configuration** → `config/settings.py`
- **Model Parameter Configuration** → `config/models.yaml`
- **Chunking Strategy Parameters** → Via CLI parameters or code configuration

### 🧪 Testing and Validation
- **Unit Tests** → `tests/unit/`
- **Asynchronous Tests** → `tests/test_*async*.py`
- **CLI Functionality Tests** → `scripts/knowledge_base_cli.py --help`
- **Multi-Knowledge Base Tests** → Refer to Chinese test reports

### 📚 Usage and Management
- **Create Knowledge Base** → `python scripts/knowledge_base_cli.py create-kb <name>`
- **Add Documents** → `python scripts/knowledge_base_cli.py add-file <path>`
- **View Strategies** → `python scripts/knowledge_base_cli.py list-strategies`
- **Get Recommendations** → `python scripts/knowledge_base_cli.py recommend-strategy --file-type pdf`

## 🎯 Architectural Advantages

### 🔄 Modular Design
- **Clear Responsibility Division**: Each module focuses on specific functional areas
- **Loose Coupling Architecture**: Modules interact through well-defined interfaces
- **Easy to Extend**: Support for rapid integration and deployment of new features

### 🛡️ High Reliability
- **Asynchronous Optimization**: Non-blocking I/O and intelligent thread pool management
- **Error Recovery**: Multi-layer fallback mechanisms and exception isolation
- **Resource Management**: Reasonable concurrency control and memory management

### 🧠 Intelligence
- **Automatic Strategy Selection**: Intelligently recommend processing strategies based on file type
- **Format Awareness**: Specialized optimization for different document formats
- **Performance Monitoring**: Detailed processing statistics and performance metrics

### 📈 Scalability
- **Multi-Knowledge Base Support**: Support for any number of independent knowledge bases
- **Strategy Pluginability**: Hot-swappable support for new chunking strategies
- **API Friendly**: RESTful API support for external system integration

---

📝 **Note**: This project structure has been validated through actual development and implements a high-performance RAG system. All modules support asynchronous processing with good extensibility and maintainability.

🔄 **Version**: v2.0 - Including multi-knowledge base and intelligent chunking strategy features
📅 **Last Updated**: 2025-07-29