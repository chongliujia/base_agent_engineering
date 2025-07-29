#!/usr/bin/env python3
"""
测试修复后的嵌入模型配置
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import ModelConfig

# 加载环境变量
load_dotenv()

def test_dashscope_embedding():
    """测试DashScope嵌入模型"""
    print("🔍 测试修复后的DashScope嵌入模型...")
    
    try:
        # 初始化模型配置
        model_config = ModelConfig()
        
        # 获取嵌入模型
        embedding_model = model_config.get_embedding_model("primary")
        
        print(f"✅ 嵌入模型初始化成功")
        print(f"📋 模型类型: {type(embedding_model).__name__}")
        
        # 测试单个文本嵌入
        print("\n🧪 测试单个文本嵌入...")
        test_text = "这是一个测试文本"
        embedding = embedding_model.embed_query(test_text)
        
        print(f"✅ 单个文本嵌入成功")
        print(f"📏 向量维度: {len(embedding)}")
        print(f"🎯 前5个值: {embedding[:5]}")
        
        # 测试多个文本嵌入
        print("\n🧪 测试多个文本嵌入...")
        test_texts = [
            "这是第一个测试文本",
            "这是第二个测试文本",
            "这是第三个测试文本"
        ]
        embeddings = embedding_model.embed_documents(test_texts)
        
        print(f"✅ 多个文本嵌入成功")
        print(f"📊 嵌入数量: {len(embeddings)}")
        print(f"📏 每个向量维度: {len(embeddings[0])}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fallback_model():
    """测试fallback嵌入模型"""
    print("\n🔍 测试fallback嵌入模型...")
    
    try:
        # 初始化模型配置
        model_config = ModelConfig()
        
        # 获取fallback嵌入模型
        embedding_model = model_config.get_embedding_model("fallback")
        
        print(f"✅ fallback嵌入模型初始化成功")
        print(f"📋 模型类型: {type(embedding_model).__name__}")
        
        # 测试嵌入
        test_text = "这是fallback模型的测试文本"
        embedding = embedding_model.embed_query(test_text)
        
        print(f"✅ fallback模型嵌入成功")
        print(f"📏 向量维度: {len(embedding)}")
        
        return True
        
    except Exception as e:
        print(f"❌ fallback模型测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🧪 开始测试修复后的嵌入模型配置...")
    
    # 检查API密钥
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("❌ DASHSCOPE_API_KEY 环境变量未设置")
        exit(1)
    
    print(f"🔑 API Key: {api_key[:10]}...")
    
    # 测试主要模型
    primary_success = test_dashscope_embedding()
    
    # 测试fallback模型
    fallback_success = test_fallback_model()
    
    print("\n" + "="*50)
    print("📊 测试结果总结:")
    print(f"   Primary模型: {'✅ 成功' if primary_success else '❌ 失败'}")
    print(f"   Fallback模型: {'✅ 成功' if fallback_success else '❌ 失败'}")
    
    if primary_success and fallback_success:
        print("\n🎉 所有测试通过！现在可以运行原始脚本了。")
    else:
        print("\n💡 建议:")
        print("   1. 检查模型配置文件")
        print("   2. 确认API密钥正确")
        print("   3. 检查网络连接")