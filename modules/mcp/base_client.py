"""
Base MCP Client - Common functionality for all MCP integrations
"""
import asyncio
import json
import aiohttp
import streamlit as st
from datetime import datetime
from typing import Dict, Any, List
from abc import ABC, abstractmethod


class BaseMCPClient(ABC):
    """Base class for MCP client implementations"""
    
    def __init__(self, endpoint: str):
        self.mcp_endpoint = endpoint
        self.tools_cache = None
        self.last_tools_refresh = None
    
    async def _refresh_tools(self):
        """Refresh available tools from MCP server"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.mcp_endpoint,
                    headers={"Content-Type": "application/json"},
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/list"
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.tools_cache = data.get("result", {}).get("tools", [])
                        self.last_tools_refresh = datetime.now()
                        return True
        except Exception as e:
            st.error(f"Failed to refresh MCP tools: {str(e)}")
        return False
    
    async def _call_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """Call a specific MCP tool"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.mcp_endpoint,
                    headers={"Content-Type": "application/json"},
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
                        data = await response.json()
                        return data.get("result", {})
                    elif response.status in [400, 404]:
                        # Tool schema may have changed, refresh tools
                        await self._refresh_tools()
                        return {}
        except Exception as e:
            st.error(f"MCP tool call error: {str(e)}")
        return {}
    
    @abstractmethod
    async def search_content(self, query: str, max_results: int = 3) -> List[Dict]:
        """Search content using MCP - must be implemented by subclasses"""
        pass
