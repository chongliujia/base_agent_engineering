# Base Agent Engineering

<div align="center">

[![English](https://img.shields.io/badge/Language-English-blue)](./README_EN.md)
[![中文](https://img.shields.io/badge/语言-中文-red)](./README.md)

</div>

---

## English | [中文](./README.md)

🚀 **Intelligent RAG System** - High-performance Retrieval-Augmented Generation (RAG) service based on FastAPI, integrating knowledge base retrieval and web search for a hybrid intelligent assistant.

---

## ✨ Core Features

- 🔍 **Hybrid Retrieval Strategy**: Intelligent fusion of knowledge base + web search
- 🧠 **Context Engineering**: Intelligent context selection, compression and optimization
- ⚡ **High-Performance API**: FastAPI-based asynchronous processing with streaming support
- 📚 **Knowledge Base Management**: Multi-format document support with intelligent chunking strategies
- 🎯 **Intelligent Routing**: Automatic optimal retrieval strategy selection based on query type
- 📊 **Comprehensive Evaluation**: Complete evaluation system for retrieval quality and generation effectiveness
- 🐳 **Containerized Deployment**: One-click Docker deployment with vector database management interface

## 🏗️ System Architecture

The system implements a sophisticated multi-layered architecture designed for scalability, reliability, and performance:

### Core Components
- **FastAPI Application Layer**: RESTful APIs with async support
- **RAG Workflow Engine**: LangGraph-based intelligent processing pipeline  
- **Multi-Knowledge Base System**: Independent knowledge collections with lifecycle management
- **Hybrid Search Engine**: Parallel knowledge base and web search with result fusion
- **Vector Storage Layer**: High-performance Milvus vector database
- **Intelligent Chunking System**: 6 specialized document processing strategies

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Docker & Docker Compose
- 8GB+ RAM (16GB recommended)

### 1. Clone Repository

```bash
git clone https://github.com/your-username/base_agent_engineering.git
cd base_agent_engineering
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit configuration file, add API keys
vim .env
```

### 3. One-Click Launch

```bash
# Start all services (including Milvus + Attu management interface)
docker-compose up -d

# Install Python dependencies
pip install -r requirements.txt

# Start RAG API service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
```

### 4. Verify Installation

```bash
# Health check
curl http://localhost:8010/api/v1/health

# Access API documentation
open http://localhost:8010/docs

# Access Milvus management interface
open http://localhost:8889
```

## 📖 Usage Guide

### API Endpoints

#### Chat Conversation (OpenAI Compatible)

```bash
curl -X POST "http://localhost:8010/api/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "What is machine learning?"}
    ],
    "model": "rag-agent",
    "use_knowledge_base": true,
    "use_web_search": true,
    "search_strategy": "hybrid"
  }'
```

#### Streaming Chat

```bash
curl -X POST "http://localhost:8010/api/v1/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Explain deep learning principles"}
    ],
    "stream": true
  }'
```

#### Hybrid Search

```bash
curl -X POST "http://localhost:8010/api/v1/search/hybrid" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning algorithm classification",
    "top_k": 10,
    "knowledge_base_weight": 0.7,
    "web_search_weight": 0.3
  }'
```

### Command Line Tools

#### Knowledge Base Management

```bash
# Create knowledge base
python -m cli kb create --name "tech_docs" --description "Technical documentation"

# Upload documents
python -m cli docs upload --file document.pdf --collection tech_docs

# Batch upload
python -m cli docs batch-upload --directory ./documents/ --collection tech_docs

# View status
python -m cli kb stats --name tech_docs
```

#### Search Testing

```bash
# Interactive search
python -m cli search --interactive --collection tech_docs

# Single search
python -m cli search --query "What is machine learning" --collection tech_docs

# Hybrid search test
python -m cli search --query "Latest AI developments" --hybrid
```

#### Enhanced CLI Tool

```bash
# Knowledge base operations
python scripts/knowledge_base_cli.py create-kb ai_research
python scripts/knowledge_base_cli.py list-kb
python scripts/knowledge_base_cli.py delete-kb test_kb --confirm

# Strategy management
python scripts/knowledge_base_cli.py list-strategies
python scripts/knowledge_base_cli.py recommend-strategy --file-type pdf

# Document processing with strategy selection
python scripts/knowledge_base_cli.py add-file doc.pdf --strategy semantic
python scripts/knowledge_base_cli.py add-dir docs/ --strategy recursive
```

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# API Service Configuration
API_HOST=0.0.0.0
API_PORT=8010                       # RAG API service port
API_WORKERS=4

# Database Configuration
MILVUS_HOST=localhost
MILVUS_PORT=19530
REDIS_URL=redis://localhost:6379

# Management Interface
ATTU_PORT=8889                      # Milvus management interface port

# API Keys
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key

# Model Configuration
DEFAULT_CHAT_MODEL=gpt-4
DEFAULT_EMBEDDING_MODEL=text-embedding-3-large
DEFAULT_RERANKING_MODEL=cross-encoder

# Logging Configuration
LOG_LEVEL=INFO
```

### Port Configuration

```bash
# Service port allocation
8010    # RAG API main service
8889    # Milvus management interface (Attu)
19530   # Milvus vector database (internal)
6379    # Redis cache (internal)
```

### Model Configuration

```yaml
# config/models/chat_models.yaml
models:
  primary:
    name: "gpt-4"
    provider: "openai"
    parameters:
      temperature: 0.7
      max_tokens: 2000
    cost_per_1k_tokens: 0.03
  
  fallback:
    name: "gpt-3.5-turbo"
    provider: "openai"
    parameters:
      temperature: 0.7
      max_tokens: 1500
    cost_per_1k_tokens: 0.002
```

## 🧪 Testing and Evaluation

### Run Tests

```bash
# Run all tests
python scripts/run_tests.py

# Or use pytest directly
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_config.py -v

# Generate coverage report
pytest --cov=config --cov=src --cov=app --cov-report=html
```

### Evaluation Metrics

- **Retrieval Quality**: Precision@K, Recall@K, MRR, NDCG
- **Generation Quality**: BLEU, ROUGE, Semantic Similarity
- **System Performance**: Response Time, QPS, Resource Utilization
- **User Experience**: Answer Relevance, Information Completeness

## 🚀 Deployment Guide

### Development Environment

```bash
# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8010

# Or use uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
```

### Production Environment

```bash
# Using Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Or using Kubernetes
kubectl apply -f deployment/k8s/
```

### Web Service Integration

For deployment alongside other web services on the same server, use Nginx reverse proxy:

```nginx
# /etc/nginx/sites-available/your-site
server {
    listen 80;
    server_name your-domain.com;

    # Main web application
    location / {
        proxy_pass http://localhost:3000;  # Your main web service
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # RAG API service
    location /api/rag/ {
        proxy_pass http://localhost:8010/api/v1/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Milvus management interface (optional)
    location /admin/milvus/ {
        proxy_pass http://localhost:8889/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🆕 Latest Features

### 🧠 Intelligent Chunking Strategy System
- **6 Professional Strategies**: Recursive, Token, Semantic, Character, Code, Format-specific
- **Automatic Strategy Recommendation**: Smart strategy suggestion based on file type
- **Format-Aware Processing**: Specialized optimization for PDF, code, Markdown formats
- **Factory Pattern**: Dynamic registration and extension of new strategies

### 📚 Multi-Knowledge Base Architecture
- **Independent Knowledge Bases**: Each KB has separate vector storage and metadata
- **Lifecycle Management**: Complete create, delete, switch, and list functionality
- **Data Isolation**: Complete separation between different knowledge bases
- **Concurrent Support**: Multi-KB concurrent operations

### ⚡ Asynchronous Processing Optimization
- **Thread Pool Priority**: Avoid gRPC event loop conflicts
- **Smart Fallback**: Auto-fallback to sync methods when async fails
- **Batch Processing**: Optimized batch vectorization for large documents
- **Concurrency Control**: Reasonable limits and resource management

### 🌐 Smart Language Adaptation
- **Auto Language Detection**: Automatically detect query language
- **Matching Response Language**: English queries get English responses
- **Streaming Adaptation**: Progress messages match query language

## 📊 Performance Monitoring

### System Metrics

```bash
# View system status
python -m cli system status

# Performance metrics
curl http://localhost:8010/api/v1/metrics
```

### Milvus Management Interface

Access `http://localhost:8889` for Attu management interface:

- 📈 **Performance Monitoring**: Query QPS, latency statistics
- 🗂️ **Collection Management**: Create, delete, view collections
- 🔍 **Data Querying**: Vector search testing
- 📊 **Index Management**: Index types and parameter optimization

## 🛠️ Development Guide

### Adding New Features

1. **New Retrieval Strategy**: Implement in `src/retrieval/`
2. **New Chunking Method**: Implement in `src/knowledge_base/ingestion/`
3. **New Evaluation Metric**: Implement in `src/evaluation/`
4. **New API Endpoint**: Implement in `app/api/`

## 🤝 Contributing

1. Fork the project
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ FAQ

### Q: How to add support for new document types?
A: Add new parsers in `src/knowledge_base/ingestion/document_processor.py`.

### Q: How to optimize retrieval performance?
A: Adjust configuration files in `config/retrieval/` or use `python -m cli eval` for performance testing.

### Q: How to switch to different vector databases?
A: Modify `docker-compose.yml` and corresponding config files. Supports Milvus, Qdrant, Weaviate, etc.

### Q: How to monitor system performance?
A: Use Attu interface for Milvus monitoring, get API metrics via `/api/v1/metrics` endpoint.

### Q: What about port conflicts?
A: Modify port configuration in `.env` file. Default ports 8010 (API) and 8889 (management) avoid common port conflicts.


---

Related Blogs: https://chongliujia.github.io/posts/rag%E7%B3%BB%E7%BB%9F%E5%BC%82%E6%AD%A5%E8%AE%BE%E8%AE%A1%E6%9E%B6%E6%9E%84%E6%96%87%E6%A1%A3/

---

⭐ If this project helps you, please give it a Star for support!
