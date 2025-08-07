# Base Agent Engineering

<div align="center">

[![English](https://img.shields.io/badge/Language-English-blue)](./README.md)
[![中文](https://img.shields.io/badge/语言-中文-red)](./README_CN.md)

</div>

---

## [English](./README.md) | 中文

**智能RAG系统** - 基于FastAPI的高性能检索增强生成(RAG)服务，集成知识库检索和联网搜索的混合智能助手。

## 核心特性

- **混合检索策略**: 知识库 + 联网搜索的智能融合
- **上下文工程**: 智能上下文选择、压缩和优化
- **高性能API**: 基于FastAPI的异步处理，支持流式响应
- **知识库管理**: 多种文档格式支持，智能分块策略
- **智能路由**: 根据查询类型自动选择最优检索策略
- **完整评估**: 检索质量和生成效果的全面评估体系
- **容器化部署**: Docker一键部署，包含向量数据库管理界面

##  关于这个项目

![1.png](images/1.png)

![1-1.png](images/1-1.png)

![2.png](images/2.png)

## 快速开始

### 环境要求

- Python 3.9+
- Docker & Docker Compose
- 8GB+ RAM (推荐16GB)

### 1. 克隆项目

```bash
git clone https://github.com/your-username/base_agent_engineering.git
cd base_agent_engineering
```

### 2. 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件，添加API密钥
vim .env
```

### 3. 一键启动

```bash
# 启动所有服务 (包含Milvus + Attu管理界面)
docker-compose up -d

# 安装Python依赖
pip install -r requirements.txt

# 启动RAG API服务
python main.py
```

### 4. 验证安装

```bash
# 健康检查
curl http://localhost:8010/health

# 获取模型信息
curl http://localhost:8010/api/v1/models

# 测试聊天功能
curl -X POST "http://localhost:8010/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "你好，介绍一下自己", "search_strategy": "web_only"}'
```

## 使用指南

#### 基础聊天接口

**URL**: `POST http://localhost:8010/api/v1/chat`

```bash
# 基础问答
curl -X POST "http://localhost:8010/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "什么是人工智能？",
    "search_strategy": "both",
    "max_web_results": 5,
    "max_kb_results": 5
  }'
```

#### 流式聊天接口

**URL**: `POST http://localhost:8010/api/v1/chat/stream`

```bash
curl -X POST "http://localhost:8010/api/v1/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "解释深度学习的原理",
    "stream": true
  }' \
  --no-buffer -N
```

#### 知识库管理

```bash
# 获取知识库列表
curl -X GET "http://localhost:8010/api/v1/knowledge-bases"

# 切换知识库
curl -X POST "http://localhost:8010/api/v1/switch-kb/ai_research"
```

### 命令行工具

#### 知识库管理

```bash
# 创建知识库
python -m cli kb create --name "tech_docs" --description "技术文档库"

# 上传文档
python -m cli docs upload --file document.pdf --collection tech_docs

# 批量上传
python -m cli docs batch-upload --directory ./documents/ --collection tech_docs

# 查看状态
python -m cli kb stats --name tech_docs
```

#### 搜索测试

```bash
# 交互式搜索
python -m cli search --interactive --collection tech_docs

# 单次搜索
python -m cli search --query "机器学习是什么" --collection tech_docs

# 混合搜索测试
python -m cli search --query "最新AI发展" --hybrid
```

#### 评估测试

```bash
# 检索质量评估
python -m cli eval retrieval --collection tech_docs --test-file test_queries.json

# 分块策略评估
python -m cli eval chunking --strategy semantic --test-file test_docs.json

# 生成基准测试报告
python -m cli eval report --output evaluation_report.html
```

## 配置说明

### 环境变量 (.env)

```bash
# API服务配置
API_HOST=0.0.0.0
API_PORT=8010                       # Chat API服务端口
API_WORKERS=4

# 数据库配置
MILVUS_HOST=localhost
MILVUS_PORT=19530
REDIS_URL=redis://localhost:6379

# API密钥
TAVILY_API_KEY=your_tavily_api_key  # 网络搜索API密钥

# 模型配置
DEFAULT_CHAT_MODEL=qwen-plus        # 千问Plus模型
DEFAULT_EMBEDDING_MODEL=text-embedding-v4

# 日志配置
LOG_LEVEL=INFO
```

### 端口配置

```bash
# 服务端口分配
8010    # Chat API主服务
19530   # Milvus向量数据库 (内部)
6379    # Redis缓存 (内部)
```

### 模型配置

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

### 检索策略配置

```yaml
# config/rag/hybrid_strategy_config.yaml
retrieval_strategies:
  default:
    knowledge_base_weight: 0.7
    web_search_weight: 0.3
    max_results_per_source: 5
    
  realtime_queries:
    knowledge_base_weight: 0.3
    web_search_weight: 0.7
    
  domain_specific:
    knowledge_base_weight: 0.9
    web_search_weight: 0.1
```

## 性能监控

### 系统指标

```bash
# 查看系统状态
curl http://localhost:8010/health

# 获取详细健康检查
curl http://localhost:8010/api/v1/health

# 查看模型信息
curl http://localhost:8010/api/v1/models
```

### 系统监控

**当前服务状态**:
- **服务端口**: 8010
- **聊天模型**: qwen-plus (千问Plus)
- **嵌入模型**: text-embedding-v4  
- **向量数据库**: Milvus
- **可用知识库**: 5个 (ai_research, knowledge_base, metadata, strategy_test, strategy_test_auto)
- **网络搜索**: ✅ 已启用 (Tavily)
- **语言自适应**: ✅ 已启用（自动检测用户语言并匹配回答语言）
- **Markdown支持**: ✅ 已启用（支持格式化输出）

## 测试和评估

### 运行测试

```bash
# 运行所有测试
python scripts/run_tests.py

# 或者直接使用pytest
pytest tests/unit/ -v

# 运行特定测试文件
pytest tests/unit/test_config.py -v

# 生成覆盖率报告
pytest --cov=config --cov=src --cov=app --cov-report=html
```

### 评估指标

- **检索质量**: Precision@K, Recall@K, MRR, NDCG
- **生成质量**: BLEU, ROUGE, 语义相似度
- **系统性能**: 响应时间, QPS, 资源使用率
- **用户体验**: 答案相关性, 信息完整性

## 部署指南

### 开发环境

```bash
# 启动开发服务器
python main.py

# 或使用uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
```

### 生产环境

```bash
# 使用Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# 或使用Kubernetes
kubectl apply -f deployment/k8s/
```

### 与Web服务集成

如果需要与其他Web服务部署在同一服务器，可以使用Nginx反向代理：

```nginx
# /etc/nginx/sites-available/your-site
server {
    listen 80;
    server_name your-domain.com;

    # 主Web应用
    location / {
        proxy_pass http://localhost:3000;  # 你的主Web服务
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Chat API服务
    location /api/chat/ {
        proxy_pass http://localhost:8010/api/v1/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 性能优化

- **并发处理**: 多worker进程
- **缓存策略**: Redis缓存热点数据
- **负载均衡**: Nginx反向代理
- **监控告警**: Prometheus + Grafana

## 开发指南

### 添加新功能

1. **新增检索策略**: 在 `src/retrieval/` 下实现
2. **新增分块方法**: 在 `src/knowledge_base/ingestion/` 下实现
3. **新增评估指标**: 在 `src/evaluation/` 下实现
4. **新增API接口**: 在 `app/api/` 下实现

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 Apache 2.0 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 常见问题

### Q: 如何添加新的文档类型支持？
A: 在 `src/knowledge_base/ingestion/document_processor.py` 中添加新的解析器。

### Q: 如何优化检索性能？
A: 调整 `config/retrieval/` 下的配置文件，或使用 `python -m cli eval` 进行性能测试。

### Q: 如何切换不同的向量数据库？
A: 修改 `docker-compose.yml` 和相应的配置文件，支持Milvus、Qdrant、Weaviate等。

### Q: 如何监控系统性能？
A: 使用Attu界面监控Milvus，通过 `/api/v1/metrics` 接口获取API指标。

### Q: 端口冲突怎么办？
A: 修改 `.env` 文件中的端口配置，默认使用8010(API)避免常用端口冲突。

---

相关博客：https://chongliujia.github.io/posts/rag%E7%B3%BB%E7%BB%9F%E5%BC%82%E6%AD%A5%E8%AE%BE%E8%AE%A1%E6%9E%B6%E6%9E%84%E6%96%87%E6%A1%A3/

---
⭐ 如果这个项目对你有帮助，请给个Star支持一下！
