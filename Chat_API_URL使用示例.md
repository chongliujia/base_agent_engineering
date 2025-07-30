# Chat API URL 使用示例

## 基础URL配置

**当前服务地址：** `http://localhost:8010`
**API版本：** v1
**基础URL：** `http://localhost:8010/api/v1`

## 1. 基础聊天接口

### URL: `POST /api/v1/chat`

**完整URL示例：**
```
POST http://localhost:8010/api/v1/chat
```

**cURL 命令示例：**

```bash
# 基础问答
curl -X POST "http://localhost:8010/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "什么是人工智能？"
  }'

# 指定知识库查询
curl -X POST "http://localhost:8010/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "介绍一下深度学习",
    "collection_name": "ai_research",
    "search_strategy": "knowledge_only"
  }'

# 仅使用网络搜索
curl -X POST "http://localhost:8010/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "今天的天气如何？",
    "search_strategy": "web_only",
    "max_web_results": 3
  }'
```

## 2. 流式聊天接口

### URL: `POST /api/v1/chat/stream`

**JavaScript 使用 fetch：**

```javascript
// 流式请求示例
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
          console.log('收到数据:', parsed);
        } catch (e) {
          // 忽略解析错误
        }
      }
    }
  }
}

// 使用示例
streamChat('请介绍一下量子计算');
```

**Server-Sent Events 示例：**

```html
<!DOCTYPE html>
<html>
<head>
    <title>流式聊天示例</title>
</head>
<body>
    <div id="messages"></div>
    <button onclick="startStreamChat()">开始流式对话</button>

    <script>
        function startStreamChat() {
            // 注意：EventSource 不支持 POST，需要使用 fetch
            fetch('http://localhost:8010/api/v1/chat/stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: '请详细介绍机器学习的发展历程',
                    stream: true
                })
            }).then(response => {
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                
                function read() {
                    return reader.read().then(({ value, done }) => {
                        if (done) return;
                        
                        const chunk = decoder.decode(value);
                        const lines = chunk.split('\n');
                        
                        lines.forEach(line => {
                            if (line.startsWith('data: ')) {
                                const data = line.slice(6);
                                if (data !== '[DONE]') {
                                    try {
                                        const parsed = JSON.parse(data);
                                        displayMessage(parsed);
                                    } catch (e) {}
                                }
                            }
                        });
                        
                        return read();
                    });
                }
                
                return read();
            });
        }
        
        function displayMessage(data) {
            const div = document.getElementById('messages');
            div.innerHTML += `<p>${data.type}: ${data.message || data.response || ''}</p>`;
        }
    </script>
</body>
</html>
```

## 3. 测试接口

### URL: `POST /api/chat/test`

**简单测试示例：**

```bash
# 基础测试
curl -X POST "http://localhost:8000/api/chat/test" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "测试问题：1+1等于几？"
  }'
```

**JavaScript 测试：**

```javascript
// 测试函数
async function testChat() {
  try {
    const response = await fetch('http://localhost:8000/api/chat/test', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: '请简单介绍一下你的功能'
      })
    });

    const result = await response.json();
    console.log('测试结果:', result);
    
    if (result.status === 'success') {
      console.log('AI回答:', result.response);
      console.log('检索到的知识库文档数:', result.knowledge_retrieved);
      console.log('检索到的网络结果数:', result.web_retrieved);
      console.log('处理时间:', result.processing_time, '秒');
    } else {
      console.error('测试失败:', result.error);
    }
  } catch (error) {
    console.error('请求失败:', error);
  }
}

// 执行测试
testChat();
```

## 4. 知识库管理接口

### 获取知识库列表

**URL: `GET /api/knowledge-bases`**

```bash
# 获取所有知识库
curl -X GET "http://localhost:8000/api/knowledge-bases"
```

```javascript
// JavaScript 获取知识库列表
async function getKnowledgeBases() {
  const response = await fetch('http://localhost:8000/api/knowledge-bases');
  const kbs = await response.json();
  
  console.log('可用知识库:');
  kbs.forEach(kb => {
    console.log(`- ${kb.name}: ${kb.document_count} 个文档`);
  });
  
  return kbs;
}

getKnowledgeBases();
```

### 切换知识库

**URL: `POST /api/switch-kb/{collection_name}`**

```bash
# 切换到指定知识库
curl -X POST "http://localhost:8000/api/switch-kb/ai_knowledge"

# 切换到另一个知识库
curl -X POST "http://localhost:8000/api/switch-kb/tech_docs"
```

```javascript
// JavaScript 切换知识库
async function switchKnowledgeBase(kbName) {
  const response = await fetch(`http://localhost:8000/api/switch-kb/${kbName}`, {
    method: 'POST'
  });
  
  const result = await response.json();
  console.log(result.message);
  return result;
}

// 使用示例
switchKnowledgeBase('ai_knowledge');
```

## 5. 提示词管理接口

### 获取提示词列表

**URL: `GET /api/prompts`**

```bash
# 获取所有提示词
curl -X GET "http://localhost:8000/api/prompts"

# 按类别获取提示词
curl -X GET "http://localhost:8000/api/prompts?category=technical"
```

### 添加自定义提示词

**URL: `POST /api/prompts/{prompt_name}`**

```bash
curl -X POST "http://localhost:8000/api/prompts/my_custom_prompt" \
  -H "Content-Type: application/json" \
  -d '{
    "version": "1.0",
    "description": "自定义技术问答提示词",
    "template": "你是一个专业的技术顾问，请详细回答以下技术问题：{query}",
    "variables": ["query"],
    "category": "technical"
  }'
```

## 6. 健康检查接口

### URL: `GET /api/health`

```bash
# 检查服务状态
curl -X GET "http://localhost:8000/api/health"
```

```javascript
// JavaScript 健康检查
async function checkHealth() {
  try {
    const response = await fetch('http://localhost:8000/api/health');
    const health = await response.json();
    
    console.log('服务状态:', health.status);
    console.log('当前知识库:', health.current_kb);
    console.log('组件状态:', health.components);
    
    return health.status === 'healthy';
  } catch (error) {
    console.error('健康检查失败:', error);
    return false;
  }
}

checkHealth();
```

## 7. 完整的网站集成示例

### HTML + JavaScript 完整示例

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI助手 - URL集成示例</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .container { display: grid; grid-template-columns: 1fr 2fr; gap: 20px; }
        .controls { background: #f5f5f5; padding: 20px; border-radius: 8px; }
        .chat-area { background: white; border: 1px solid #ddd; border-radius: 8px; }
        .messages { height: 400px; overflow-y: auto; padding: 20px; }
        .message { margin-bottom: 15px; padding: 10px; border-radius: 5px; }
        .user { background: #e3f2fd; text-align: right; }
        .ai { background: #f5f5f5; }
        .input-area { padding: 20px; border-top: 1px solid #ddd; }
        .input-group { display: flex; gap: 10px; margin-bottom: 10px; }
        select, input, button { padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        button { background: #2196f3; color: white; cursor: pointer; }
        button:hover { background: #1976d2; }
        .status { font-size: 12px; color: #666; margin-top: 10px; }
    </style>
</head>
<body>
    <h1>AI助手 - URL使用示例</h1>
    
    <div class="container">
        <!-- 控制面板 -->
        <div class="controls">
            <h3>API配置</h3>
            <div class="input-group">
                <label>API基础URL:</label>
                <input type="text" id="apiUrl" value="http://localhost:8000/api" style="width: 100%;">
            </div>
            
            <div class="input-group">
                <label>知识库:</label>
                <select id="knowledgeBase">
                    <option value="">默认</option>
                </select>
                <button onclick="loadKnowledgeBases()">刷新</button>
            </div>
            
            <div class="input-group">
                <label>搜索策略:</label>
                <select id="searchStrategy">
                    <option value="both">知识库+网络</option>
                    <option value="knowledge_only">仅知识库</option>
                    <option value="web_only">仅网络搜索</option>
                </select>
            </div>
            
            <div class="input-group">
                <label>响应方式:</label>
                <select id="responseType">
                    <option value="normal">普通响应</option>
                    <option value="stream">流式响应</option>
                    <option value="test">测试接口</option>
                </select>
            </div>
            
            <button onclick="checkApiHealth()">检查API状态</button>
            <div id="healthStatus" class="status"></div>
        </div>
        
        <!-- 聊天区域 -->
        <div class="chat-area">
            <div id="messages" class="messages"></div>
            <div class="input-area">
                <div class="input-group">
                    <input type="text" id="messageInput" placeholder="请输入您的问题..." style="flex: 1;">
                    <button onclick="sendMessage()">发送</button>
                </div>
                <div id="status" class="status"></div>
            </div>
        </div>
    </div>

    <script>
        class ChatAPIClient {
            constructor() {
                this.baseUrl = document.getElementById('apiUrl').value;
            }
            
            updateBaseUrl() {
                this.baseUrl = document.getElementById('apiUrl').value;
            }
            
            async request(endpoint, options = {}) {
                this.updateBaseUrl();
                const url = `${this.baseUrl}${endpoint}`;
                
                const config = {
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers
                    },
                    ...options
                };
                
                console.log(`🌐 请求URL: ${url}`);
                console.log(`📋 请求配置:`, config);
                
                const response = await fetch(url, config);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                return response;
            }
            
            async chat(query, options = {}) {
                const response = await this.request('/chat', {
                    method: 'POST',
                    body: JSON.stringify({
                        query,
                        collection_name: options.collection_name || null,
                        search_strategy: options.search_strategy || 'both',
                        ...options
                    })
                });
                
                return await response.json();
            }
            
            async chatTest(query) {
                const response = await this.request('/chat/test', {
                    method: 'POST',
                    body: JSON.stringify({ query })
                });
                
                return await response.json();
            }
            
            async chatStream(query, options = {}) {
                const response = await this.request('/chat/stream', {
                    method: 'POST',
                    body: JSON.stringify({
                        query,
                        stream: true,
                        ...options
                    })
                });
                
                return response;
            }
            
            async getKnowledgeBases() {
                const response = await this.request('/knowledge-bases');
                return await response.json();
            }
            
            async switchKnowledgeBase(kbName) {
                const response = await this.request(`/switch-kb/${kbName}`, {
                    method: 'POST'
                });
                return await response.json();
            }
            
            async checkHealth() {
                const response = await this.request('/health');
                return await response.json();
            }
        }
        
        const api = new ChatAPIClient();
        
        function addMessage(content, isUser = false, isSystem = false) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user' : isSystem ? 'system' : 'ai'}`;
            messageDiv.innerHTML = content;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function updateStatus(message) {
            document.getElementById('status').textContent = message;
        }
        
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const query = input.value.trim();
            if (!query) return;
            
            const knowledgeBase = document.getElementById('knowledgeBase').value;
            const searchStrategy = document.getElementById('searchStrategy').value;
            const responseType = document.getElementById('responseType').value;
            
            addMessage(query, true);
            input.value = '';
            updateStatus('正在处理...');
            
            try {
                const options = {
                    collection_name: knowledgeBase || null,
                    search_strategy: searchStrategy
                };
                
                if (responseType === 'test') {
                    const result = await api.chatTest(query);
                    addMessage(`
                        <strong>回答:</strong> ${result.response}<br>
                        <small>
                            状态: ${result.status}<br>
                            知识库检索: ${result.knowledge_retrieved} 条<br>
                            网络检索: ${result.web_retrieved} 条<br>
                            处理时间: ${result.processing_time.toFixed(2)}秒
                        </small>
                    `);
                    
                } else if (responseType === 'stream') {
                    const response = await api.chatStream(query, options);
                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    
                    let messageDiv = null;
                    
                    while (true) {
                        const { value, done } = await reader.read();
                        if (done) break;
                        
                        const chunk = decoder.decode(value);
                        const lines = chunk.split('\n');
                        
                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                const data = line.slice(6);
                                if (data === '[DONE]') break;
                                
                                try {
                                    const parsed = JSON.parse(data);
                                    
                                    if (parsed.type === 'start' || parsed.type === 'progress') {
                                        updateStatus(parsed.message);
                                    } else if (parsed.type === 'complete') {
                                        if (!messageDiv) {
                                            addMessage('');
                                            messageDiv = document.querySelector('#messages .message:last-child');
                                        }
                                        messageDiv.innerHTML = `
                                            <strong>回答:</strong> ${parsed.response}<br>
                                            <small>
                                                知识库检索: ${parsed.metadata.knowledge_retrieved} 条<br>
                                                网络检索: ${parsed.metadata.web_retrieved} 条
                                            </small>
                                        `;
                                    } else if (parsed.type === 'error') {
                                        addMessage(`<span style="color: red;">错误: ${parsed.message}</span>`);
                                    }
                                } catch (e) {
                                    // 忽略解析错误
                                }
                            }
                        }
                    }
                    
                } else {
                    const result = await api.chat(query, options);
                    let sourcesHtml = '';
                    
                    if (result.sources.knowledge_base.length > 0) {
                        sourcesHtml += '<br><strong>知识库来源:</strong><br>';
                        result.sources.knowledge_base.forEach(source => {
                            sourcesHtml += `📚 ${source.content.substring(0, 100)}...<br>`;
                        });
                    }
                    
                    if (result.sources.web_search.length > 0) {
                        sourcesHtml += '<br><strong>网络来源:</strong><br>';
                        result.sources.web_search.forEach(source => {
                            sourcesHtml += `🔍 <a href="${source.url}" target="_blank">${source.title}</a><br>`;
                        });
                    }
                    
                    addMessage(`
                        <strong>回答:</strong> ${result.response}
                        ${sourcesHtml}
                        <br><small>处理时间: ${result.processing_time.toFixed(2)}秒</small>
                    `);
                }
                
                updateStatus('完成');
                
            } catch (error) {
                console.error('请求失败:', error);
                addMessage(`<span style="color: red;">错误: ${error.message}</span>`);
                updateStatus('错误');
            }
        }
        
        async function loadKnowledgeBases() {
            try {
                const kbs = await api.getKnowledgeBases();
                const select = document.getElementById('knowledgeBase');
                
                // 清空现有选项（保留默认选项）
                while (select.children.length > 1) {
                    select.removeChild(select.lastChild);
                }
                
                // 添加知识库选项
                kbs.forEach(kb => {
                    const option = document.createElement('option');
                    option.value = kb.collection_name;
                    option.textContent = `${kb.name} (${kb.document_count}个文档)`;
                    select.appendChild(option);
                });
                
                updateStatus(`已加载 ${kbs.length} 个知识库`);
                
            } catch (error) {
                console.error('加载知识库失败:', error);
                updateStatus('加载知识库失败');
            }
        }
        
        async function checkApiHealth() {
            try {
                const health = await api.checkHealth();
                const statusDiv = document.getElementById('healthStatus');
                
                let statusHtml = `<strong>状态:</strong> ${health.status}<br>`;
                statusHtml += `<strong>当前知识库:</strong> ${health.current_kb}<br>`;
                statusHtml += '<strong>组件状态:</strong><br>';
                
                Object.entries(health.components).forEach(([component, status]) => {
                    const icon = status === 'ok' ? '✅' : '❌';
                    statusHtml += `${icon} ${component}: ${status}<br>`;
                });
                
                statusDiv.innerHTML = statusHtml;
                
            } catch (error) {
                document.getElementById('healthStatus').innerHTML = 
                    `<span style="color: red;">健康检查失败: ${error.message}</span>`;
            }
        }
        
        // 页面加载时的初始化
        document.addEventListener('DOMContentLoaded', function() {
            loadKnowledgeBases();
            checkApiHealth();
            
            // 回车发送消息
            document.getElementById('messageInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        });
    </script>
</body>
</html>
```

## 8. 不同环境的URL配置

### 当前开发环境（推荐）
```javascript
const API_BASE_URL = 'http://localhost:8010/api/v1';
```

### 生产环境
```javascript
const API_BASE_URL = 'https://your-domain.com/api/v1';
```

### Docker 部署
```javascript
const API_BASE_URL = 'http://your-server-ip:8010/api/v1';
```

### 带认证的环境
```javascript
const headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer your-token-here'
};
```

## 快速验证命令

```bash
# 验证服务是否正常运行
curl http://localhost:8010/health

# 测试聊天功能
curl -X POST "http://localhost:8010/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello", "search_strategy": "web_only", "max_web_results": 1}'
```

## 当前服务状态

- ✅ **服务地址**: http://localhost:8010
- ✅ **所有接口**: 已修复并测试通过
- ✅ **聊天功能**: 正常（支持混合检索）
- ✅ **流式响应**: 正常
- ✅ **模型信息**: 正常
- ✅ **知识库管理**: 正常

使用这些示例，你可以快速集成Chat API到你的网站中。当前服务运行在8010端口，所有功能都已验证可用。