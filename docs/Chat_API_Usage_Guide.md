# Chat API Usage Guide

## Overview

The Chat API is an intelligent conversation interface based on LangChain and LangGraph, supporting knowledge base retrieval and web search functionality. This API can be integrated into websites to provide intelligent Q&A services for users.

## Basic Information

- **Current Service Address**: `http://localhost:8010`
- **API Version**: v1
- **Base URL**: `http://localhost:8010/api/v1`
- **Protocol**: HTTP/HTTPS
- **Request Format**: JSON
- **Response Format**: JSON
- **Supported Model**: Qwen Plus (qwen-plus)
- **Vector Storage**: Milvus

## Main Endpoints

### 1. Chat Conversation API

#### POST `/api/v1/chat`

Main chat interface supporting intelligent Q&A, knowledge base retrieval, and web search. Implements hybrid retrieval strategy based on LangGraph workflow.

**Request Parameters**:

```json
{
  "query": "string",           // Required: User question (1-1000 characters)
  "collection_name": "string", // Optional: Specify knowledge base collection name
  "search_strategy": "string", // Optional: Retrieval strategy (knowledge_only/web_only/both, default: both)
  "prompt_template": "string", // Optional: Custom prompt template name
  "stream": false,            // Optional: Whether to use streaming response (default: false)
  "max_web_results": 5,       // Optional: Max web search results (1-10, default: 5)
  "max_kb_results": 5         // Optional: Max knowledge base retrieval results (1-10, default: 5)
}
```

**Response Format**:

```json
{
  "query": "string",          // User question
  "response": "string",       // AI response
  "sources": {                // Source information
    "knowledge_base": [       // Knowledge base sources
      {
        "content": "string",
        "metadata": {},
        "relevance_score": 0.8
      }
    ],
    "web_search": [           // Web search sources
      {
        "title": "string",
        "content": "string",
        "url": "string",
        "score": 0.9
      }
    ]
  },
  "metadata": {               // Metadata
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

### 2. Streaming Chat API

#### POST `/api/v1/chat/stream`

Supports Server-Sent Events streaming response, returning processing progress in real-time. Suitable for scenarios requiring real-time feedback.

**Usage Example**:

```javascript
// Streaming request example (using fetch)
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
              console.log('Started processing:', parsed.message);
              break;
            case 'progress':
              console.log('Processing progress:', parsed.message);
              break;
            case 'complete':
              console.log('Completed:', parsed.response);
              break;
            case 'error':
              console.error('Error:', parsed.message);
              break;
          }
        } catch (e) {
          // Ignore parsing errors
        }
      }
    }
  }
}
```

### 3. Model Information API

#### GET `/api/v1/models`

Get information about currently loaded models and configuration.

**Response Format**:

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

### 4. Knowledge Base Management API

#### GET `/api/v1/knowledge-bases`

Get list of all available knowledge bases.

**Response Format**:

```json
[
  {
    "name": "ai_research",
    "description": "Knowledge base ai_research",
    "document_count": 0,
    "collection_name": "ai_research",
    "last_updated": ""
  },
  {
    "name": "knowledge_base",
    "description": "Knowledge base knowledge_base", 
    "document_count": 0,
    "collection_name": "knowledge_base",
    "last_updated": ""
  }
]
```

#### POST `/api/v1/switch-kb/{collection_name}`

Switch the currently used knowledge base.

**Response Format**:

```json
{
  "message": "Switched to knowledge base: collection_name",
  "current_kb": "collection_name",
  "timestamp": "2025-07-31T00:00:00"
}
```

### 5. Health Check API

#### GET `/health`

Check API service status. (Note: This endpoint is at root path, not under /api/v1)

**Response Format**:

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

Detailed health check interface (under API path).

**Response Format**:

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

## Website Integration Example

### JavaScript Example

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

// Usage example
const chatAPI = new ChatAPI('http://localhost:8010/api/v1');

// Send message
chatAPI.sendMessage('Hello, please introduce your features')
  .then(response => {
    console.log('AI response:', response.response);
    console.log('Source information:', response.sources);
    console.log('Processing time:', response.processing_time);
  })
  .catch(error => {
    console.error('Error:', error);
  });

// Get model information
chatAPI.getModels()
  .then(models => {
    console.log('Current model:', models.chat_model.name);
    console.log('Vector storage:', models.vector_store);
  });
```

## Error Handling

Common HTTP status codes and error handling:

- `200`: Success
- `400`: Bad request parameters
- `404`: Resource not found (e.g., knowledge base doesn't exist)
- `500`: Internal server error

Error response format:

```json
{
  "detail": "Error description message"
}
```

## Best Practices

1. **Request Rate Limiting**: Recommend controlling request frequency to avoid excessive API calls
2. **Error Retry**: Implement appropriate error retry mechanisms
3. **Timeout Settings**: Set reasonable request timeout (recommend 30 seconds)
4. **Caching Strategy**: Consider client-side caching for repeated queries
5. **Streaming Response**: Use streaming interface for long-processing queries

## Configuration

Before use, ensure the following configurations are correct:

1. **API Keys**: Ensure necessary API keys are configured (e.g., search engine API)
2. **Knowledge Base**: Upload and configure knowledge base documents
3. **Prompts**: Configure appropriate prompt templates according to business requirements

## Quick Test Commands

Here are some test commands you can use immediately:

```bash
# 1. Health check
curl http://localhost:8010/health

# 2. Get model information
curl http://localhost:8010/api/v1/models

# 3. Get knowledge base list
curl http://localhost:8010/api/v1/knowledge-bases

# 4. Basic chat test
curl -X POST "http://localhost:8010/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello, introduce yourself", "search_strategy": "web_only"}'

# 5. Streaming chat test
curl -X POST "http://localhost:8010/api/v1/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is artificial intelligence?", "stream": true}' \
  --no-buffer -N

# 6. English query test (automatic language adaptation)
curl -X POST "http://localhost:8010/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "search_strategy": "web_only"}'
```

## Current Configuration Status

- **Service Port**: 8010
- **Chat Model**: qwen-plus (Qwen Plus)
- **Embedding Model**: text-embedding-v4
- **Vector Database**: Milvus
- **Available Knowledge Bases**: 5 (ai_research, knowledge_base, metadata, strategy_test, strategy_test_auto)
- **Web Search**: Enabled (Tavily)
- **LangSmith Tracing**: Disabled
- **Language Adaptation**: ✅ Enabled (automatically detects user language and matches response language)
- **Markdown Support**: ✅ Enabled (supports formatted output)
- **Character Encoding**: UTF-8 (Chinese display issues fixed)

## New Features

### 🌐 Intelligent Language Adaptation
- **Automatic Language Detection**: System automatically detects query language (Chinese/English, etc.)
- **Matching Language Response**: English queries return English responses, Chinese queries return Chinese responses
- **Streaming Message Adaptation**: Progress messages in streaming responses also display according to query language

### 📝 Markdown Format Support
- **Formatted Output**: All responses support Markdown format for easy website rendering
- **Rich Format Elements**:
  - **Bold** for emphasizing important concepts
  - *Italics* for marking technical terms
  - Ordered and unordered lists
  - `Code format` for technical terminology
  - > Quotes for important information
  - ### Subheadings for content structure organization
  - [Link](URL) format for source references

### 🔤 UTF-8 Encoding Optimization
- **Character Encoding Fix**: HTTP response headers correctly set `charset=utf-8`
- **Normal Chinese Display**: Solves Chinese character garbling issues in website integration
- **Multi-language Support**: Perfect support for Chinese, English and other multi-language characters

## Support & Feedback

For questions or technical support, please contact the development team. The API has been fully fixed and is now running normally on port 8010.