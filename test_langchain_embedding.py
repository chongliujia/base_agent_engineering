#!/usr/bin/env python3
"""
测试LangChain嵌入模型配置
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 加载环境变量
load_dotenv()

from config.settings import get_model_config

def test_langchain_embedding():
    """测试LangChain嵌入模型配置"""
    try:
        print("🧪 测试LangChain嵌入模型...")
        
        # 获取模型配置
        model_config = get_model_config()
        print(f"✅ 模型配置加载成功")
        
        # 获取嵌入模型
        embedding_model = model_config.get_embedding_model()
        print(f"✅ 嵌入模型初始化成功: {type(embedding_model)}")
        
        # 打印模型配置信息
        print(f"📋 模型配置信息:")
        embedding_config = model_config._config["embedding_models"]["primary"]
        print(f"   模型名称: {embedding_config['name']}")
        print(f"   提供商: {embedding_config['provider']}")
        print(f"   Base URL: {embedding_config.get('base_url', 'N/A')}")
        print(f"   API Key环境变量: {embedding_config['api_key_env']}")
        
        # 测试单个文本嵌入
        test_text = "这是一个测试文本"
        print(f"🔤 测试文本: {test_text}")
        
        embeddings = embedding_model.embed_query(test_text)
        print(f"✅ 单文本嵌入成功，维度: {len(embeddings)}")
        
        # 测试文本列表嵌入
        test_texts = ["文本1", "文本2", "文本3"]
        print(f"📝 测试文本列表: {test_texts}")
        
        embeddings_list = embedding_model.embed_documents(test_texts)
        print(f"✅ 文本列表嵌入成功，数量: {len(embeddings_list)}")
        print(f"📏 每个向量维度: {len(embeddings_list[0])}")
        
        return True
        
    except Exception as e:
        print(f"❌ LangChain嵌入模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_langchain_embedding()
    sys.exit(0 if success else 1)