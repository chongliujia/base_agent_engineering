"""
Prompt Management System - Supporting configurable and templated prompts
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
    """Prompt template"""
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
        """Render prompt template"""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            missing_var = str(e).strip("'")
            raise ValueError(f"Template variable missing: {missing_var}. Required variables: {self.variables}")


class PromptManager:
    """Prompt manager"""
    
    def __init__(self, prompts_dir: str = None):
        self.settings = get_settings()
        self.prompts_dir = Path(prompts_dir or "config/prompts")
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        
        # Built-in prompt templates
        self.built_in_prompts = {}
        self._load_built_in_prompts()
        
        # User custom prompts
        self.custom_prompts = {}
        self._load_custom_prompts()
    
    def _load_built_in_prompts(self):
        """Load built-in prompt templates"""
        
        # RAG Q&A prompt (supports Markdown)
        self.built_in_prompts["rag_qa"] = PromptTemplate(
            name="rag_qa",
            version="1.0",
            description="Q&A prompt based on knowledge base and web search, supports Markdown format",
            template="""You are a professional AI assistant capable of answering user questions based on knowledge base documents and web search results.

## Context Information

### Knowledge Base Retrieval Results:
{knowledge_context}

### Web Search Results:
{web_context}

## Response Requirements

1. **Accuracy First**: Answer based on the provided context information
2. **Information Fusion**: Integrate information from knowledge base and web search
3. **Source Citation**: Clearly indicate information sources
4. **Structured Response**: Use clear paragraphs and bullet points
5. **Honest Response**: If information is insufficient, please state honestly
6. **Markdown Format**: Please use Markdown syntax to optimize answer format:
   - Use **bold** to emphasize important concepts
   - Use *italics* to mark professional terms
   - Use ordered lists (1. 2. 3.) or unordered lists (-) to organize information
   - Use `code format` to mark technical terms
   - Use > to quote important information
   - Use ### subheadings to organize content structure

## User Question:
{query}

## Answer:
Please provide an accurate, comprehensive and well-formatted answer based on the above context information using Markdown format.""",
            variables=["knowledge_context", "web_context", "query"],
            category="rag"
        )
        
        # Knowledge-only Q&A (supports Markdown)
        self.built_in_prompts["knowledge_only"] = PromptTemplate(
            name="knowledge_only", 
            version="1.0",
            description="Q&A prompt based only on knowledge base, supports Markdown format",
            template="""You are a professional document assistant, specializing in answering user questions based on knowledge base document content.

## Knowledge Base Context:
{knowledge_context}

## Response Guidelines:
- Answer strictly based on the provided document content
- If there is no relevant information in the documents, please state clearly
- Quote specific document fragments to support your answer
- Maintain accuracy and professionalism in your response
- **Use Markdown format** to optimize answer presentation:
  - Use **bold** to emphasize key concepts
  - Use *italics* to mark document sources
  - Use lists to organize information points
  - Use > to quote original document text
  - Use ### to organize answer structure

## User Question:
{query}

## Document-based Answer:""",
            variables=["knowledge_context", "query"],
            category="knowledge"
        )
        
        # Web search Q&A (supports Markdown)
        self.built_in_prompts["web_only"] = PromptTemplate(
            name="web_only",
            version="1.0", 
            description="Q&A prompt based only on web search, supports Markdown format",
            template="""You are an information research assistant, answering user questions based on the latest web search results.

## Web Search Results:
{web_context}

## Response Requirements:
- Provide the latest and accurate information based on search results
- Integrate information from multiple sources
- Mark information source links
- Pay attention to the timeliness and reliability of information
- **Use Markdown format** to optimize answer presentation:
  - Use **bold** to emphasize important information
  - Use *italics* to mark source websites
  - Use lists to organize multiple information points
  - Use [link text](URL) format to provide source links
  - Use ### to organize answer structure

## User Question:
{query}

## Search-based Answer:""",
            variables=["web_context", "query"],
            category="web"
        )
        
        # Query analysis prompt
        self.built_in_prompts["query_analysis"] = PromptTemplate(
            name="query_analysis",
            version="1.0",
            description="For analyzing user query intent and type",
            template="""Please analyze the following user query to determine its type and retrieval strategy.

## User Query:
{query}

## Analysis Dimensions:
1. **Query Type**: Factual, Analytical, Operational, Conceptual
2. **Timeliness Requirement**: Whether latest information is needed
3. **Complexity**: Simple, Medium, Complex
4. **Domain**: Technology, Business, Life, Academic, etc.
5. **Recommended Strategy**: knowledge_only, web_only, both

Please return analysis results in JSON format:
{{
    "query_type": "type",
    "needs_realtime": true/false,
    "complexity": "simple/medium/complex",
    "domain": "domain",
    "recommended_strategy": "strategy",
    "keywords": ["keyword1", "keyword2"],
    "reasoning": "analysis reasoning"
}}""",
            variables=["query"],
            category="analysis"
        )
        
        # Information fusion prompt
        self.built_in_prompts["information_fusion"] = PromptTemplate(
            name="information_fusion",
            version="1.0",
            description="For fusing multi-source information",
            template="""Please integrate and deduplicate the following information from different sources.

## Knowledge Base Information:
{knowledge_info}

## Web Search Information:
{web_info}

## Fusion Requirements:
1. Remove duplicate information
2. Resolve information conflicts
3. Sort by importance
4. Retain source identification

## Fused Information:
Please provide integrated information in the following format:
- Core information point 1 [Source: Knowledge Base/Web]
- Core information point 2 [Source: Knowledge Base/Web]
...""",
            variables=["knowledge_info", "web_info"],
            category="fusion"
        )

        # Language detection prompt
        self.built_in_prompts["language_detection"] = PromptTemplate(
            name="language_detection",
            version="1.0",
            description="Detect text language type",
            template="""Please detect the language type of the following text:

Text content: {text}

Please return language code:
- zh: Chinese
- en: English
- ja: Japanese
- ko: Korean
- other: Other languages

Return only the language code, no other content.""",
            variables=["text"],
            category="analysis"
        )
        
        # Smart language-adaptive RAG prompt (supports Markdown)
        self.built_in_prompts["rag_qa_adaptive"] = PromptTemplate(
            name="rag_qa_adaptive",
            version="1.0",
            description="RAG prompt that automatically adapts response language based on user question language, supports Markdown format", 
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
        """Load user custom prompts"""
        prompts_file = self.prompts_dir / "custom_prompts.yaml"
        
        if prompts_file.exists():
            try:
                with open(prompts_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    
                for prompt_data in data.get("prompts", []):
                    prompt = PromptTemplate(**prompt_data)
                    self.custom_prompts[prompt.name] = prompt
                    
                print(f"✅ Loaded {len(self.custom_prompts)} custom prompts")
                
            except Exception as e:
                print(f"⚠️ Failed to load custom prompts: {e}")
    
    def get_prompt(self, name: str, prefer_custom: bool = True) -> Optional[PromptTemplate]:
        """Get prompt template"""
        if prefer_custom and name in self.custom_prompts:
            return self.custom_prompts[name]
        
        if name in self.built_in_prompts:
            return self.built_in_prompts[name]
            
        if name in self.custom_prompts:
            return self.custom_prompts[name]
        
        return None
    
    def render_prompt(self, name: str, **kwargs) -> str:
        """Render prompt"""
        prompt = self.get_prompt(name)
        if not prompt:
            raise ValueError(f"Prompt template not found: {name}")
        
        return prompt.render(**kwargs)
    
    def list_prompts(self, category: str = None) -> Dict[str, List[PromptTemplate]]:
        """List all prompts"""
        all_prompts = {**self.built_in_prompts, **self.custom_prompts}
        
        if category:
            filtered = {k: v for k, v in all_prompts.items() if v.category == category}
            return {"prompts": list(filtered.values())}
        
        # Group by category
        categories = {}
        for prompt in all_prompts.values():
            if prompt.category not in categories:
                categories[prompt.category] = []
            categories[prompt.category].append(prompt)
        
        return categories
    
    def add_custom_prompt(self, prompt: PromptTemplate) -> bool:
        """Add custom prompt"""
        self.custom_prompts[prompt.name] = prompt
        return self._save_custom_prompts()
    
    def update_custom_prompt(self, name: str, **updates) -> bool:
        """Update custom prompt"""
        if name not in self.custom_prompts:
            return False
        
        prompt = self.custom_prompts[name]
        for key, value in updates.items():
            if hasattr(prompt, key):
                setattr(prompt, key, value)
        
        prompt.updated_at = datetime.now().isoformat()
        return self._save_custom_prompts()
    
    def delete_custom_prompt(self, name: str) -> bool:
        """Delete custom prompt"""
        if name in self.custom_prompts:
            del self.custom_prompts[name]
            return self._save_custom_prompts()
        return False
    
    def _save_custom_prompts(self) -> bool:
        """Save custom prompts to file"""
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
            print(f"❌ Failed to save prompts: {e}")
            return False
    
    def detect_language(self, text: str) -> str:
        """Simple language detection function"""
        # Remove whitespace
        text = text.strip()
        if not text:
            return "unknown"
        
        # Count different character types
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        japanese_chars = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff]', text))
        korean_chars = len(re.findall(r'[\uac00-\ud7af]', text))
        
        total_chars = len(re.findall(r'[\w\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]', text))
        
        if total_chars == 0:
            return "unknown"
        
        # Calculate character ratios for each language
        chinese_ratio = chinese_chars / total_chars
        english_ratio = english_chars / total_chars  
        japanese_ratio = japanese_chars / total_chars
        korean_ratio = korean_chars / total_chars
        
        # Determine primary language
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
            return "zh"  # Default to Chinese
    
    def select_adaptive_prompt(self, query: str, base_template: str = "rag_qa") -> str:
        """Select appropriate prompt template based on query language"""
        detected_lang = self.detect_language(query)
        
        # If English query, use language-adaptive template
        if detected_lang == "en":
            return "rag_qa_adaptive"
        # For other languages or Chinese, use adaptive template to ensure language matching
        else:
            return "rag_qa_adaptive"
    
    def export_prompts(self, output_file: str = None) -> str:
        """Export all prompts"""
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


# Global prompt manager instance
prompt_manager = PromptManager()


def get_prompt_manager() -> PromptManager:
    """Get prompt manager instance"""
    return prompt_manager


def render_prompt(name: str, **kwargs) -> str:
    """Convenient function for quick prompt rendering"""
    return prompt_manager.render_prompt(name, **kwargs)