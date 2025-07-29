# 项目目录结构

本文档详细描述了Base Agent Engineering项目的完整目录结构和各模块功能说明。

## 📋 模块功能说明

### 🔧 配置管理 (config/)
- **models/**: 各种AI模型的配置文件
- **retrieval/**: 检索策略和参数配置
- **rag/**: RAG系统的融合和路由配置

### 🤖 核心源码 (src/)

#### Agents模块 (agents/)
- **base_agent.py**: Agent基础类定义
- **rag_agent.py**: 主要的RAG智能体实现
- **knowledge_agent.py**: 专门处理知识库查询的Agent

#### RAG核心系统 (rag/)
- **query_analyzer.py**: 分析用户查询意图和类型
- **retrieval_router.py**: 智能路由到合适的检索策略
- **information_fusion.py**: 融合多源信息
- **context_builder.py**: 构建对话上下文
- **response_generator.py**: 生成最终回答

#### 检索系统 (retrieval/)
- **knowledge_base/**: 知识库检索（向量、关键词、混合）
- **web_search/**: 联网搜索（Tavily、SERP等）
- **fusion/**: 检索结果融合和去重
- **reranking/**: 结果重排序优化

#### 知识库管理 (knowledge_base/)
- **ingestion/**: 文档处理、分块、向量化流水线
- **storage/**: 向量存储、元数据存储、文件存储
- **maintenance/**: 索引优化和清理工具

#### 上下文工程 (context/)
- **memory_manager.py**: 管理对话历史记忆
- **context_selector.py**: 智能选择相关上下文
- **context_compressor.py**: 压缩长上下文
- **token_manager.py**: Token使用量管理

#### 评估系统 (evaluation/)
- **rag_evaluator.py**: 端到端RAG系统评估
- **retrieval_evaluator.py**: 检索质量评估
- **generation_evaluator.py**: 生成质量评估
- **benchmark_runner.py**: 自动化基准测试

#### API接口 (api/)
- **routes/**: RESTful API路由定义
- **schemas/**: 请求/响应数据模型

### 📚 数据存储 (knowledge_base/)
- **documents/**: 原始文档、处理后文档、元数据
- **embeddings/**: 向量数据存储
- **indexes/**: 搜索索引文件

### 🧪 测试 (tests/)
- **unit/**: 单元测试
- **integration/**: 集成测试
- **evaluation/**: 评估测试数据集

### 🛠️ 脚本工具 (scripts/)
- **setup_knowledge_base.py**: 初始化知识库
- **ingest_documents.py**: 批量导入文档
- **evaluate_rag.py**: 运行RAG评估
- **benchmark_retrieval.py**: 检索性能基准测试

## 🚀 快速导航

### 开发新功能
- 新增检索策略 → `src/retrieval/`
- 新增分块方法 → `src/knowledge_base/ingestion/`
- 新增评估指标 → `src/evaluation/`
- 新增API接口 → `src/api/routes/`

### 配置修改
- 模型配置 → `config/models/`
- 检索策略 → `config/retrieval/`
- RAG参数 → `config/rag/`

### 测试和评估
- 单元测试 → `tests/unit/`
- 性能测试 → `scripts/benchmark_*.py`
- 评估数据 → `tests/evaluation/`

---

📝 **注意**: 这个目录结构是模块化设计，支持独立开发和测试各个组件。每个模块都有清晰的职责分工，便于维护和扩展。