# 知识库操作说明手册

## 概述

本手册详细介绍如何使用知识库系统进行文档管理、向量化存储和智能搜索。

## 目录

1. [系统架构](#系统架构)
2. [环境配置](#环境配置)
3. [文档上传](#文档上传)
4. [批量上传](#批量上传)
5. [分块策略](#分块策略)
6. [搜索测试](#搜索测试)
7. [统计信息](#统计信息)
8. [故障排除](#故障排除)

## 系统架构

知识库系统包含以下核心组件：

- **文档处理器**: 支持多种文件格式（TXT、PDF、DOCX、MD等）
- **分块器**: 将长文档分割成适合向量化的小块
- **向量存储**: 使用Milvus存储文档向量
- **嵌入模型**: 将文本转换为向量表示
- **搜索引擎**: 基于语义相似度的智能搜索

## 环境配置

### 1. 启动Milvus服务

```bash
# 使用Docker启动Milvus
docker run -d --name milvus-standalone \
  -p 19530:19530 \
  -v milvus_data:/var/lib/milvus \
  milvusdb/milvus:latest standalone
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置文件

检查 `config/config.yaml` 中的设置：

```yaml
vector_store:
  type: "milvus"
  host: "localhost"
  port: 19530
  collection_name: "knowledge_base"

embedding:
  model_name: "text-embedding-ada-002"
  
chunking:
  chunk_size: 1000
  chunk_overlap: 200
```

## 文档上传

### 单文件上传

```bash
# 上传单个文件
python scripts/knowledge_base_cli.py add-file path/to/document.txt

# 指定分块大小
python scripts/knowledge_base_cli.py add-file document.pdf --chunk-size 800 --chunk-overlap 150
```

### 支持的文件格式

- **文本文件**: `.txt`, `.md`
- **PDF文件**: `.pdf`
- **Word文档**: `.docx`, `.doc`
- **网页文件**: `.html`

### 上传示例

```bash
# 上传Markdown文件
python scripts/knowledge_base_cli.py add-file docs/readme.md

# 上传PDF并自定义分块
python scripts/knowledge_base_cli.py add-file research.pdf --chunk-size 1200 --chunk-overlap 100
```

## 批量上传

### 目录批量上传

```bash
# 上传整个目录
python scripts/knowledge_base_cli.py add-directory /path/to/documents/

# 指定文件类型过滤
python scripts/knowledge_base_cli.py add-directory docs/ --file-types txt,md,pdf

# 递归上传子目录
python scripts/knowledge_base_cli.py add-directory docs/ --recursive
```

### 批量上传脚本

创建批量上传脚本：

```python
#!/usr/bin/env python3
"""批量上传脚本示例"""

import asyncio
from src.knowledge_base.knowledge_base_manager import KnowledgeBaseManager

async def batch_upload():
    kb_manager = KnowledgeBaseManager()
    
    # 文件列表
    files = [
        "docs/manual.pdf",
        "docs/faq.md", 
        "docs/tutorial.txt"
    ]
    
    for file_path in files:
        print(f"上传文件: {file_path}")
        result = await kb_manager.add_file(file_path)
        print(f"结果: {result}")

if __name__ == "__main__":
    asyncio.run(batch_upload())
```

## 分块策略

### 分块参数说明

- **chunk_size**: 每个分块的最大字符数（推荐：800-1200）
- **chunk_overlap**: 分块间重叠字符数（推荐：chunk_size的10-20%）

### 不同文档类型的推荐设置

| 文档类型 | chunk_size | chunk_overlap | 说明 |
|---------|------------|---------------|------|
| 技术文档 | 1000 | 200 | 保持技术概念完整性 |
| 小说/故事 | 800 | 150 | 保持情节连贯性 |
| 学术论文 | 1200 | 250 | 保持论证逻辑完整 |
| FAQ文档 | 600 | 100 | 每个问答独立分块 |
| 代码文档 | 1500 | 300 | 保持代码块完整 |

### 自定义分块策略

```python
from src.document_processing.chunking_strategy import ChunkingStrategy

# 创建自定义分块器
chunker = ChunkingStrategy(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", "。", ".", " "]
)

# 应用分块
chunks = chunker.split_text(document_text)
```

## 搜索测试

### 基本搜索

```bash
# 基本搜索
python scripts/knowledge_base_cli.py search "机器学习"

# 指定返回数量
python scripts/knowledge_base_cli.py search "人工智能" -k 5

# 显示相似度分数
python scripts/knowledge_base_cli.py search "深度学习" --scores
```

### 高级搜索

```bash
# 带元数据过滤的搜索
python scripts/knowledge_base_cli.py search "算法" --filter "source:algorithm.pdf"

# 多关键词搜索
python scripts/knowledge_base_cli.py search "机器学习 神经网络" -k 10
```

### 搜索质量评估

#### 1. 相似度分数解读

- **0.9-1.0**: 极高相关性，几乎完全匹配
- **0.8-0.9**: 高相关性，内容高度相关
- **0.7-0.8**: 中等相关性，有一定关联
- **0.6-0.7**: 低相关性，可能相关
- **<0.6**: 相关性很低，可能不相关

#### 2. 搜索效果测试

```python
# 创建测试脚本
test_queries = [
    "什么是机器学习？",
    "深度学习的应用领域",
    "如何选择算法？",
    "数据预处理步骤"
]

for query in test_queries:
    print(f"\n查询: {query}")
    # 执行搜索并分析结果
```

## 统计信息

### 查看知识库统计

```bash
# 查看统计信息
python scripts/knowledge_base_cli.py stats
```

### 统计信息包含

- **集合名称**: 向量存储集合名
- **文档数量**: 存储的文档分块总数
- **处理统计**: 上传成功率、失败次数等
- **最后更新时间**: 最近一次更新时间

### 详细统计脚本

```python
#!/usr/bin/env python3
"""详细统计信息脚本"""

import asyncio
from src.knowledge_base.knowledge_base_manager import KnowledgeBaseManager

async def detailed_stats():
    kb_manager = KnowledgeBaseManager()
    
    # 获取统计信息
    stats = kb_manager.get_knowledge_base_stats()
    
    print("📊 详细统计信息:")
    print(f"  向量存储统计: {stats.get('vector_stats', {})}")
    print(f"  处理历史: {stats.get('processing_stats', {})}")
    
    # 测试搜索功能
    test_result = await kb_manager.search("测试", k=1)
    print(f"  搜索功能状态: {'正常' if test_result else '异常'}")

if __name__ == "__main__":
    asyncio.run(detailed_stats())
```

## 命中测试

### 1. 准确性测试

创建测试查询集合，验证搜索结果的准确性：

```python
#!/usr/bin/env python3
"""搜索准确性测试"""

test_cases = [
    {
        "query": "机器学习定义",
        "expected_keywords": ["机器学习", "算法", "数据", "学习"],
        "min_score": 0.7
    },
    {
        "query": "深度学习应用",
        "expected_keywords": ["深度学习", "神经网络", "应用"],
        "min_score": 0.6
    }
]

async def accuracy_test():
    kb_manager = KnowledgeBaseManager()
    
    for test_case in test_cases:
        query = test_case["query"]
        results = await kb_manager.search(query, k=3)
        
        print(f"\n测试查询: {query}")
        
        if not results:
            print("❌ 无搜索结果")
            continue
            
        for i, (doc, score) in enumerate(results):
            print(f"  结果 {i+1}: 分数={score:.3f}")
            
            # 检查关键词匹配
            content = doc.page_content.lower()
            matched_keywords = [
                kw for kw in test_case["expected_keywords"] 
                if kw.lower() in content
            ]
            
            print(f"    匹配关键词: {matched_keywords}")
            print(f"    分数达标: {'✅' if score >= test_case['min_score'] else '❌'}")

if __name__ == "__main__":
    asyncio.run(accuracy_test())
```

### 2. 性能测试

```python
#!/usr/bin/env python3
"""搜索性能测试"""

import time
import asyncio
from src.knowledge_base.knowledge_base_manager import KnowledgeBaseManager

async def performance_test():
    kb_manager = KnowledgeBaseManager()
    
    queries = [
        "机器学习", "人工智能", "深度学习", 
        "算法优化", "数据分析", "神经网络"
    ]
    
    total_time = 0
    successful_queries = 0
    
    for query in queries:
        start_time = time.time()
        
        try:
            results = await kb_manager.search(query, k=5)
            end_time = time.time()
            
            query_time = end_time - start_time
            total_time += query_time
            successful_queries += 1
            
            print(f"查询: {query}")
            print(f"  耗时: {query_time:.3f}秒")
            print(f"  结果数: {len(results)}")
            
        except Exception as e:
            print(f"查询失败: {query} - {e}")
    
    if successful_queries > 0:
        avg_time = total_time / successful_queries
        print(f"\n性能统计:")
        print(f"  平均查询时间: {avg_time:.3f}秒")
        print(f"  成功查询数: {successful_queries}/{len(queries)}")

if __name__ == "__main__":
    asyncio.run(performance_test())
```

## 故障排除

### 常见问题

#### 1. Milvus连接失败

```bash
# 检查Milvus服务状态
docker ps | grep milvus

# 重启Milvus服务
docker restart milvus-standalone
```

#### 2. 文档上传失败

- 检查文件路径是否正确
- 确认文件格式是否支持
- 查看错误日志获取详细信息

#### 3. 搜索结果不准确

- 调整分块大小和重叠参数
- 检查嵌入模型是否适合文档类型
- 增加训练数据量

#### 4. 统计信息显示N/A

- 检查向量存储连接
- 确认集合是否正确创建
- 查看日志中的错误信息

### 日志分析

```bash
# 查看详细日志
python scripts/knowledge_base_cli.py search "test" --verbose

# 启用调试模式
export LOG_LEVEL=DEBUG
python scripts/knowledge_base_cli.py stats
```

### 数据备份与恢复

```bash
# 导出知识库数据
python scripts/export_knowledge_base.py --output backup.json

# 恢复知识库数据
python scripts/import_knowledge_base.py --input backup.json
```

## 最佳实践

### 1. 文档准备

- 确保文档内容清晰、结构化
- 移除不必要的格式和特殊字符
- 为重要文档添加元数据标签

### 2. 分块优化

- 根据文档类型选择合适的分块大小
- 保持重要概念在同一分块内
- 定期测试和调整分块参数

### 3. 搜索优化

- 使用具体、明确的查询词
- 结合多个关键词提高准确性
- 根据结果反馈调整搜索策略

### 4. 维护管理

- 定期清理过时文档
- 监控系统性能指标
- 备份重要数据

## 联系支持

如遇到问题，请：

1. 查看日志文件获取错误详情
2. 参考本手册的故障排除部分
3. 提交Issue并附上详细的错误信息

---

*最后更新: 2025-01-29*