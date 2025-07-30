# Chat API 使用文档

## 概述

Chat API 是一个基于LangChain和LangGraph的智能对话接口，支持知识库检索和联网搜索功能。该API可以集成到网站中，为用户提供智能问答服务。

## 基础信息

- **当前服务地址**: `http://localhost:8010`
- **API版本**: v1
- **基础URL**: `http://localhost:8010/api/v1`
- **协议**: HTTP/HTTPS
- **请求格式**: JSON
- **响应格式**: JSON
- **支持模型**: 千问Plus (qwen-plus)
- **向量存储**: Milvus

## 主要接口

### 1. 聊天对话接口

#### POST `/api/v1/chat`

主要的聊天接口，支持智能问答、知识库检索和联网搜索。基于LangGraph工作流实现混合检索策略。

**请求参数**:

```json
{
  "query": "string",           // 必填：用户问题（1-1000字符）
  "collection_name": "string", // 可选：指定知识库集合名称
  "search_strategy": "string", // 可选：检索策略（knowledge_only/web_only/both，默认both）
  "prompt_template": "string", // 可选：自定义提示词模板名称
  "stream": false,            // 可选：是否流式响应（默认false）
  "max_web_results": 5,       // 可选：最大网络搜索结果数（1-10，默认5）
  "max_kb_results": 5         // 可选：最大知识库检索结果数（1-10，默认5）
}
```

**响应格式**:

```json
{
  "query": "string",          // 用户问题
  "response": "string",       // AI回答
  "sources": {                // 来源信息
    "knowledge_base": [       // 知识库来源
      {
        "content": "string",
        "metadata": {},
        "relevance_score": 0.8
      }
    ],
    "web_search": [           // 网络搜索来源
      {
        "title": "string",
        "content": "string",
        "url": "string",
        "score": 0.9
      }
    ]
  },
  "metadata": {               // 元数据
    "collection_used": "string",
    "search_strategy": "string",
    "knowledge_retrieved": 5,
    "web_retrieved": 3,
    "processing_time": 2.5
  },
  "timestamp": "2024-01-01T00:00:00",
  "processing_time": 2.5
}
```

### 2. 流式对话接口

#### POST `/api/v1/chat/stream`

支持Server-Sent Events的流式响应，实时返回处理进度。适合需要实时反馈的场景。

**使用方法**:

```javascript
// 流式请求示例（使用fetch）
async function streamChat(query) {
  const response = await fetch('http://localhost:8010/api/v1/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: query,
      stream: true
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') return;
        
        try {
          const parsed = JSON.parse(data);
          switch(parsed.type) {
            case 'start':
              console.log('开始处理:', parsed.message);
              break;
            case 'progress':
              console.log('处理进度:', parsed.message);
              break;
            case 'complete':
              console.log('完成:', parsed.response);
              break;
            case 'error':
              console.error('错误:', parsed.message);
              break;
          }
        } catch (e) {
          // 忽略解析错误
        }
      }
    }
  }
}
```

### 3. 模型信息接口

#### GET `/api/v1/models`

获取当前加载的模型信息和配置。

**响应格式**:

```json
{
  "chat_model": {
    "name": "qwen-plus",
    "provider": "langchain_openai",
    "max_context_length": 8192
  },
  "embedding_model": {
    "name": "text-embedding-v4",
    "provider": "langchain_community",
    "dimensions": "unknown"
  },
  "vector_store": "milvus",
  "langsmith_enabled": false
}
```

### 4. 知识库管理接口

#### GET `/api/v1/knowledge-bases`

获取所有可用的知识库列表。

**响应格式**:

```json
[
  {
    "name": "ai_research",
    "description": "知识库 ai_research",
    "document_count": 0,
    "collection_name": "ai_research",
    "last_updated": ""
  },
  {
    "name": "knowledge_base",
    "description": "知识库 knowledge_base", 
    "document_count": 0,
    "collection_name": "knowledge_base",
    "last_updated": ""
  }
]
```

#### POST `/api/v1/switch-kb/{collection_name}`

切换当前使用的知识库。

**响应格式**:

```json
{
  "message": "已切换到知识库: collection_name",
  "current_kb": "collection_name",
  "timestamp": "2025-07-31T00:00:00"
}
```

### 5. 提示词管理接口

#### GET `/api/v1/prompts`

获取可用的提示词模板。

**查询参数**:
- `category`: 可选，提示词类别过滤

#### POST `/api/v1/prompts/{prompt_name}`

添加自定义提示词模板。

### 6. 健康检查接口

#### GET `/health`

检查API服务状态。（注意：此接口在根路径，不在/api/v1下）

**响应格式**:

```json
{
  "status": "healthy",
  "timestamp": 1753893696.392066,
  "version": "1.0.0",
  "models": {
    "chat_model": true,
    "embedding_model": true,
    "vector_store": true
  },
  "langchain_enabled": true,
  "langgraph_enabled": true,
  "langsmith_tracing": false
}
```

#### GET `/api/v1/health`

详细的健康检查接口（在API路径下）。

**响应格式**:

```json
{
  "status": "healthy",
  "timestamp": "2025-07-31T00:00:00",
  "components": {
    "rag_workflow": "ok",
    "knowledge_base": "ok",
    "web_search": "ok",
    "prompt_manager": "ok"
  },
  "current_kb": "knowledge_base"
}
```

## 网站集成示例

### JavaScript 示例

```javascript
class ChatAPI {
  constructor(baseURL) {
    this.baseURL = baseURL;
  }

  async sendMessage(query, options = {}) {
    const response = await fetch(`${this.baseURL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: query,
        ...options
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  }

  async getKnowledgeBases() {
    const response = await fetch(`${this.baseURL}/knowledge-bases`);
    return await response.json();
  }

  async switchKnowledgeBase(kbName) {
    const response = await fetch(`${this.baseURL}/switch-kb/${kbName}`, {
      method: 'POST'
    });
    return await response.json();
  }

  async getModels() {
    const response = await fetch(`${this.baseURL}/models`);
    return await response.json();
  }
}

// 使用示例
const chatAPI = new ChatAPI('http://localhost:8010/api/v1');

// 发送消息
chatAPI.sendMessage('你好，请介绍一下你的功能')
  .then(response => {
    console.log('AI回答:', response.response);
    console.log('来源信息:', response.sources);
    console.log('处理时间:', response.processing_time);
  })
  .catch(error => {
    console.error('错误:', error);
  });

// 获取模型信息
chatAPI.getModels()
  .then(models => {
    console.log('当前模型:', models.chat_model.name);
    console.log('向量存储:', models.vector_store);
  });
```

### HTML 聊天界面示例

```html
<!DOCTYPE html>
<html>
<head>
    <title>AI助手聊天界面</title>
    <meta charset="UTF-8">
    <style>
        .chat-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .chat-messages {
            border: 1px solid #ddd;
            height: 400px;
            overflow-y: auto;
            padding: 10px;
            margin-bottom: 10px;
        }
        .message {
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 5px;
        }
        .user-message {
            background-color: #e3f2fd;
            text-align: right;
        }
        .ai-message {
            background-color: #f5f5f5;
        }
        .input-container {
            display: flex;
            gap: 10px;
        }
        #messageInput {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        #sendButton {
            padding: 10px 20px;
            background-color: #2196f3;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <h1>AI咨询助手</h1>
        <div id="chatMessages" class="chat-messages"></div>
        <div class="input-container">
            <input type="text" id="messageInput" placeholder="请输入您的问题..." />
            <button id="sendButton">发送</button>
        </div>
    </div>

    <script>
        const chatAPI = new ChatAPI('http://localhost:8010/api/v1');
        const messagesContainer = document.getElementById('chatMessages');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');

        function addMessage(content, isUser = false) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
            messageDiv.innerHTML = content;
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        async function sendMessage() {
            const query = messageInput.value.trim();
            if (!query) return;

            addMessage(query, true);
            messageInput.value = '';
            sendButton.disabled = true;

            try {
                const response = await chatAPI.sendMessage(query);
                addMessage(response.response);
                
                // 显示来源信息（可选）
                if (response.sources.knowledge_base.length > 0 || response.sources.web_search.length > 0) {
                    let sourcesHtml = '<small><strong>信息来源:</strong><br>';
                    response.sources.knowledge_base.forEach(source => {
                        sourcesHtml += `📚 知识库: ${source.content}<br>`;
                    });
                    response.sources.web_search.forEach(source => {
                        sourcesHtml += `🔍 网络: <a href="${source.url}" target="_blank">${source.title}</a><br>`;
                    });
                    sourcesHtml += '</small>';
                    addMessage(sourcesHtml);
                }
            } catch (error) {
                addMessage(`<span style="color: red;">错误: ${error.message}</span>`);
            } finally {
                sendButton.disabled = false;
            }
        }

        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
```

## 错误处理

常见的HTTP状态码和错误处理：

- `200`: 成功
- `400`: 请求参数错误
- `404`: 资源不存在（如知识库不存在）
- `500`: 服务器内部错误

错误响应格式：

```json
{
  "detail": "错误描述信息"
}
```

## 最佳实践

1. **请求频率限制**: 建议控制请求频率，避免过于频繁的API调用
2. **错误重试**: 实现适当的错误重试机制
3. **超时设置**: 设置合理的请求超时时间（建议30秒）
4. **缓存策略**: 对于重复的查询可以考虑客户端缓存
5. **流式响应**: 对于长时间处理的查询，建议使用流式接口

## 配置说明

在使用前需要确保以下配置正确：

1. **API密钥**: 确保配置了必要的API密钥（如搜索引擎API）
2. **知识库**: 上传并配置好知识库文档
3. **提示词**: 根据业务需求配置合适的提示词模板

## 快速测试命令

以下是一些可以立即使用的测试命令：

```bash
# 1. 健康检查
curl http://localhost:8010/health

# 2. 获取模型信息
curl http://localhost:8010/api/v1/models

# 3. 获取知识库列表
curl http://localhost:8010/api/v1/knowledge-bases

# 4. 基础聊天测试
curl -X POST "http://localhost:8010/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "你好，介绍一下自己", "search_strategy": "web_only"}'

# 5. 流式聊天测试（中文）
curl -X POST "http://localhost:8010/api/v1/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是人工智能？", "stream": true}' \
  --no-buffer -N

# 6. 英文查询测试（自动语言适配）
curl -X POST "http://localhost:8010/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "search_strategy": "web_only"}'

# 7. 流式英文查询测试
curl -X POST "http://localhost:8010/api/v1/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain artificial intelligence", "stream": true}' \
  --no-buffer -N
```

## 当前配置状态

- **服务端口**: 8010
- **聊天模型**: qwen-plus (千问Plus)
- **嵌入模型**: text-embedding-v4
- **向量数据库**: Milvus
- **可用知识库**: 5个 (ai_research, knowledge_base, metadata, strategy_test, strategy_test_auto)
- **网络搜索**: 已启用 (Tavily)
- **LangSmith追踪**: 未启用
- **语言自适应**: ✅ 已启用（自动检测用户语言并匹配回答语言）
- **Markdown支持**: ✅ 已启用（支持格式化输出）
- **字符编码**: UTF-8（已修复中文显示问题）

## 新功能特性

### 🌐 智能语言适配
- **自动语言检测**: 系统会自动检测用户查询的语言（中文/英文等）
- **匹配语言回答**: 英文查询返回英文回答，中文查询返回中文回答
- **流式消息适配**: 流式响应的进度提示也会根据查询语言显示

### 📝 Markdown格式支持
- **格式化输出**: 所有回答支持Markdown格式，便于网站渲染
- **丰富的格式元素**:
  - **粗体**强调重要概念
  - *斜体*标注专业术语
  - 有序列表和无序列表
  - `代码格式`标注技术术语
  - > 引用重要信息
  - ### 子标题组织内容结构
  - [链接](URL)格式的来源引用

### 🔤 UTF-8编码优化
- **字符编码修复**: HTTP响应头正确设置`charset=utf-8`
- **中文显示正常**: 解决网站集成时的中文乱码问题
- **多语言支持**: 完美支持中文、英文等多种语言字符

## 支持与反馈

如有问题或需要技术支持，请联系开发团队。API现已全面修复并正常运行在8010端口。