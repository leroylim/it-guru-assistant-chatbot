"""
AWS Knowledge MCP Client
"""
import re
import aiohttp
import streamlit as st
from datetime import datetime
from typing import Dict, Any, List
from .base_client import BaseMCPClient


class AWSMCP(BaseMCPClient):
    """AWS Knowledge MCP integration using real MCP protocol"""
    
    def __init__(self):
        super().__init__("https://knowledge-mcp.global.api.aws")
    
    async def read_documentation(self, url: str) -> str:
        """Read AWS documentation page and convert to markdown"""
        try:
            result = await self._call_tool("read_documentation", {"url": url})
            if result and "content" in result:
                return result["content"]
            return ""
        except Exception as e:
            st.error(f"AWS read_documentation error: {str(e)}")
            return ""
    
    async def recommend_content(self, url: str, max_results: int = 3) -> List[Dict]:
        """Get content recommendations for AWS documentation page"""
        try:
            result = await self._call_tool("recommend", {"url": url})
            if result and "content" in result:
                content = result["content"]
                if isinstance(content, list):
                    recommendations = []
                    for item in content[:max_results]:
                        if isinstance(item, dict):
                            recommendations.append({
                                "title": item.get("title", "AWS Documentation"),
                                "excerpt": item.get("description", item.get("summary", ""))[:200] + "...",
                                "url": item.get("url", item.get("link", "")),
                                "source": "AWS Documentation"
                            })
                    return recommendations
            return []
        except Exception as e:
            st.error(f"AWS recommend error: {str(e)}")
            return []
    
    async def search_content(self, query: str, max_results: int = 3) -> List[Dict]:
        """Search AWS documentation using MCP"""
        try:
            # Refresh tools if not cached or stale
            if not self.tools_cache or not self.last_tools_refresh:
                await self._refresh_tools()
            
            # Check if query contains a URL for recommendation
            if "docs.aws.amazon.com" in query.lower():
                # Extract URL and get recommendations
                url_match = re.search(r'https?://docs\.aws\.amazon\.com[^\s]+', query)
                if url_match:
                    url = url_match.group(0)
                    recommendations = await self.recommend_content(url, max_results)
                    if recommendations:
                        return recommendations
            
            # Try to use search_documentation tool
            search_result = await self._call_tool("search_documentation", {
                "search_phrase": query,
                "limit": max_results
            })
            
            if search_result and "content" in search_result:
                # Parse the search results
                results = []
                content = search_result["content"]
                
                # Handle different response formats
                if isinstance(content, list):
                    for item in content[:max_results]:
                        if isinstance(item, dict):
                            results.append({
                                "title": item.get("title", f"AWS Documentation: {query}"),
                                "excerpt": item.get("excerpt", item.get("description", item.get("summary", "")))[:200] + "...",
                                "url": item.get("url", item.get("link", "")),
                                "source": "AWS Documentation"
                            })
                elif isinstance(content, str):
                    # If content is a string, create a single result
                    results.append({
                        "title": f"AWS Documentation: {query}",
                        "excerpt": content[:200] + "...",
                        "url": f"https://docs.aws.amazon.com/search/doc-search.html?searchPath=documentation&searchQuery={query.replace(' ', '%20')}",
                        "source": "AWS Documentation"
                    })
                
                return results
            
            # Return empty if MCP call fails
            return []
            
        except Exception as e:
            st.error(f"AWS MCP error: {str(e)}")
            return []
