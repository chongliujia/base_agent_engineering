#!/usr/bin/env python3
"""
简单的嵌入模型测试
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

def test_simple_embedding():
    """测试简单的嵌入API调用"""
    try:
        print("🧪 测试简单嵌入API...")
        
        # 检查API密钥
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            print("❌ DASHSCOPE_API_KEY 环境变量未设置")
            return False
        
        print(f"🔑 API Key: {api_key[:10]}...")
        
        # 直接使用OpenAI客户端
        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        print(f"✅ 客户端初始化成功")
        
        # 测试单个文本
        response = client.embeddings.create(
            model="text-embedding-v4",
            input="这是一个测试文本",
            dimensions=1024,
            encoding_format="float"
        )
        
        print(f"✅ API调用成功")
        print(f"📊 响应数据: {len(response.data)} 个嵌入向量")
        print(f"📏 向量维度: {len(response.data[0].embedding)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_embedding()
    exit(0 if success else 1)