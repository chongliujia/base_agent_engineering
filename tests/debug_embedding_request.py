#!/usr/bin/env python3
"""
调试嵌入模型请求参数
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import OpenAIEmbeddings

# 加载环境变量
load_dotenv()

def debug_direct_api():
    """调试直接API调用"""
    print("🔍 调试直接API调用...")
    
    client = OpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    
    try:
        response = client.embeddings.create(
            model="text-embedding-v4",
            input="测试文本",
            dimensions=1024,
            encoding_format="float"
        )
        print("✅ 直接API调用成功")
        return True
    except Exception as e:
        print(f"❌ 直接API调用失败: {e}")
        return False

def debug_langchain_embedding():
    """调试LangChain嵌入模型"""
    print("🔍 调试LangChain嵌入模型...")
    
    # 创建LangChain嵌入模型
    embedding_model = OpenAIEmbeddings(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="text-embedding-v4",
        dimensions=1024,
        encoding_format="float"
    )
    
    print(f"📋 LangChain模型配置:")
    print(f"   API Key: {os.getenv('DASHSCOPE_API_KEY')[:10]}...")
    print(f"   Base URL: https://dashscope.aliyuncs.com/compatible-mode/v1")
    print(f"   Model: text-embedding-v4")
    print(f"   Dimensions: 1024")
    print(f"   Encoding Format: float")
    
    try:
        embeddings = embedding_model.embed_query("测试文本")
        print("✅ LangChain嵌入模型调用成功")
        print(f"📏 向量维度: {len(embeddings)}")
        return True
    except Exception as e:
        print(f"❌ LangChain嵌入模型调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def debug_with_different_params():
    """尝试不同的参数组合"""
    print("🔍 尝试不同的参数组合...")
    
    # 尝试不带dimensions参数
    print("\n1. 尝试不带dimensions参数:")
    try:
        embedding_model = OpenAIEmbeddings(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="text-embedding-v4"
        )
        embeddings = embedding_model.embed_query("测试文本")
        print("✅ 不带dimensions参数成功")
        print(f"📏 向量维度: {len(embeddings)}")
        return True
    except Exception as e:
        print(f"❌ 不带dimensions参数失败: {e}")
    
    # 尝试不带encoding_format参数
    print("\n2. 尝试不带encoding_format参数:")
    try:
        embedding_model = OpenAIEmbeddings(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="text-embedding-v4",
            dimensions=1024
        )
        embeddings = embedding_model.embed_query("测试文本")
        print("✅ 不带encoding_format参数成功")
        print(f"📏 向量维度: {len(embeddings)}")
        return True
    except Exception as e:
        print(f"❌ 不带encoding_format参数失败: {e}")
    
    # 尝试最简配置
    print("\n3. 尝试最简配置:")
    try:
        embedding_model = OpenAIEmbeddings(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="text-embedding-v4"
        )
        embeddings = embedding_model.embed_query("测试文本")
        print("✅ 最简配置成功")
        print(f"📏 向量维度: {len(embeddings)}")
        return True
    except Exception as e:
        print(f"❌ 最简配置失败: {e}")
    
    return False

if __name__ == "__main__":
    print("🧪 开始调试嵌入模型配置...")
    
    # 检查API密钥
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("❌ DASHSCOPE_API_KEY 环境变量未设置")
        exit(1)
    
    print(f"🔑 API Key: {api_key[:10]}...")
    
    # 调试直接API调用
    if debug_direct_api():
        print("\n" + "="*50)
        # 调试LangChain嵌入模型
        if not debug_langchain_embedding():
            print("\n" + "="*50)
            # 尝试不同参数组合
            debug_with_different_params()
    else:
        print("❌ 直接API调用失败，请检查API密钥和网络连接")