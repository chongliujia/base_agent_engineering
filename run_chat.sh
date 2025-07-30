#!/bin/bash

# RAG终端聊天程序启动脚本
# Usage: ./run_chat.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}🚀 启动RAG终端聊天程序...${NC}"
echo -e "${CYAN}================================${NC}"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 未安装或不在PATH中${NC}"
    exit 1
fi

# 检查是否在项目根目录
if [ ! -f "scripts/terminal_chat.py" ]; then
    echo -e "${RED}❌ 请在项目根目录下运行此脚本${NC}"
    exit 1
fi

# 检查依赖文件
echo -e "${BLUE}🔍 检查依赖文件...${NC}"

required_files=(
    "src/rag/workflow.py"
    "src/knowledge_base/knowledge_base_manager.py"
    "src/prompts/prompt_manager.py"
    "config/settings.py"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ 缺少必要文件: $file${NC}"
        exit 1
    fi
done

# 检查环境变量
echo -e "${BLUE}🔧 检查环境配置...${NC}"

if [ -f ".env" ]; then
    echo -e "${GREEN}✅ 找到.env配置文件${NC}"
else
    echo -e "${YELLOW}⚠️  未找到.env文件，将使用默认配置${NC}"
fi

# 检查关键环境变量
if [ -z "$TAVILY_API_KEY" ] && ! grep -q "TAVILY_API_KEY" .env 2>/dev/null; then
    echo -e "${YELLOW}⚠️  TAVILY_API_KEY未配置，网络搜索功能可能不可用${NC}"
fi

if [ -z "$DASHSCOPE_API_KEY" ] && ! grep -q "DASHSCOPE_API_KEY" .env 2>/dev/null; then
    echo -e "${YELLOW}⚠️  DASHSCOPE_API_KEY未配置，请确保已配置AI模型密钥${NC}"
fi

# 启动程序
echo -e "${GREEN}🎉 启动聊天程序...${NC}"
echo -e "${CYAN}================================${NC}"
echo

# 使用python3运行聊天程序
python3 scripts/terminal_chat.py

echo
echo -e "${CYAN}📊 程序已退出${NC}"