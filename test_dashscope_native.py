#!/usr/bin/env python3
"""
测试 DashScope 原生 API 调用
"""
import os
import json
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_dashscope_native_api():
    """测试 DashScope 原生 API"""
    print("🔍 测试 DashScope 原生 API...")
    
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("❌ DASHSCOPE_API_KEY 环境变量未设置")
        return False
    
    print(f"🔑 API Key: {api_key[:10]}...")
    
    # DashScope 原生 API 端点
    url = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 使用 contents 参数（DashScope 原生格式）
    data = {
        "model": "text-embedding-v4",
        "input": {
            "texts": ["测试文本"]
        },
        "parameters": {
            "text_type": "document"
        }
    }
    
    try:
        print("📤 发送请求到 DashScope 原生 API...")
        print(f"   URL: {url}")
        print(f"   Data: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        response = requests.post(url, headers=headers, json=data)
        
        print(f"📥 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ DashScope 原生 API 调用成功")
            print(f"📋 响应数据: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 检查嵌入向量
            if "output" in result and "embeddings" in result["output"]:
                embeddings = result["output"]["embeddings"]
                if embeddings and len(embeddings) > 0:
                    embedding = embeddings[0]["embedding"]
                    print(f"📏 向量维度: {len(embedding)}")
                    print(f"🎯 前5个值: {embedding[:5]}")
            
            return True
        else:
            print(f"❌ DashScope 原生 API 调用失败")
            print(f"   状态码: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_dashscope_openai_compatible():
    """测试 DashScope OpenAI 兼容模式"""
    print("\n🔍 测试 DashScope OpenAI 兼容模式...")
    
    api_key = os.getenv("DASHSCOPE_API_KEY")
    
    # OpenAI 兼容模式端点
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 使用 input 参数（OpenAI 兼容格式）
    data = {
        "model": "text-embedding-v4",
        "input": "测试文本",
        "encoding_format": "float"
    }
    
    try:
        print("📤 发送请求到 OpenAI 兼容模式...")
        print(f"   URL: {url}")
        print(f"   Data: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        response = requests.post(url, headers=headers, json=data)
        
        print(f"📥 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ OpenAI 兼容模式调用成功")
            print(f"📋 响应数据: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 检查嵌入向量
            if "data" in result and len(result["data"]) > 0:
                embedding = result["data"][0]["embedding"]
                print(f"📏 向量维度: {len(embedding)}")
                print(f"🎯 前5个值: {embedding[:5]}")
            
            return True
        else:
            print(f"❌ OpenAI 兼容模式调用失败")
            print(f"   状态码: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

if __name__ == "__main__":
    print("🧪 开始测试 DashScope API...")
    
    # 测试原生 API
    native_success = test_dashscope_native_api()
    
    # 测试 OpenAI 兼容模式
    compatible_success = test_dashscope_openai_compatible()
    
    print("\n" + "="*50)
    print("📊 测试结果总结:")
    print(f"   DashScope 原生 API: {'✅ 成功' if native_success else '❌ 失败'}")
    print(f"   OpenAI 兼容模式: {'✅ 成功' if compatible_success else '❌ 失败'}")
    
    if not native_success and not compatible_success:
        print("\n💡 建议:")
        print("   1. 检查 API 密钥是否正确")
        print("   2. 检查网络连接")
        print("   3. 查看 DashScope 官方文档确认 API 格式")