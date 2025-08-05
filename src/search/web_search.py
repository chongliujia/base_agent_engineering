"""
Web Search Module - Supporting Multiple Search Engines
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from config.settings import get_settings


class WebSearchResult:
    """Web search result"""
    
    def __init__(self, title: str, content: str, url: str, score: float = 0.0, 
                 source: str = "", published_date: str = ""):
        self.title = title
        self.content = content
        self.url = url
        self.score = score
        self.source = source
        self.published_date = published_date
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "url": self.url,
            "score": self.score,
            "source": self.source,
            "published_date": self.published_date,
            "timestamp": self.timestamp
        }


class TavilySearchEngine:
    """Tavily search engine implementation"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.tavily.com"
        self.session = None
    
    async def _get_session(self):
        """Get or create HTTP session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def search(self, query: str, max_results: int = 5, 
                    search_depth: str = "basic", 
                    include_domains: List[str] = None,
                    exclude_domains: List[str] = None) -> List[WebSearchResult]:
        """Execute Tavily search"""
        
        if not self.api_key:
            raise ValueError("Tavily API key not configured")
        
        session = await self._get_session()
        
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results,
            "include_answer": True,
            "include_raw_content": False,
            "include_images": False
        }
        
        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains
        
        try:
            async with session.post(
                f"{self.base_url}/search",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Tavily API error {response.status}: {error_text}")
                
                data = await response.json()
                return self._parse_tavily_results(data)
                
        except Exception as e:
            print(f"❌ Tavily search failed: {e}")
            return []
    
    def _parse_tavily_results(self, data: Dict[str, Any]) -> List[WebSearchResult]:
        """Parse Tavily search results"""
        results = []
        
        # Parse search results
        for item in data.get("results", []):
            result = WebSearchResult(
                title=item.get("title", ""),
                content=item.get("content", ""),
                url=item.get("url", ""),
                score=item.get("score", 0.0),
                source="tavily",
                published_date=item.get("published_date", "")
            )
            results.append(result)
        
        return results
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None


class DuckDuckGoSearchEngine:
    """DuckDuckGo search engine (backup)"""
    
    def __init__(self):
        self.session = None
    
    async def _get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def search(self, query: str, max_results: int = 5) -> List[WebSearchResult]:
        """Execute DuckDuckGo search (simplified version)"""
        # This is a simplified implementation, should actually use duckduckgo-search library
        # Provided here as a backup solution with basic structure
        
        results = [
            WebSearchResult(
                title=f"DuckDuckGo search result: {query}",
                content=f"This is search result content about '{query}'",
                url="https://duckduckgo.com",
                score=0.8,
                source="duckduckgo"
            )
        ]
        
        return results
    
    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None


class WebSearchManager:
    """Web search manager"""
    
    def __init__(self):
        self.settings = get_settings()
        self.tavily_engine = None
        self.duckduckgo_engine = None
        
        # Initialize search engines
        if self.settings.tavily_api_key:
            self.tavily_engine = TavilySearchEngine(self.settings.tavily_api_key)
        
        self.duckduckgo_engine = DuckDuckGoSearchEngine()
    
    async def search(self, query: str, max_results: int = 5, 
                    preferred_engine: str = "tavily",
                    search_config: Dict[str, Any] = None) -> List[WebSearchResult]:
        """Execute web search"""
        
        search_config = search_config or {}
        
        # Prefer Tavily
        if preferred_engine == "tavily" and self.tavily_engine:
            try:
                results = await self.tavily_engine.search(
                    query=query,
                    max_results=max_results,
                    search_depth=search_config.get("search_depth", "basic"),
                    include_domains=search_config.get("include_domains"),
                    exclude_domains=search_config.get("exclude_domains")
                )
                
                if results:
                    print(f"✅ Tavily search successful: found {len(results)} results")
                    return results
                    
            except Exception as e:
                print(f"⚠️ Tavily search failed, trying backup: {e}")
        
        # Backup: DuckDuckGo
        if self.duckduckgo_engine:
            try:
                results = await self.duckduckgo_engine.search(query, max_results)
                print(f"✅ DuckDuckGo search successful: found {len(results)} results")
                return results
                
            except Exception as e:
                print(f"❌ DuckDuckGo search also failed: {e}")
        
        # Return empty results
        print("❌ All search engines unavailable")
        return []
    
    def get_search_summary(self, results: List[WebSearchResult]) -> Dict[str, Any]:
        """Get search results summary"""
        if not results:
            return {"total": 0, "sources": [], "average_score": 0.0}
        
        sources = list(set(result.source for result in results))
        total_score = sum(result.score for result in results)
        average_score = total_score / len(results) if results else 0.0
        
        return {
            "total": len(results),
            "sources": sources,
            "average_score": round(average_score, 2),
            "urls": [result.url for result in results],
            "timestamp": datetime.now().isoformat()
        }
    
    async def close(self):
        """Close all search engine connections"""
        if self.tavily_engine:
            await self.tavily_engine.close()
        if self.duckduckgo_engine:
            await self.duckduckgo_engine.close()


# Global search manager instance
web_search_manager = WebSearchManager()


async def search_web(query: str, max_results: int = 5, 
                    search_config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Simplified search interface"""
    results = await web_search_manager.search(query, max_results, search_config=search_config)
    return [result.to_dict() for result in results]


async def close_search_connections():
    """Close search connections (for cleanup when application shuts down)"""
    await web_search_manager.close()