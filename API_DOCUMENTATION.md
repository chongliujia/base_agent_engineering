# Base Agent Engineering - API 接口文档

## 基础信息

- **服务地址**: `http://localhost:8010`
- **API版本**: v1
- **基础路径**: `/api/v1`
- **⚠️ 重要提示**: 使用知识库功能时，必须在请求中指定 `collection_name` 参数

## 聊天相关接口

### 1. 普通聊天接口

**接口**: `POST /api/v1/chat`

**描述**: 发送聊天消息并获取AI回复

**请求参数**:
```json
{
  "query": "你的问题",
  "collection_name": "car_docs",  // 🔑 必需: 指定知识库名称
  "search_strategy": "both",      // 可选: "knowledge_only", "web_only", "both"
  "max_web_results": 5,           // 可选: 网络搜索结果数量
  "max_kb_results": 5             // 可选: 知识库搜索结果数量
}
```

**响应示例**:
```json
{
  "response": "AI的回复内容",
  "sources": [
    {
      "type": "knowledge_base",
      "content": "相关知识库内容",
      "metadata": {...}
    }
  ],
  "timestamp": "2025-01-07T21:00:00Z"
}
```

**调用示例**:
```bash
# 使用car_docs知识库进行汽车相关咨询
curl -X POST "http://localhost:8010/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "汽车发动机故障怎么处理？",
    "collection_name": "car_docs",
    "search_strategy": "both",
    "max_web_results": 5,
    "max_kb_results": 5
  }'

# 仅使用网络搜索（无需指定知识库）
curl -X POST "http://localhost:8010/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "什么是人工智能？",
    "search_strategy": "web_only"
  }'
```

### 2. 流式聊天接口

**接口**: `POST /api/v1/stream`

**描述**: 发送聊天消息并获取流式AI回复

**请求参数**:
```json
{
  "query": "你的问题",
  "collection_name": "car_docs",  // 🔑 推荐: 指定知识库名称以获得更准确的回答
  "stream": true
}
```

**响应格式**: Server-Sent Events (SSE)

**调用示例**:
```bash
# 流式输出汽车相关问题回答
curl -X POST "http://localhost:8010/api/v1/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "汽车刹车系统保养注意事项？",
    "collection_name": "car_docs"
  }' \
  --no-buffer -N

# 一般性问题流式输出
curl -X POST "http://localhost:8010/api/v1/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "解释深度学习的原理",
    "search_strategy": "web_only"
  }' \
  --no-buffer -N
```

**JavaScript调用示例**:
```javascript
// 使用知识库的流式请求
const response = await fetch('http://localhost:8010/api/v1/chat/stream', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: '汽车保养相关问题',
    collection_name: 'car_docs'  // 🔑 指定知识库
  })
});

// 一般性问题的流式请求
const response2 = await fetch('http://localhost:8010/api/v1/chat/stream', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: '什么是机器学习？',
    search_strategy: 'web_only'
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = line.slice(6);
      if (data === '[DONE]') return;
      
      try {
        const parsed = JSON.parse(data);
        console.log(parsed);
      } catch (e) {
        // 处理解析错误
      }
    }
  }
}
```

## 知识库管理接口

### 3. 获取知识库列表

**接口**: `GET /api/v1/knowledge-bases`

**描述**: 获取所有可用的知识库列表

**响应示例**:
```json
[
  {
    "name": "car_docs",
    "description": "汽车文档知识库",
    "document_count": 150,
    "collection_name": "car_docs",
    "last_updated": "2025-01-07T20:00:00Z"
  },
  {
    "name": "ai_research",
    "description": "AI研究知识库",
    "document_count": 89,
    "collection_name": "ai_research",
    "last_updated": "2025-01-06T15:30:00Z"
  }
]
```

**调用示例**:
```bash
curl -X GET "http://localhost:8010/api/v1/knowledge-bases"
```

**响应示例中的知识库**:
- `car_docs`: 汽车维修和保养相关文档知识库
- `knowledge_base`: 默认通用知识库
- 其他自定义知识库

### 4. 切换知识库

**接口**: `POST /api/v1/switch-kb/{collection_name}`

**描述**: 切换当前使用的知识库

**路径参数**:
- `collection_name`: 知识库名称

**响应示例**:
```json
{
  "message": "Switched to knowledge base: car_docs",
  "current_kb": "car_docs",
  "timestamp": "2025-01-07T21:00:00Z"
}
```

**调用示例**:
```bash
curl -X POST "http://localhost:8010/api/v1/switch-kb/car_docs"
```

## 知识库操作接口

### 5. 上传单个文件

**接口**: `POST /api/v1/knowledge-base/upload-file`

**描述**: 上传单个文件到知识库

**请求参数**: `multipart/form-data`
- `file`: 文件对象
- `collection_name`: 知识库名称（可选）
- `chunking_strategy`: 分块策略（可选）

**调用示例**:
```bash
curl -X POST "http://localhost:8010/api/v1/knowledge-base/upload-file" \
  -F "file=@document.pdf" \
  -F "collection_name=car_docs" \
  -F "chunking_strategy=recursive"
```

### 6. 批量上传文件

**接口**: `POST /api/v1/knowledge-base/upload-files`

**描述**: 批量上传多个文件到知识库

**请求参数**: `multipart/form-data`
- `files`: 多个文件对象
- `collection_name`: 知识库名称（可选）

**调用示例**:
```bash
curl -X POST "http://localhost:8010/api/v1/knowledge-base/upload-files" \
  -F "files=@doc1.pdf" \
  -F "files=@doc2.txt" \
  -F "collection_name=car_docs"
```

### 7. 添加目录

**接口**: `POST /api/v1/knowledge-base/add-directory`

**描述**: 添加整个目录到知识库

**请求参数**:
```json
{
  "directory_path": "/path/to/documents",
  "collection_name": "car_docs",
  "recursive": true,
  "auto_strategy": true
}
```

### 8. 搜索知识库

**接口**: `GET /api/v1/knowledge-base/search`

**描述**: 在知识库中搜索内容

**查询参数**:
- `query`: 搜索查询（必需）
- `k`: 返回结果数量（默认5，最大20）
- `include_scores`: 是否包含相似度分数（默认false）

**调用示例**:
```bash
curl -X GET "http://localhost:8010/api/v1/knowledge-base/search?query=汽车发动机&k=10&include_scores=true"
```

### 9. 获取知识库统计

**接口**: `GET /api/v1/knowledge-base/stats`

**描述**: 获取当前知识库的统计信息

**响应示例**:
```json
{
  "total_documents": 150,
  "total_chunks": 1250,
  "collection_name": "car_docs",
  "file_types": {
    "pdf": 80,
    "txt": 45,
    "docx": 25
  },
  "last_updated": "2025-01-07T20:00:00Z"
}
```

**调用示例**:
```bash
curl -X GET "http://localhost:8010/api/v1/knowledge-base/stats"
```

### 10. 清空知识库

**接口**: `DELETE /api/v1/knowledge-base/clear`

**描述**: 清空当前知识库的所有内容

**调用示例**:
```bash
curl -X DELETE "http://localhost:8010/api/v1/knowledge-base/clear"
```

### 12. 获取知识库文档列表

**接口**: `GET /api/v1/knowledge-base/documents`

**描述**: 获取知识库中的文档列表

**查询参数**:
- `limit`: 返回文档数量限制（默认50，最大200）
- `collection_name`: 指定知识库名称（可选）

**调用示例**:
```bash
# 获取car_docs知识库中的文档列表
curl -X GET "http://localhost:8010/api/v1/knowledge-base/documents?collection_name=car_docs&limit=20"

# 获取默认知识库中的文档列表
curl -X GET "http://localhost:8010/api/v1/knowledge-base/documents"
```

**响应示例**:
```json
{
  "success": true,
  "total_documents_shown": 15,
  "unique_sources": [
    "/Users/jiachongliu/Downloads/汽车维修问题.pdf"
  ],
  "unique_filenames": [
    "汽车维修问题.pdf"
  ],
  "documents": [
    {
      "source": "/Users/jiachongliu/Downloads/汽车维修问题.pdf",
      "filename": "汽车维修问题.pdf",
      "file_type": ".pdf",
      "page": 1,
      "chunk_size": 856
    }
  ]
}
```

### 13. 按源文件路径删除文档

**接口**: `DELETE /api/v1/knowledge-base/documents/by-source`

**描述**: 根据源文件路径删除知识库中的所有相关文档块

**查询参数**:
- `source_path`: 源文件路径（必需）
- `collection_name`: 指定知识库名称（可选）

**调用示例**:
```bash
# 从car_docs知识库删除指定源文件的所有文档
curl -X DELETE "http://localhost:8010/api/v1/knowledge-base/documents/by-source?source_path=/Users/jiachongliu/Downloads/汽车维修问题.pdf&collection_name=car_docs"
```

**响应示例**:
```json
{
  "success": true,
  "message": "Successfully deleted documents from source: /Users/jiachongliu/Downloads/汽车维修问题.pdf",
  "source_path": "/Users/jiachongliu/Downloads/汽车维修问题.pdf",
  "delete_result": {
    "success": true,
    "message": "Delete successful"
  }
}
```

### 14. 按文件名删除文档

**接口**: `DELETE /api/v1/knowledge-base/documents/by-filename`

**描述**: 根据文件名删除知识库中的相关文档

**查询参数**:
- `filename`: 文件名（必需）
- `collection_name`: 指定知识库名称（可选）

**调用示例**:
```bash
# 从car_docs知识库删除指定文件名的所有文档
curl -X DELETE "http://localhost:8010/api/v1/knowledge-base/documents/by-filename?filename=汽车维修问题.pdf&collection_name=car_docs"
```

### 15. 获取支持的文件格式

**接口**: `GET /api/v1/knowledge-base/supported-formats`

**描述**: 获取系统支持的文件格式列表

**响应示例**:
```json
{
  "supported_formats": [
    ".pdf", ".txt", ".docx", ".md", ".py", ".js", ".html"
  ],
  "total_formats": 7
}
```

## 提示词管理接口

### 12. 获取提示词列表

**接口**: `GET /api/v1/chat/prompts`

**描述**: 获取可用的提示词模板

**查询参数**:
- `category`: 提示词分类（可选）

**调用示例**:
```bash
curl -X GET "http://localhost:8010/api/v1/chat/prompts?category=chat"
```

### 13. 添加自定义提示词

**接口**: `POST /api/v1/chat/prompts/{prompt_name}`

**描述**: 添加自定义提示词模板

**请求参数**:
```json
{
  "version": "1.0",
  "description": "自定义提示词描述",
  "template": "你是一个专业的{domain}助手...",
  "variables": ["domain"],
  "category": "custom"
}
```

## 系统监控接口

### 14. 健康检查

**接口**: `GET /api/v1/chat/health`

**描述**: 获取系统健康状态

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-07T21:00:00Z",
  "components": {
    "rag_workflow": "ok",
    "knowledge_base": "ok",
    "web_search": "ok",
    "prompt_manager": "ok"
  },
  "current_kb": "car_docs"
}
```

**调用示例**:
```bash
curl -X GET "http://localhost:8010/api/v1/chat/health"
```

## 错误处理

所有API接口都遵循统一的错误响应格式：

```json
{
  "detail": "错误描述信息",
  "status_code": 400
}
```

常见HTTP状态码：
- `200`: 成功
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误

## 前端集成示例

### React Hook 示例

```javascript
import { useState, useEffect } from 'react';

// 聊天Hook
export const useChat = () => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async (query, collectionName = 'car_docs') => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8010/api/v1/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          query, 
          collection_name: collectionName  // 🔑 指定知识库
        })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantMessage = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') break;

            try {
              const parsed = JSON.parse(data);
              if (parsed.type === 'content') {
                assistantMessage += parsed.content;
                // 实时更新UI
                setMessages(prev => [
                  ...prev.slice(0, -1),
                  { role: 'assistant', content: assistantMessage }
                ]);
              }
            } catch (e) {
              console.error('解析错误:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('发送消息失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return { messages, sendMessage, isLoading };
};

// 知识库管理Hook
export const useKnowledgeBase = () => {
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  const [currentKB, setCurrentKB] = useState('');

  const fetchKnowledgeBases = async () => {
    try {
      const response = await fetch('http://localhost:8010/api/v1/chat/knowledge-bases');
      const data = await response.json();
      setKnowledgeBases(data);
    } catch (error) {
      console.error('获取知识库列表失败:', error);
    }
  };

  const switchKnowledgeBase = async (kbName) => {
    try {
      const response = await fetch(`http://localhost:8010/api/v1/chat/switch-kb/${kbName}`, {
        method: 'POST'
      });
      const data = await response.json();
      setCurrentKB(kbName);
      return data;
    } catch (error) {
      console.error('切换知识库失败:', error);
    }
  };

  useEffect(() => {
    fetchKnowledgeBases();
  }, []);

  return {
    knowledgeBases,
    currentKB,
    switchKnowledgeBase,
    refreshKnowledgeBases: fetchKnowledgeBases
  };
};
```

### Vue.js 组合式API示例

```javascript
import { ref, onMounted } from 'vue';

// 聊天组合式函数
export function useChat() {
  const messages = ref([]);
  const isLoading = ref(false);

  const sendMessage = async (query, collectionName = 'car_docs') => {
    isLoading.value = true;
    
    // 添加用户消息
    messages.value.push({ role: 'user', content: query });
    
    try {
      const response = await fetch('http://localhost:8010/api/v1/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          query, 
          collection_name: collectionName  // 🔑 指定知识库
        })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      // 添加助手消息占位符
      messages.value.push({ role: 'assistant', content: '' });
      const assistantIndex = messages.value.length - 1;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') break;

            try {
              const parsed = JSON.parse(data);
              if (parsed.type === 'content') {
                messages.value[assistantIndex].content += parsed.content;
              }
            } catch (e) {
              console.error('解析错误:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('发送消息失败:', error);
    } finally {
      isLoading.value = false;
    }
  };

  return {
    messages,
    isLoading,
    sendMessage
  };
}
```

## 注意事项

1. **🔑 知识库指定**: 使用知识库功能时，**必须**在请求中指定 `collection_name` 参数
   - 汽车相关咨询请使用: `"collection_name": "car_docs"`
   - 如不指定或指定错误的名称，将使用默认知识库，可能无法检索到相关内容
2. **CORS设置**: 如果从浏览器调用API，确保服务器已正确配置CORS
3. **流式响应**: 使用流式接口时，注意正确处理SSE格式
4. **文件上传**: 上传大文件时建议显示进度条
5. **错误处理**: 建议实现统一的错误处理机制
6. **认证**: 如果需要认证，在请求头中添加相应的token
7. **端口配置**: 确保使用正确的端口号 `8010`（而非文档中可能出现的其他端口）

## 更新日志

- **v1.0.0**: 初始版本，包含基础聊天和知识库管理功能
- **v1.1.0**: 添加流式响应支持
- **v1.2.0**: 增加提示词管理功能
- **v1.3.0**: 优化文件上传和批量处理