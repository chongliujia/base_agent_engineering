#!/usr/bin/env python3
"""
测试嵌入模型API调用
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import get_model_config

def test_embedding_api():
    """测试嵌入模型API调用"""
    try:
        print("🧪 测试嵌入模型API...")
        
        # 获取模型配置
        model_config = get_model_config()
        embedding_model = model_config.get_embedding_model()
        
        print(f"✅ 嵌入模型初始化成功: {type(embedding_model)}")
        
        # 测试单个文本
        test_text = "这是一个测试文本"
        print(f"🔤 测试文本: {test_text}")
        
        embeddings = embedding_model.embed_query(test_text)
        print(f"✅ 单文本嵌入成功，维度: {len(embeddings)}")
        
        # 测试文本列表
        test_texts = ["文本1", "文本2", "文本3"]
        print(f"📝 测试文本列表: {test_texts}")
        
        embeddings_list = embedding_model.embed_documents(test_texts)
        print(f"✅ 文本列表嵌入成功，数量: {len(embeddings_list)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 嵌入模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_embedding_api()
    sys.exit(0 if success else 1)