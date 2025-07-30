"""
提示词管理系统 - 支持可配置和模板化的提示词
"""

import json
import yaml
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict

from config.settings import get_settings


@dataclass
class PromptTemplate:
    """提示词模板"""
    name: str
    version: str
    description: str
    template: str
    variables: List[str]
    category: str = "general"
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def render(self, **kwargs) -> str:
        """渲染提示词模板"""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            missing_var = str(e).strip("'")
            raise ValueError(f"模板变量缺失: {missing_var}. 需要的变量: {self.variables}")


class PromptManager:
    """提示词管理器"""
    
    def __init__(self, prompts_dir: str = None):
        self.settings = get_settings()
        self.prompts_dir = Path(prompts_dir or "config/prompts")
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        
        # 内置提示词模板
        self.built_in_prompts = {}
        self._load_built_in_prompts()
        
        # 用户自定义提示词
        self.custom_prompts = {}
        self._load_custom_prompts()
    
    def _load_built_in_prompts(self):
        """加载内置提示词模板"""
        
        # RAG问答提示词（支持Markdown）
        self.built_in_prompts["rag_qa"] = PromptTemplate(
            name="rag_qa",
            version="1.0",
            description="基于知识库和网络搜索的问答提示词，支持Markdown格式",
            template="""你是一个专业的AI助手，能够基于知识库文档和网络搜索结果回答用户问题。

## 上下文信息

### 知识库检索结果：
{knowledge_context}

### 网络搜索结果：
{web_context}

## 回答要求

1. **准确性优先**：基于提供的上下文信息进行回答
2. **信息融合**：综合知识库和网络搜索的信息
3. **引用来源**：明确标注信息来源
4. **结构化回答**：使用清晰的段落和要点
5. **诚实回应**：如果信息不足，请诚实说明
6. **Markdown格式**：请使用Markdown语法来优化回答格式：
   - 使用 **粗体** 强调重要概念
   - 使用 *斜体* 标注专业术语
   - 使用有序列表 (1. 2. 3.) 或无序列表 (- ) 组织信息
   - 使用 `代码格式` 标注技术术语
   - 使用 > 引用重要信息
   - 使用 ### 子标题组织内容结构

## 用户问题：
{query}

## 回答：
请基于上述上下文信息，使用Markdown格式为用户提供准确、全面且格式优美的回答。""",
            variables=["knowledge_context", "web_context", "query"],
            category="rag"
        )
        
        # 纯知识库问答（支持Markdown）
        self.built_in_prompts["knowledge_only"] = PromptTemplate(
            name="knowledge_only", 
            version="1.0",
            description="仅基于知识库的问答提示词，支持Markdown格式",
            template="""你是一个专业的文档助手，专门基于知识库中的文档内容回答用户问题。

## 知识库上下文：
{knowledge_context}

## 回答指南：
- 严格基于提供的文档内容进行回答
- 如果文档中没有相关信息，请明确说明
- 引用具体的文档片段支持你的回答
- 保持回答的准确性和专业性
- **使用Markdown格式**优化回答展示：
  - 使用 **粗体** 强调关键概念
  - 使用 *斜体* 标注文档来源
  - 使用列表组织信息要点
  - 使用 > 引用文档原文
  - 使用 ### 组织答案结构

## 用户问题：
{query}

## 基于文档的回答：""",
            variables=["knowledge_context", "query"],
            category="knowledge"
        )
        
        # 网络搜索问答（支持Markdown）
        self.built_in_prompts["web_only"] = PromptTemplate(
            name="web_only",
            version="1.0", 
            description="仅基于网络搜索的问答提示词，支持Markdown格式",
            template="""你是一个信息研究助手，基于最新的网络搜索结果回答用户问题。

## 网络搜索结果：
{web_context}

## 回答要求：
- 基于搜索结果提供最新、准确的信息
- 综合多个来源的信息
- 标注信息的来源链接
- 注意信息的时效性和可靠性
- **使用Markdown格式**优化回答展示：
  - 使用 **粗体** 强调重要信息
  - 使用 *斜体* 标注来源网站
  - 使用列表组织多个信息点
  - 使用 [链接文本](URL) 格式提供来源链接
  - 使用 ### 组织答案结构

## 用户问题：
{query}

## 基于搜索结果的回答：""",
            variables=["web_context", "query"],
            category="web"
        )
        
        # 查询分析提示词
        self.built_in_prompts["query_analysis"] = PromptTemplate(
            name="query_analysis",
            version="1.0",
            description="用于分析用户查询意图和类型",
            template="""请分析以下用户查询，确定其类型和检索策略。

## 用户查询：
{query}

## 分析维度：
1. **查询类型**：事实性、分析性、操作性、概念性
2. **时效性需求**：是否需要最新信息
3. **复杂度**：简单、中等、复杂
4. **领域**：技术、商业、生活、学术等
5. **推荐策略**：knowledge_only、web_only、both

请以JSON格式返回分析结果：
{{
    "query_type": "类型",
    "needs_realtime": true/false,
    "complexity": "简单/中等/复杂",
    "domain": "领域",
    "recommended_strategy": "策略",
    "keywords": ["关键词1", "关键词2"],
    "reasoning": "分析理由"
}}""",
            variables=["query"],
            category="analysis"
        )
        
        # 信息融合提示词
        self.built_in_prompts["information_fusion"] = PromptTemplate(
            name="information_fusion",
            version="1.0",
            description="用于融合多源信息",
            template="""请将以下来自不同来源的信息进行整合和去重。

## 知识库信息：
{knowledge_info}

## 网络搜索信息：
{web_info}

## 融合要求：
1. 去除重复信息
2. 解决信息冲突
3. 按重要性排序
4. 保留信息来源标识

## 融合后的信息：
请提供整合后的信息，格式如下：
- 核心信息点1 [来源：知识库/网络]
- 核心信息点2 [来源：知识库/网络]
...""",
            variables=["knowledge_info", "web_info"],
            category="fusion"
        )

        # 语言检测提示词
        self.built_in_prompts["language_detection"] = PromptTemplate(
            name="language_detection",
            version="1.0",
            description="检测文本语言类型",
            template="""请检测以下文本的语言类型：

文本内容：{text}

请返回语言代码：
- zh: 中文
- en: 英文
- ja: 日文
- ko: 韩文
- other: 其他语言

仅返回语言代码，不要其他内容。""",
            variables=["text"],
            category="analysis"
        )
        
        # 智能语言适配RAG提示词（支持Markdown）
        self.built_in_prompts["rag_qa_adaptive"] = PromptTemplate(
            name="rag_qa_adaptive",
            version="1.0",
            description="根据用户问题语言自动适配回答语言的RAG提示词，支持Markdown格式", 
            template="""You are a professional AI assistant. Please analyze the user's question language and respond in the same language.

If the user asks in English, respond in English.
If the user asks in Chinese, respond in Chinese.
If the user asks in other languages, try to respond in that language or English.

## Context Information

### Knowledge Base Results:
{knowledge_context}

### Web Search Results:
{web_context}

## Response Guidelines

1. **Language Matching**: Respond in the same language as the user's question
2. **Accuracy First**: Base your answer on the provided context
3. **Source Citation**: Clearly indicate information sources using markdown format
4. **Markdown Format**: Use proper markdown syntax for better readability:
   - Use **bold** for emphasis
   - Use *italics* for terminology
   - Use numbered lists (1. 2. 3.) or bullet points (- ) for structure
   - Use `code` for technical terms
   - Use > for important quotes
   - Use ### for subheadings if needed
5. **Natural Style**: Use natural and appropriate style for the detected language
6. **Structure**: Organize information clearly with headers, lists, and paragraphs

## User Question:
{query}

## Response:
[Please respond in the same language as the user's question above, using markdown format for better presentation]""",
            variables=["knowledge_context", "web_context", "query"],
            category="rag"
        )
    
    def _load_custom_prompts(self):
        """加载用户自定义提示词"""
        prompts_file = self.prompts_dir / "custom_prompts.yaml"
        
        if prompts_file.exists():
            try:
                with open(prompts_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    
                for prompt_data in data.get("prompts", []):
                    prompt = PromptTemplate(**prompt_data)
                    self.custom_prompts[prompt.name] = prompt
                    
                print(f"✅ 加载了 {len(self.custom_prompts)} 个自定义提示词")
                
            except Exception as e:
                print(f"⚠️ 加载自定义提示词失败: {e}")
    
    def get_prompt(self, name: str, prefer_custom: bool = True) -> Optional[PromptTemplate]:
        """获取提示词模板"""
        if prefer_custom and name in self.custom_prompts:
            return self.custom_prompts[name]
        
        if name in self.built_in_prompts:
            return self.built_in_prompts[name]
            
        if name in self.custom_prompts:
            return self.custom_prompts[name]
        
        return None
    
    def render_prompt(self, name: str, **kwargs) -> str:
        """渲染提示词"""
        prompt = self.get_prompt(name)
        if not prompt:
            raise ValueError(f"未找到提示词模板: {name}")
        
        return prompt.render(**kwargs)
    
    def list_prompts(self, category: str = None) -> Dict[str, List[PromptTemplate]]:
        """列出所有提示词"""
        all_prompts = {**self.built_in_prompts, **self.custom_prompts}
        
        if category:
            filtered = {k: v for k, v in all_prompts.items() if v.category == category}
            return {"prompts": list(filtered.values())}
        
        # 按类别分组
        categories = {}
        for prompt in all_prompts.values():
            if prompt.category not in categories:
                categories[prompt.category] = []
            categories[prompt.category].append(prompt)
        
        return categories
    
    def add_custom_prompt(self, prompt: PromptTemplate) -> bool:
        """添加自定义提示词"""
        self.custom_prompts[prompt.name] = prompt
        return self._save_custom_prompts()
    
    def update_custom_prompt(self, name: str, **updates) -> bool:
        """更新自定义提示词"""
        if name not in self.custom_prompts:
            return False
        
        prompt = self.custom_prompts[name]
        for key, value in updates.items():
            if hasattr(prompt, key):
                setattr(prompt, key, value)
        
        prompt.updated_at = datetime.now().isoformat()
        return self._save_custom_prompts()
    
    def delete_custom_prompt(self, name: str) -> bool:
        """删除自定义提示词"""
        if name in self.custom_prompts:
            del self.custom_prompts[name]
            return self._save_custom_prompts()
        return False
    
    def _save_custom_prompts(self) -> bool:
        """保存自定义提示词到文件"""
        try:
            prompts_data = {
                "prompts": [asdict(prompt) for prompt in self.custom_prompts.values()],
                "saved_at": datetime.now().isoformat()
            }
            
            prompts_file = self.prompts_dir / "custom_prompts.yaml"
            with open(prompts_file, 'w', encoding='utf-8') as f:
                yaml.dump(prompts_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"❌ 保存提示词失败: {e}")
            return False
    
    def detect_language(self, text: str) -> str:
        """简单的语言检测函数"""
        # 去除空白字符
        text = text.strip()
        if not text:
            return "unknown"
        
        # 统计不同字符类型
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        japanese_chars = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff]', text))
        korean_chars = len(re.findall(r'[\uac00-\ud7af]', text))
        
        total_chars = len(re.findall(r'[\w\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]', text))
        
        if total_chars == 0:
            return "unknown"
        
        # 计算各语言字符占比
        chinese_ratio = chinese_chars / total_chars
        english_ratio = english_chars / total_chars  
        japanese_ratio = japanese_chars / total_chars
        korean_ratio = korean_chars / total_chars
        
        # 判断主要语言
        if chinese_ratio > 0.3:
            return "zh"
        elif english_ratio > 0.7:
            return "en"
        elif japanese_ratio > 0.2:
            return "ja" 
        elif korean_ratio > 0.2:
            return "ko"
        elif english_ratio > 0.4:
            return "en"
        else:
            return "zh"  # 默认中文
    
    def select_adaptive_prompt(self, query: str, base_template: str = "rag_qa") -> str:
        """根据查询语言选择合适的提示词模板"""
        detected_lang = self.detect_language(query)
        
        # 如果是英文查询，使用语言自适应模板
        if detected_lang == "en":
            return "rag_qa_adaptive"
        # 其他语言或中文，使用自适应模板以确保语言匹配
        else:
            return "rag_qa_adaptive"
    
    def export_prompts(self, output_file: str = None) -> str:
        """导出所有提示词"""
        all_prompts = {**self.built_in_prompts, **self.custom_prompts}
        
        export_data = {
            "export_info": {
                "timestamp": datetime.now().isoformat(),
                "total_prompts": len(all_prompts),
                "categories": list(set(p.category for p in all_prompts.values()))
            },
            "prompts": [asdict(prompt) for prompt in all_prompts.values()]
        }
        
        if output_file:
            output_path = Path(output_file)
            with open(output_path, 'w', encoding='utf-8') as f:
                if output_path.suffix.lower() == '.json':
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                else:
                    yaml.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return json.dumps(export_data, ensure_ascii=False, indent=2)


# 全局提示词管理器实例
prompt_manager = PromptManager()


def get_prompt_manager() -> PromptManager:
    """获取提示词管理器实例"""
    return prompt_manager


def render_prompt(name: str, **kwargs) -> str:
    """快速渲染提示词的便捷函数"""
    return prompt_manager.render_prompt(name, **kwargs)