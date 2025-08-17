"""
Microsoft Learn MCP Client with SSE streaming support
"""
import aiohttp
import streamlit as st
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List


class MicrosoftLearnMCP:
    """Microsoft Learn MCP integration using SSE streaming protocol"""
    
    def __init__(self):
        self.mcp_endpoint = "https://learn.microsoft.com/api/mcp"
        self.tools_cache = None
        self.last_tools_refresh = None
    
    async def _handle_sse_stream(self, response) -> Dict:
        """Handle Server-Sent Events streaming response"""
        try:
            result = {}
            content_buffer = []
            
            async for chunk in response.content.iter_chunked(1024):
                chunk_text = chunk.decode('utf-8')
                content_buffer.append(chunk_text)
                
                # Process complete lines
                full_content = ''.join(content_buffer)
                lines = full_content.split('\n')
                
                # Keep the last incomplete line in buffer
                content_buffer = [lines[-1]] if not full_content.endswith('\n') else []
                
                for line in lines[:-1] if not full_content.endswith('\n') else lines:
                    line = line.strip()
                    if line.startswith('data: '):
                        data_str = line[6:]  # Remove 'data: ' prefix
                        if data_str and data_str != '[DONE]':
                            try:
                                data = json.loads(data_str)
                                # Accumulate the streaming response
                                if 'result' in data:
                                    result = data['result']
                                elif 'content' in data:
                                    result = data
                                elif 'error' in data:
                                    st.error(f"MCP error: {data['error']}")
                            except json.JSONDecodeError:
                                continue
            return result
        except Exception as e:
            st.error(f"SSE stream handling error: {str(e)}")
            return {}
    
    async def _refresh_tools(self):
        """Refresh available tools from Microsoft MCP server using SSE"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.mcp_endpoint,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "text/event-stream"
                    },
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/list"
                    }
                ) as response:
                    if response.status == 200:
                        result = await self._handle_sse_stream(response)
                        if result and "tools" in result:
                            self.tools_cache = result["tools"]
                            self.last_tools_refresh = datetime.now()
                            return True
        except Exception as e:
            st.error(f"Failed to refresh Microsoft MCP tools: {str(e)}")
        return False
    
    async def _call_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """Call a specific Microsoft MCP tool using SSE"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.mcp_endpoint,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "text/event-stream"
                    },
                    json={
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/call",
                        "params": {
                            "name": tool_name,
                            "arguments": arguments
                        }
                    }
                ) as response:
                    if response.status == 200:
                        result = await self._handle_sse_stream(response)
                        return result
                    elif response.status in [400, 404]:
                        # Tool schema may have changed, refresh tools
                        await self._refresh_tools()
                        return {}
        except Exception as e:
            st.error(f"Microsoft MCP tool call error: {str(e)}")
        return {}
    
    async def _fallback_search(self, query: str, max_results: int = 3) -> List[Dict]:
        """Fallback search using Microsoft Learn search API directly"""
        try:
            async with aiohttp.ClientSession() as session:
                # Use Microsoft Learn search API
                search_url = "https://learn.microsoft.com/api/search"
                params = {
                    "search": query,
                    "locale": "en-us",
                    "facet": "category",
                    "top": max_results
                }
                
                async with session.get(search_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        
                        if "results" in data:
                            for item in data["results"][:max_results]:
                                results.append({
                                    "title": item.get("title", f"Microsoft Learn: {query}"),
                                    "excerpt": item.get("description", item.get("summary", ""))[:200] + "...",
                                    "url": item.get("url", f"https://learn.microsoft.com{item.get('path', '')}"),
                                    "source": "Microsoft Learn"
                                })
                        
                        return results
        except Exception as e:
            st.error(f"Microsoft Learn fallback search error: {str(e)}")
        
        return []
    
    async def search_content(self, query: str, max_results: int = 3) -> List[Dict]:
        """Search Microsoft Learn documentation using MCP with SSE, fallback to direct API"""
        try:
            # First try MCP approach
            if not self.tools_cache or not self.last_tools_refresh:
                await self._refresh_tools()
            
            # Use microsoft_docs_search tool if available
            if self.tools_cache:
                search_result = await self._call_tool("microsoft_docs_search", {"query": query})
                
                if search_result and "content" in search_result:
                    # Parse the search results
                    results = []
                    content = search_result["content"]
                    
                    # Handle different response formats
                    if isinstance(content, list):
                        for item in content[:max_results]:
                            if isinstance(item, dict):
                                results.append({
                                    "title": item.get("title", f"Microsoft Learn: {query}"),
                                    "excerpt": item.get("excerpt", item.get("description", ""))[:200] + "...",
                                    "url": item.get("url", item.get("link", "")),
                                    "source": "Microsoft Learn"
                                })
                    elif isinstance(content, str):
                        # If content is a string, create a single result
                        results.append({
                            "title": f"Microsoft Learn: {query}",
                            "excerpt": content[:200] + "...",
                            "url": f"https://learn.microsoft.com/search?query={query.replace(' ', '%20')}",
                            "source": "Microsoft Learn"
                        })
                    
                    if results:
                        return results
            
            # Fallback to direct API search
            return await self._fallback_search(query, max_results)
            
        except Exception as e:
            st.error(f"Microsoft Learn search error: {str(e)}")
            # Final fallback to direct search
            return await self._fallback_search(query, max_results)
