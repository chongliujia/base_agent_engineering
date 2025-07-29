#!/usr/bin/env python3
"""
简单的模型配置测试
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载环境变量（强制覆盖系统环境变量）
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file, override=True)  # override=True 会覆盖已存在的环境变量
    print(f"✅ 已加载环境变量文件并覆盖系统设置: {env_file}")
else:
    print(f"⚠️  环境变量文件不存在: {env_file}")

def test_configuration():
    """测试配置文件和模型加载"""
    print("🚀 简单配置测试")
    print("="*50)
    
    try:
        # 1. 测试配置文件加载
        print("1. 测试配置文件加载...")
        from config.settings import get_model_config, get_settings
        
        model_config = get_model_config()
        settings = get_settings()
        
        print("   ✅ 配置加载成功")
        
        # 2. 打印当前配置信息
        print("\n2. 当前配置信息:")
        config = model_config._config
        
        print(f"   聊天模型:")
        for name, model_info in config["chat_models"].items():
            print(f"     - {name}: {model_info['name']} ({model_info['provider']})")
        
        print(f"   嵌入模型:")
        for name, model_info in config["embedding_models"].items():
            print(f"     - {name}: {model_info['name']} ({model_info['provider']})")
        
        print(f"   重排序模型:")
        for name, model_info in config["reranking_models"].items():
            print(f"     - {name}: {model_info['name']} ({model_info['provider']})")
        
        # 3. 测试模型实例化（不调用API）
        print("\n3. 测试模型实例化...")
        
        # 测试聊天模型
        try:
            chat_model = model_config.get_chat_model("primary")
            print(f"   ✅ 聊天模型实例化成功: {type(chat_model).__name__}")
        except Exception as e:
            print(f"   ❌ 聊天模型实例化失败: {e}")
        
        # 测试嵌入模型
        try:
            embedding_model = model_config.get_embedding_model("primary")
            print(f"   ✅ 嵌入模型实例化成功: {type(embedding_model).__name__}")
        except Exception as e:
            print(f"   ❌ 嵌入模型实例化失败: {e}")
        
        # 测试重排序模型
        try:
            reranking_model = model_config.get_reranking_model("primary")
            print(f"   ✅ 重排序模型实例化成功: {type(reranking_model).__name__}")
        except Exception as e:
            print(f"   ❌ 重排序模型实例化失败: {e}")
        
        # 4. 测试环境变量
        print("\n4. 环境变量检查:")
        env_vars = {
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "DASHSCOPE_API_KEY": os.getenv("DASHSCOPE_API_KEY"),
            "LANGSMITH_API_KEY": os.getenv("LANGSMITH_API_KEY"),
        }
        
        for var_name, var_value in env_vars.items():
            if var_value:
                print(f"   ✅ {var_name}: 已设置 ({'sk-...' + var_value[-8:] if var_value.startswith('sk-') else '****'})")
            else:
                print(f"   ❌ {var_name}: 未设置")
        
        print("\n✅ 配置测试完成!")
        return True
        
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_connections():
    """测试API连接（如果有API密钥）"""
    print("\n🔌 API连接测试")
    print("="*50)
    
    from config.settings import get_model_config
    model_config = get_model_config()
    
    # 测试重排序模型（如果有DashScope密钥）
    if os.getenv("DASHSCOPE_API_KEY"):
        print("1. 测试DashScope重排序模型...")
        try:
            reranker = model_config.get_reranking_model("primary")
            
            query = "今天天气怎么样?"
            documents = [
                "机器学习是人工智能的一个分支",
                "今天天气很好",
                "深度学习是机器学习的子领域"
            ]
            
            results = reranker.rerank(query, documents, top_n=3)
            print(f"   ✅ 重排序成功，处理了 {len(results)} 个文档")
            for i, result in enumerate(results):
                print(f"      {i+1}. [分数: {result['relevance_score']:.3f}] {result['document'][:30]}...")
                
        except Exception as e:
            print(f"   ❌ 重排序测试失败: {e}")
    else:
        print("1. ⚠️  未设置DASHSCOPE_API_KEY，跳过重排序测试")
    
    # 测试聊天模型（如果配置了相应的密钥）
    config = model_config._config["chat_models"]["primary"]
    api_key_env = config.get("api_key_env", "")
    
    if api_key_env and os.getenv(api_key_env):
        print(f"2. 测试聊天模型 ({config['name']})...")
        try:
            from langchain_core.messages import HumanMessage
            chat_model = model_config.get_chat_model("primary")
            
            # 简单的测试消息
            messages = [HumanMessage(content="你是谁？")]
            response = chat_model.invoke(messages)
            print(f"   ✅ 聊天模型响应: {response.content[:50]}...")
            
        except Exception as e:
            print(f"   ❌ 聊天模型测试失败: {e}")
    else:
        print(f"2. ⚠️  未设置API密钥，跳过聊天模型测试")

if __name__ == "__main__":
    success = test_configuration()
    
    if success:
        test_api_connections()
    
    print("\n" + "="*50)
    print("🎯 测试完成!")