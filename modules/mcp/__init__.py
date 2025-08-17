"""
MCP Package - Model Context Protocol integrations
"""
from .base_client import BaseMCPClient
from .microsoft_client import MicrosoftLearnMCP
from .aws_client import AWSMCP
from .exa_client import ExaMCP
from .intent_detector import AIIntentDetector
from .router import Router

__all__ = [
    'BaseMCPClient',
    'MicrosoftLearnMCP', 
    'AWSMCP',
    'ExaMCP',
    'AIIntentDetector',
    'Router'
]
