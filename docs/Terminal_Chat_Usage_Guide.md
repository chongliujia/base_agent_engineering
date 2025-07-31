# Terminal Chat Usage Guide

## Overview

The Terminal Chat is an interactive command-line interface for the RAG (Retrieval-Augmented Generation) system. It provides a direct way to interact with the intelligent chat system, supporting both knowledge base queries and web searches through a simple terminal interface.

## Features

- 💬 **Interactive Chat Interface**: Real-time conversation with the AI assistant
- 🔍 **Hybrid Search**: Combines knowledge base and web search capabilities
- 📚 **Multiple Knowledge Bases**: Switch between different knowledge collections
- ⚙️ **Configurable Settings**: Customizable search strategies and parameters
- 🌐 **Language Support**: Automatic language detection and response matching
- 📄 **Rich Output**: Formatted responses with source attribution
- 🔄 **Session Management**: Persistent conversation context

## Installation and Setup

### Prerequisites

- Python 3.9 or higher
- Required dependencies installed (`pip install -r requirements.txt`)
- Running RAG API service
- Configured environment variables

### Quick Start

1. **Ensure API Service is Running**
   ```bash
   # Start the RAG API service first
   python main.py
   ```

2. **Launch Terminal Chat**
   ```bash
   # Method 1: Using the script directly
   python scripts/terminal_chat.py
   
   # Method 2: Using the convenience script
   ./run_chat.sh
   
   # Method 3: With custom configuration
   python scripts/terminal_chat.py --host localhost --port 8010
   ```

## Usage Instructions

### Basic Commands

#### Starting a Conversation
```
=== RAG Terminal Chat ===
Connected to: http://localhost:8010
Type 'help' for commands, 'quit' to exit

You: Hello, how can you help me?
AI: Hello! I'm an intelligent assistant powered by a RAG system...
```

#### Available Commands

- **`help`** - Display available commands and usage information
- **`quit` / `exit`** - Exit the terminal chat
- **`clear`** - Clear the terminal screen
- **`status`** - Show current system status and configuration
- **`models`** - Display information about loaded models
- **`kb list`** - List all available knowledge bases
- **`kb switch <name>`** - Switch to a different knowledge base
- **`kb current`** - Show current knowledge base
- **`settings`** - Display current chat settings
- **`settings set <key> <value>`** - Modify chat settings

### Chat Modes

#### 1. Standard Chat Mode
```
You: What is machine learning?
AI: Machine learning is a subset of artificial intelligence (AI) that focuses on...

Sources:
📚 Knowledge Base: Introduction to ML concepts
🌐 Web Search: Latest ML developments from research papers
```

#### 2. Knowledge Base Only Mode
```
You: /kb What is our company policy on remote work?
AI: Based on our internal documentation...

Sources:
📚 Knowledge Base: Company HR Policies - Remote Work Guidelines
```

#### 3. Web Search Only Mode
```
You: /web What are the latest developments in AI this week?
AI: This week has seen several significant developments in AI...

Sources:
🌐 Web Search: TechCrunch - AI News
🌐 Web Search: MIT Technology Review - AI Breakthroughs
```

### Advanced Features

#### Knowledge Base Management

**List Available Knowledge Bases:**
```
You: kb list
Available Knowledge Bases:
1. ai_research (42 documents)
2. company_docs (156 documents) [CURRENT]
3. technical_specs (89 documents)
4. user_manuals (203 documents)
```

**Switch Knowledge Base:**
```
You: kb switch ai_research
Switched to knowledge base: ai_research
You can now query AI research documents specifically.
```

**Check Current Knowledge Base:**
```
You: kb current
Current Knowledge Base: ai_research
Documents: 42
Last Updated: 2025-07-30 14:23:15
```

#### Settings Configuration

**View Current Settings:**
```
You: settings
Current Settings:
- Search Strategy: hybrid
- Max KB Results: 5
- Max Web Results: 5
- Response Language: auto-detect
- Show Sources: true
- Streaming: false
```

**Modify Settings:**
```
You: settings set search_strategy knowledge_only
Search strategy updated to: knowledge_only

You: settings set max_results 10
Max results updated to: 10
```

#### System Information

**Check System Status:**
```
You: status
System Status: ✅ Healthy
API Endpoint: http://localhost:8010
Response Time: 1.2s
Connected: ✅
Knowledge Base: ✅ ai_research
Web Search: ✅ Enabled
Current Model: qwen-plus
```

**View Model Information:**
```
You: models
Loaded Models:
🤖 Chat Model: qwen-plus (LangChain OpenAI)
🔍 Embedding Model: text-embedding-v4
📊 Vector Store: Milvus
LangSmith Tracing: Disabled
```

### Query Examples

#### General Knowledge Queries
```
You: Explain quantum computing in simple terms
AI: Quantum computing is a revolutionary approach to computation that leverages...

Processing Time: 2.3s
Sources Used: 3 knowledge base + 2 web sources
```

#### Domain-Specific Queries
```
You: What are the best practices for RAG system implementation?
AI: Based on current research and best practices, here are the key recommendations...

**Key Best Practices:**
1. **Chunking Strategy**: Use semantic chunking for better context preservation
2. **Hybrid Search**: Combine vector similarity with keyword matching
3. **Reranking**: Implement cross-encoder reranking for improved relevance
...
```

#### Multi-Language Support
```
You: 什么是人工智能？
AI: 人工智能（Artificial Intelligence，AI）是计算机科学的一个分支...

You: What is artificial intelligence?
AI: Artificial Intelligence (AI) is a branch of computer science that aims to create...
```

## Configuration Options

### Environment Variables

```bash
# API Configuration
CHAT_API_HOST=localhost
CHAT_API_PORT=8010
CHAT_API_TIMEOUT=30

# Display Settings
CHAT_SHOW_SOURCES=true
CHAT_SHOW_TIMING=true
CHAT_MAX_HISTORY=50

# Default Behavior
CHAT_DEFAULT_STRATEGY=hybrid
CHAT_DEFAULT_KB=knowledge_base
CHAT_AUTO_LANGUAGE=true
```

### Command Line Arguments

```bash
python scripts/terminal_chat.py \
    --host localhost \
    --port 8010 \
    --timeout 30 \
    --kb ai_research \
    --strategy hybrid \
    --no-sources \
    --verbose
```

**Available Arguments:**
- `--host`: API server hostname (default: localhost)
- `--port`: API server port (default: 8010)
- `--timeout`: Request timeout in seconds (default: 30)
- `--kb`: Default knowledge base to use
- `--strategy`: Default search strategy (hybrid/knowledge_only/web_only)
- `--no-sources`: Hide source information in responses
- `--verbose`: Enable verbose logging
- `--config`: Path to custom configuration file

### Configuration File

**chat_config.yaml:**
```yaml
api:
  host: localhost
  port: 8010
  timeout: 30
  
display:
  show_sources: true
  show_timing: true
  max_history: 50
  colors: true
  
defaults:
  search_strategy: hybrid
  knowledge_base: ai_research
  max_kb_results: 5
  max_web_results: 5
  
language:
  auto_detect: true
  default: en
  supported: ["en", "zh", "es", "fr"]
```

## Troubleshooting

### Common Issues

#### Connection Issues
```
Error: Cannot connect to RAG API at http://localhost:8010

Solutions:
1. Ensure the API service is running: python main.py
2. Check if the port is correct: curl http://localhost:8010/health
3. Verify firewall settings
4. Try different host/port combination
```

#### Knowledge Base Issues
```
Error: Knowledge base 'ai_research' not found

Solutions:
1. List available knowledge bases: kb list
2. Create the knowledge base using CLI tools
3. Check knowledge base status in API
4. Verify collection names in Milvus
```

#### Response Quality Issues
```
Issue: Responses are not relevant or accurate

Solutions:
1. Try different search strategies
2. Switch to a more specific knowledge base
3. Rephrase your query with more context
4. Check if knowledge base contains relevant documents
5. Verify model configuration
```

### Debug Mode

**Enable Debug Logging:**
```bash
python scripts/terminal_chat.py --verbose --debug
```

**Debug Output Example:**
```
DEBUG: Sending request to /api/v1/chat
DEBUG: Query: "What is machine learning?"
DEBUG: Strategy: hybrid
DEBUG: KB: ai_research
DEBUG: Response received in 2.3s
DEBUG: Sources: 3 KB + 2 Web
```

### Performance Optimization

#### Tips for Better Performance

1. **Use Specific Knowledge Bases**: Switch to domain-specific KBs for better relevance
2. **Optimize Query Length**: Keep queries concise but descriptive
3. **Adjust Result Limits**: Reduce max_results for faster responses
4. **Use Appropriate Strategy**: Choose knowledge_only for internal docs, web_only for current events
5. **Cache Frequently Asked Questions**: The system automatically caches common queries

#### Performance Monitoring
```
You: perf stats
Performance Statistics:
Average Response Time: 2.1s
Cache Hit Rate: 67%
Knowledge Base Queries: 45
Web Search Queries: 23
Total Queries This Session: 68
```

## Integration Examples

### Batch Processing

**Process Multiple Queries:**
```bash
# Create a file with queries
echo "What is AI?" > queries.txt
echo "Explain machine learning" >> queries.txt
echo "How does deep learning work?" >> queries.txt

# Process batch queries
python scripts/terminal_chat.py --batch queries.txt --output results.txt
```

### API Integration

**Use Terminal Chat as a Testing Tool:**
```python
# test_chat_api.py
import subprocess
import json

def test_query(query):
    result = subprocess.run([
        'python', 'scripts/terminal_chat.py',
        '--query', query,
        '--json-output'
    ], capture_output=True, text=True)
    
    return json.loads(result.stdout)

# Test various queries
test_cases = [
    "What is artificial intelligence?",
    "Explain quantum computing",
    "Latest developments in robotics"
]

for query in test_cases:
    result = test_query(query)
    print(f"Query: {query}")
    print(f"Response: {result['response'][:100]}...")
    print(f"Sources: {len(result['sources'])}")
    print("-" * 50)
```

## Best Practices

### Query Formulation

1. **Be Specific**: "Explain the transformer architecture in deep learning" vs "What is AI?"
2. **Provide Context**: "In the context of our company's data pipeline, how should we implement..."
3. **Use Keywords**: Include relevant technical terms and domain-specific vocabulary
4. **Ask Follow-up Questions**: Build on previous responses for deeper understanding

### Session Management

1. **Use Descriptive Session Names**: Start with topic or project name
2. **Clear Context When Switching Topics**: Use `clear` command or start new session
3. **Save Important Responses**: Copy useful information to external notes
4. **Review Session History**: Use up/down arrows to recall previous queries

### Knowledge Base Usage

1. **Switch to Relevant KBs**: Use domain-specific knowledge bases for better results
2. **Keep KBs Updated**: Regularly update knowledge bases with new documents
3. **Organize by Domain**: Create separate KBs for different subjects or projects
4. **Monitor KB Performance**: Check which KBs provide the most relevant results

---

**Last Updated**: 2025-07-31
**Version**: 2.0
**Compatibility**: Python 3.9+, RAG API v1