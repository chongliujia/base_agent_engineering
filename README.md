# Base Agent Engineering

🚀 **智能RAG系统** - 基于FastAPI的高性能检索增强生成(RAG)服务，集成知识库检索和联网搜索的混合智能助手。

## ✨ 核心特性

- 🔍 **混合检索策略**: 知识库 + 联网搜索的智能融合
- 🧠 **上下文工程**: 智能上下文选择、压缩和优化
- ⚡ **高性能API**: 基于FastAPI的异步处理，支持流式响应
- 📚 **知识库管理**: 多种文档格式支持，智能分块策略
- 🎯 **智能路由**: 根据查询类型自动选择最优检索策略
- 📊 **完整评估**: 检索质量和生成效果的全面评估体系
- 🐳 **容器化部署**: Docker一键部署，包含向量数据库管理界面

## 🏗️ 系统架构

## 🚀 快速开始

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
curl http://localhost:8888/api/v1/health

# 访问API文档
open http://localhost:8888/docs

# 访问Milvus管理界面
open http://localhost:8889
```

## 📖 使用指南

### API接口

#### 聊天对话 (兼容OpenAI格式)

```bash
curl -X POST "http://localhost:8888/api/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "什么是机器学习？"}
    ],
    "model": "rag-agent",
    "use_knowledge_base": true,
    "use_web_search": true,
    "search_strategy": "hybrid"
  }'
```

#### 流式聊天

```bash
curl -X POST "http://localhost:8888/api/v1/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "解释深度学习的原理"}
    ],
    "stream": true
  }'
```

#### 混合搜索

```bash
curl -X POST "http://localhost:8888/api/v1/search/hybrid" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "机器学习算法分类",
    "top_k": 10,
    "knowledge_base_weight": 0.7,
    "web_search_weight": 0.3
  }'
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

## ⚙️ 配置说明

### 环境变量 (.env)

```bash
# API服务配置
API_HOST=0.0.0.0
API_PORT=8888                       # RAG API服务端口
API_WORKERS=4

# 数据库配置
MILVUS_HOST=localhost
MILVUS_PORT=19530
REDIS_URL=redis://localhost:6379

# 管理界面
ATTU_PORT=8889                      # Milvus管理界面端口

# API密钥
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key

# 模型配置
DEFAULT_CHAT_MODEL=gpt-4
DEFAULT_EMBEDDING_MODEL=text-embedding-3-large
DEFAULT_RERANKING_MODEL=cross-encoder

# 日志配置
LOG_LEVEL=INFO
```

### 端口配置

```bash
# 服务端口分配
8888    # RAG API主服务
8889    # Milvus管理界面 (Attu)
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

## 📊 性能监控

### 系统指标

```bash
# 查看系统状态
python -m cli system status

# 性能指标
curl http://localhost:8888/api/v1/metrics
```

### Milvus管理界面

访问 `http://localhost:8889` 使用Attu管理界面：

- 📈 **性能监控**: 查询QPS、延迟统计
- 🗂️ **集合管理**: 创建、删除、查看集合
- 🔍 **数据查询**: 向量搜索测试
- 📊 **索引管理**: 索引类型和参数优化

## 🧪 测试和评估

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

## 🚀 部署指南

### 开发环境

```bash
# 启动开发服务器
python main.py

# 或使用uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8888
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

    # RAG API服务
    location /api/rag/ {
        proxy_pass http://localhost:8888/api/v1/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Milvus管理界面（可选）
    location /admin/milvus/ {
        proxy_pass http://localhost:8889/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 性能优化

- **并发处理**: 多worker进程
- **缓存策略**: Redis缓存热点数据
- **负载均衡**: Nginx反向代理
- **监控告警**: Prometheus + Grafana

## 🛠️ 开发指南

### 添加新功能

1. **新增检索策略**: 在 `src/retrieval/` 下实现
2. **新增分块方法**: 在 `src/knowledge_base/ingestion/` 下实现
3. **新增评估指标**: 在 `src/evaluation/` 下实现
4. **新增API接口**: 在 `app/api/` 下实现

### 代码规范

```bash
# 代码格式化
black .
isort .

# 类型检查
mypy .

# 代码质量检查
flake8 .
```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙋‍♂️ 常见问题

### Q: 如何添加新的文档类型支持？
A: 在 `src/knowledge_base/ingestion/document_processor.py` 中添加新的解析器。

### Q: 如何优化检索性能？
A: 调整 `config/retrieval/` 下的配置文件，或使用 `python -m cli eval` 进行性能测试。

### Q: 如何切换不同的向量数据库？
A: 修改 `docker-compose.yml` 和相应的配置文件，支持Milvus、Qdrant、Weaviate等。

### Q: 如何监控系统性能？
A: 使用Attu界面监控Milvus，通过 `/api/v1/metrics` 接口获取API指标。

### Q: 端口冲突怎么办？
A: 修改 `.env` 文件中的端口配置，默认使用8888(API)和8889(管理界面)避免常用端口冲突。

## 📞 支持

- 📧 Email: your-email@example.com
- 💬 Issues: [GitHub Issues](https://github.com/your-username/base_agent_engineering/issues)
- 📖 文档: [项目Wiki](https://github.com/your-username/base_agent_engineering/wiki)

---

⭐ 如果这个项目对你有帮助，请给个Star支持一下！