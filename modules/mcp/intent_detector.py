"""
AI Intent Detector - Pure AI-powered intent detection using LLM classification
"""
import asyncio
import json
import httpx
import streamlit as st
from typing import Dict, Any


class AIIntentDetector:
    """Pure AI-powered intent detector using LLM classification"""
    
    def __init__(self):
        # (Feedback tracking removed)
        pass
    
    async def detect_intent(self, query: str) -> Dict[str, Any]:
        """Use AI to classify query intent with enhanced prompting"""
        try:
            # --- Scope guard (runs before any external calls) ---
            enforce_scope = bool(st.secrets.get("ENFORCE_IT_SCOPE", True))
            allow_it_career = bool(st.secrets.get("ALLOW_IT_CAREER_TOPICS", True))
            query_lower = query.lower().strip()

            if enforce_scope:
                # Non-IT topics to block
                non_it_patterns = [
                    'relationship', 'dating', 'marriage', 'breakup', 'love',
                    'diet', 'nutrition', 'weight loss', 'fitness', 'workout',
                    'mental health', 'therapy', 'depression', 'anxiety',
                    'finance', 'stocks', 'crypto', 'investment', 'tax', 'budget',
                    'politics', 'election', 'government', 'policy',
                    'religion', 'spiritual', 'astrology', 'horoscope',
                    'parenting', 'pregnancy', 'baby', 'children',
                    'travel', 'vacation', 'tourism', 'itinerary',
                    'sports', 'football', 'soccer', 'basketball',
                    'cooking', 'recipe', 'food', 'restaurant',
                    'celebrity', 'gossip', 'entertainment', 'movie', 'music'
                ]
                # IT-career/pro topics (allowed when configured)
                it_career_whitelist = [
                    'resume', 'cv', 'interview', 'career', 'study path', 'roadmap',
                    'certification', 'certifications', 'soc analyst', 'sre career',
                    'devops upskilling', 'job market', 'portfolio', 'linkedin'
                ]

                matches_non_it = any(pat in query_lower for pat in non_it_patterns)
                matches_it_career = any(pat in query_lower for pat in it_career_whitelist)

                if matches_non_it and not (allow_it_career and matches_it_career):
                    return {
                        'source': 'out_of_scope',
                        'confidence': 0.95,
                        'method': 'scope_guard',
                        'reasoning': 'Detected non-IT topic per scope policy'
                    }

            api_key = st.secrets.get("OPENROUTER_API_KEY")
            if not api_key:
                return self._fallback_classification(query)
            
            classification_prompt = f"""
            You are an expert IT query classifier. Analyze this query and determine the best source.
            
            Categories:
            1. **microsoft_learn**: Microsoft, Azure, Office 365, Windows, PowerShell, Active Directory, Teams, SharePoint, Exchange
            2. **aws_mcp**: AWS, Amazon Web Services, EC2, S3, Lambda, CloudFormation, VPC, IAM, RDS
            3. **exa_search**: Technical queries needing current information, vulnerabilities, troubleshooting, comparisons
            4. **ai_general**: Simple greetings, conversational queries, basic questions that don't need external sources
            
            Query: "{query}"
            
            Consider:
            - Keywords and context
            - Whether information needs to be current/real-time
            - Specific vendor/platform mentioned
            - Type of information requested
            
            Respond with JSON only:
            {{
                "source": "category_name",
                "confidence": 0.95,
                "reasoning": "detailed explanation of classification decision"
            }}
            """
            
            # Use a free model for intent detection
            default_model = st.secrets.get("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/leroylim/it-guru-assistant-chatbot.git",
                        "X-Title": "IT-Guru Assistant"
                    },
                    json={
                        "model": default_model,  # Use model from secrets.toml
                        "messages": [
                            {"role": "user", "content": classification_prompt}
                        ],
                        "max_tokens": 200,
                        "temperature": 0.1
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result['choices'][0]['message']['content'].strip()
                    
                    # Parse JSON response
                    try:
                        classification = json.loads(content)
                        classification['method'] = 'ai_classification'
                        return classification
                    except json.JSONDecodeError:
                        # Fallback if JSON parsing fails
                        return self._fallback_classification(query)
                else:
                    return self._fallback_classification(query)
                    
        except Exception as e:
            st.error(f"AI intent detection error: {str(e)}")
            return self._fallback_classification(query)
    
    def _fallback_classification(self, query: str) -> Dict[str, Any]:
        """Fallback classification using pattern matching"""
        query_lower = query.lower().strip()
        
        # Check for simple greetings/conversational queries that don't need MCP
        greeting_patterns = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 
                           'how are you', 'what can you do', 'help', 'thanks', 'thank you']
        
        if any(pattern in query_lower for pattern in greeting_patterns) and len(query_lower) < 50:
            return {
                'source': 'ai_general',
                'confidence': 0.9,
                'method': 'fallback_greeting',
                'reasoning': 'Simple greeting or conversational query, no external sources needed'
            }
        
        if any(word in query_lower for word in ['microsoft', 'azure', 'office', 'windows', 'powershell']):
            return {
                'source': 'microsoft_learn',
                'confidence': 0.7,
                'method': 'fallback_pattern',
                'reasoning': 'Microsoft-related query detected'
            }
        elif any(word in query_lower for word in ['aws', 'amazon', 'ec2', 's3', 'lambda']):
            return {
                'source': 'aws_mcp',
                'confidence': 0.7,
                'method': 'fallback_pattern',
                'reasoning': 'AWS-related query detected'
            }
        else:
            return {
                'source': 'exa_search',
                'confidence': 0.6,
                'method': 'fallback_default',
                'reasoning': 'General IT query, using real-time search'
            }
    
    def get_confidence_explanation(self, intent: Dict[str, Any]) -> str:
        """Generate human-readable confidence explanation"""
        confidence = intent.get('confidence', 0)
        method = intent.get('method', 'unknown')
        reasoning = intent.get('reasoning', 'No reasoning provided')
        
        if method == 'ai_classification':
            return f"AI classified with {confidence:.1%} confidence: {reasoning}"
        elif method == 'fallback_pattern':
            return f"Pattern matching with {confidence:.1%} confidence: {reasoning}"
        else:
            return f"Method: {method}, confidence: {confidence:.1%}"
    
    # (learn_from_feedback removed)
