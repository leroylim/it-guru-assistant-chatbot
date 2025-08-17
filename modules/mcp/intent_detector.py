"""
AI Intent Detector - Pure AI-powered intent detection using LLM classification
"""
import asyncio
import json
import httpx
import streamlit as st
import re
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
            use_llm_scope_check = bool(st.secrets.get("LLM_SCOPE_CHECK", False))
            query_lower = query.lower().strip()

            if enforce_scope:
                # Non-IT topics to block (use specific phrases to avoid collisions)
                non_it_patterns = [
                    'relationship', 'dating', 'marriage', 'breakup', 'love',
                    'diet', 'nutrition', 'weight loss', 'fitness', 'workout',
                    'mental health', 'therapy', 'depression', 'anxiety',
                    'finance', 'stock market', 'stock trading', 'cryptocurrency', 'crypto trading', 'crypto wallet', 'investment', 'tax', 'budget',
                    'politics', 'election', 'public policy', 'foreign policy', 'economic policy',
                    'religion', 'spiritual', 'astrology', 'horoscope',
                    'parenting', 'pregnancy', 'baby',
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

                # Common IT anchors: if present, prefer allowing the query
                it_anchors = [
                    'firewall', 'vpn', 'router', 'switch', 'ips', 'ids', 'siem', 'xdr', 'edr', 'soar', 'endpoint',
                    'malware', 'cve', 'vulnerability', 'exploit', 'threat', 'tls', 'ssl', 'certificate', 'certificates', 'ssh',
                    'linux', 'windows', 'active directory', 'group policy', 'gpo', 'powershell',
                    'azure', 'aws', 'gcp', 'kubernetes', 'docker', 'terraform', 'ansible', 'devops', 'sre',
                    'fortinet', 'cisco', 'palo alto', 'okta', 'cloudflare', 'nginx', 'istio', 'gitlab', 'github', 's3', 'ec2', 'vpc'
                ]

                # Regex word-boundary matching for single-word non-IT terms; substring for multi-word phrases
                def matches_non_it_term(text: str) -> bool:
                    for term in non_it_patterns:
                        if ' ' in term:
                            if term in text:
                                return True
                        else:
                            if re.search(r'\b' + re.escape(term) + r'\b', text):
                                return True
                    return False

                matches_non_it = matches_non_it_term(query_lower)
                matches_it_career = any(pat in query_lower for pat in it_career_whitelist)
                matches_it_anchor = any(anchor in query_lower for anchor in it_anchors)

                # Block only if clearly non-IT and no strong IT anchors present
                if matches_non_it and not matches_it_anchor and not (allow_it_career and matches_it_career):
                    return {
                        'source': 'out_of_scope',
                        'confidence': 0.95,
                        'method': 'scope_guard',
                        'reasoning': 'Detected non-IT topic per scope policy'
                    }

                # Ambiguous case: contains a non-IT term and an IT anchor
                if use_llm_scope_check and matches_non_it and matches_it_anchor:
                    try:
                        llm_in_scope = await self._llm_scope_check(query)
                        if not llm_in_scope:
                            return {
                                'source': 'out_of_scope',
                                'confidence': 0.9,
                                'method': 'llm_scope_guard',
                                'reasoning': 'LLM determined query is out of IT scope'
                            }
                    except Exception as _:
                        # If LLM scope check fails, fall through to allow and continue
                        pass

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

    async def _llm_scope_check(self, query: str) -> bool:
        """Return True if query is within IT scope, else False. Uses lightweight LLM if configured."""
        api_key = st.secrets.get("OPENROUTER_API_KEY")
        if not api_key:
            # Without API key, default to allow to avoid false negatives
            return True
        model = st.secrets.get("LLM_SCOPE_MODEL", st.secrets.get("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free"))

        prompt = f"""
        You judge if a user query is within the scope of an IT assistant focused on:
        - IT infrastructure, networking, servers, Windows/Linux, Active Directory
        - Cybersecurity (firewalls, VPN, SIEM, EDR, IAM), vulnerabilities, CVEs
        - Cloud/DevOps (AWS, Azure, GCP, Kubernetes, Docker, Terraform, CI/CD)
        - IT career and certifications (if mentioned)

        If the query is primarily about non-IT personal topics (politics, religion, relationships, diet, travel, entertainment, general finance), it is OUT OF SCOPE.

        Query: "{query}"

        Respond with strict JSON only: {{"in_scope": true}}
        """

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
                    "model": model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 20,
                    "temperature": 0.0
                }
            )
            if response.status_code == 200:
                try:
                    result = response.json()
                    content = result['choices'][0]['message']['content'].strip()
                    data = json.loads(content)
                    return bool(data.get("in_scope", True))
                except Exception:
                    return True
            return True
    
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
