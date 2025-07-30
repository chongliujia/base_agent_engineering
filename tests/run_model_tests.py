#!/usr/bin/env python3
"""
模型连接测试运行脚本
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """运行模型连接测试"""
    print("🚀 Base Agent Engineering - 模型连接测试")
    print("="*60)
    
    # 设置项目根目录
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # 检查Python路径
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # 检查必要的依赖
    try:
        import pytest
        import yaml
        import dashscope
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
        from langchain_community.vectorstores import Milvus
        print("✅ 所有依赖检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return 1
    
    # 检查配置文件
    config_file = project_root / "config" / "models.yaml"
    if not config_file.exists():
        print(f"❌ 配置文件不存在: {config_file}")
        return 1
    print(f"✅ 配置文件存在: {config_file}")
    
    print("\n🔑 环境变量检查:")
    api_keys_status = {
        "OPENAI_API_KEY": "✅ 已设置" if os.getenv("OPENAI_API_KEY") else "❌ 未设置",
        "DASHSCOPE_API_KEY": "✅ 已设置" if os.getenv("DASHSCOPE_API_KEY") else "❌ 未设置",
        "LANGSMITH_API_KEY": "✅ 已设置" if os.getenv("LANGSMITH_API_KEY") else "⚠️  未设置（可选）"
    }
    
    for key, status in api_keys_status.items():
        print(f"   {key}: {status}")
    
    if not any([os.getenv("OPENAI_API_KEY"), os.getenv("DASHSCOPE_API_KEY")]):
        print("\n⚠️  警告：至少需要设置 OPENAI_API_KEY 或 DASHSCOPE_API_KEY 中的一个来进行完整测试")
    
    print("\n🧪 运行模型连接测试...")
    print("-" * 40)
    
    # 运行直接的连接测试（不使用pytest）
    try:
        from tests.unit.test_model_connections import run_connection_tests
        run_connection_tests()
    except Exception as e:
        print(f"❌ 直接测试失败: {e}")
        print("\n🔄 尝试使用pytest运行测试...")
        
        # 使用pytest运行测试
        test_files = [
            "tests/unit/test_model_connections.py",
            "tests/unit/test_config.py"
        ]
        
        for test_file in test_files:
            if Path(test_file).exists():
                print(f"\n📋 运行 {test_file}...")
                try:
                    result = subprocess.run([
                        sys.executable, "-m", "pytest", 
                        test_file, 
                        "-v", 
                        "--tb=short",
                        "--no-header"
                    ], capture_output=True, text=True, cwd=project_root)
                    
                    if result.returncode == 0:
                        print(f"✅ {test_file} 测试通过")
                        print(result.stdout)
                    else:
                        print(f"❌ {test_file} 测试失败")
                        print("STDOUT:", result.stdout)
                        print("STDERR:", result.stderr)
                        
                except Exception as e:
                    print(f"❌ 运行pytest失败: {e}")
            else:
                print(f"⚠️  测试文件不存在: {test_file}")
    
    print("\n" + "="*60)
    print("🎯 测试完成！")
    
    # 显示使用建议
    print("\n💡 使用建议:")
    print("1. 确保设置了正确的API密钥环境变量")
    print("2. 如果测试失败，请检查网络连接和API配额")
    print("3. 可以单独运行特定测试: python -m pytest tests/unit/test_model_connections.py -v")
    print("4. 运行示例: python examples/rerank_example.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())