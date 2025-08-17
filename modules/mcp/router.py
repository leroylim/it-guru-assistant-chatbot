"""
MCP Router - Routes queries to appropriate sources using pure AI intent detection
"""
import streamlit as st
from typing import Dict, Any
from .intent_detector import AIIntentDetector
from .microsoft_client import MicrosoftLearnMCP
from .aws_client import AWSMCP
from .exa_client import ExaMCP


class Router:
    """Routes queries to appropriate sources using pure AI intent detection"""
    
    def __init__(self):
        self.intent_detector = AIIntentDetector()
        self.microsoft_mcp = MicrosoftLearnMCP()
        self.aws_mcp = AWSMCP()
        self.exa_mcp = ExaMCP()
    
    async def get_enhanced_context(self, query: str) -> Dict[str, Any]:
        """Get enhanced context from appropriate sources using AI intent detection"""
        # Use AI intent detection
        intent = await self.intent_detector.detect_intent(query)
        
        enhanced_context = {
            'source': intent['source'],
            'confidence': intent['confidence'],
            'keywords': intent.get('keywords', []),
            'method': intent.get('method', 'unknown'),
            'reasoning': intent.get('reasoning', ''),
            'results': [],
            'context_text': '',
            'confidence_explanation': self.intent_detector.get_confidence_explanation(intent)
        }
        
        # Early refusal path for out-of-scope queries
        if intent['source'] == 'out_of_scope':
            refusal_msg = st.secrets.get(
                "OUT_OF_SCOPE_MESSAGE",
                "Sorry, I’m focused on IT infrastructure, cybersecurity, cloud, DevOps, and IT careers. Please rephrase your question within this scope."
            )
            enhanced_context['context_text'] = refusal_msg
            enhanced_context['multi_source'] = False
            return enhanced_context

        try:
            # Route to appropriate source based on AI classification
            if intent['source'] == 'microsoft_learn':
                results = await self.microsoft_mcp.search_content(query)
                enhanced_context['results'] = results
                
            elif intent['source'] == 'aws_mcp':
                results = await self.aws_mcp.search_content(query)
                enhanced_context['results'] = results
                
            elif intent['source'] == 'exa_search':
                results = await self.exa_mcp.search_content(query)
                enhanced_context['results'] = results
                
            elif intent['source'] == 'ai_general':
                # For simple greetings/conversational queries, don't call external sources
                enhanced_context['results'] = []
                enhanced_context['context_text'] = 'Using AI general knowledge for conversational response.'
            
            enhanced_context['multi_source'] = False
            
            # Format context text
            if enhanced_context['results']:
                context_parts = []
                for result in enhanced_context['results']:
                    context_parts.append(
                        f"**{result['title']}** ({result['source']})\n"
                        f"{result['excerpt']}\n"
                        f"URL: {result['url']}\n"
                    )
                enhanced_context['context_text'] = "\n".join(context_parts)
            
        except Exception as e:
            st.error(f"Routing error: {str(e)}")
        
        return enhanced_context
