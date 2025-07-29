#!/bin/bash

# Base Agent Engineering 一键测试脚本
# 
# 使用方法:
#   chmod +x run_test.sh
#   ./run_test.sh

set -e  # 遇到错误立即退出

echo "🚀 Base Agent Engineering - 一键测试启动"
echo "=================================================="

# 检查是否在项目根目录
if [ ! -f "config/models.yaml" ]; then
    echo "❌ 错误：请在项目根目录运行此脚本"
    exit 1
fi

# 检查 .env 文件是否存在
if [ ! -f ".env" ]; then
    echo "❌ 错误：.env 文件不存在，请先创建并配置API密钥"
    echo "   可以复制 .env.example 文件并修改其中的API密钥"
    exit 1
fi

echo "✅ 环境检查通过"

# Python程序会自动加载.env文件，这里只做检查
echo "📋 检查.env文件内容..."

# 从.env文件读取并显示API密钥状态（不加载到shell环境）
dashscope_key=$(grep "^DASHSCOPE_API_KEY=" .env | cut -d'=' -f2)
openai_key=$(grep "^OPENAI_API_KEY=" .env | cut -d'=' -f2)

echo ""
echo "🔑 .env文件中的API密钥状态:"
if [ -n "$dashscope_key" ] && [ "$dashscope_key" != "your_dashscope_api_key_here" ]; then
    echo "   ✅ DASHSCOPE_API_KEY: 已设置"
else
    echo "   ❌ DASHSCOPE_API_KEY: 未设置或使用默认值"
fi

if [ -n "$openai_key" ] && [ "$openai_key" != "your_openai_api_key_here" ]; then
    echo "   ✅ OPENAI_API_KEY: 已设置"
else
    echo "   ⚠️  OPENAI_API_KEY: 未设置或使用默认值"
fi

# 检查Python环境
echo ""
echo "🐍 Python环境检查..."
if ! command -v python &> /dev/null; then
    echo "❌ Python未安装"
    exit 1
fi

python_version=$(python --version 2>&1)
echo "   ✅ Python版本: $python_version"

# 检查依赖包
echo ""
echo "📦 检查Python依赖..."
missing_packages=()

# 检查关键包
packages=("pydantic" "pydantic_settings" "langchain" "langchain_openai" "dashscope" "yaml")
for package in "${packages[@]}"; do
    if ! python -c "import $package" &> /dev/null; then
        missing_packages+=("$package")
    fi
done

if [ ${#missing_packages[@]} -gt 0 ]; then
    echo "❌ 缺少以下Python包: ${missing_packages[*]}"
    echo "   请运行: pip install -r requirements.txt"
    exit 1
fi

echo "   ✅ 所有依赖包已安装"

# 运行配置测试
echo ""
echo "🧪 运行配置测试..."
echo "--------------------------------------------------"

if python test_simple.py; then
    echo ""
    echo "✅ 配置测试通过!"
else
    echo ""
    echo "❌ 配置测试失败!"
    exit 1
fi

# 可选：运行完整的pytest测试
echo ""
echo "🔬 是否运行完整测试? (y/N)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "运行完整测试套件..."
    echo "--------------------------------------------------"
    
    if python -m pytest tests/unit/test_model_connections.py -v; then
        echo "✅ 完整测试通过!"
    else
        echo "⚠️  部分测试失败，但配置基本正常"
    fi
fi

echo ""
echo "=================================================="
echo "🎉 测试完成!"
echo ""
echo "💡 接下来你可以："
echo "   1. 运行示例：python examples/rerank_example.py"
echo "   2. 启动API服务：python main.py"
echo "   3. 运行特定测试：python -m pytest tests/unit/ -v"
echo ""
echo "📚 更多信息请查看 README.md"