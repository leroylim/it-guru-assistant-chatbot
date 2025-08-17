"""
Configuration settings for IT-Guru Assistant
"""
import os
from typing import Dict, List

# Application settings
APP_CONFIG = {
    "title": "IT-Guru Assistant",
    "description": "Your specialized AI assistant for IT infrastructure and cybersecurity",
    "icon": "🔧",
    "layout": "wide",
    "max_context_messages": 10,
    "max_tokens": 4000,
    "temperature": 0.7
}

# OpenRouter models are selected via secrets.toml and UI; no static lists here.

# RAG settings removed (no local knowledge base / embeddings)

# IT domain keywords for query classification
IT_KEYWORDS = [
    'network', 'firewall', 'server', 'security', 'dns', 'ip', 'vpn', 'ssl', 'tls',
    'active directory', 'dhcp', 'tcp', 'udp', 'router', 'switch', 'cybersecurity',
    'malware', 'virus', 'backup', 'cloud', 'database', 'sql', 'linux', 'windows',
    'patch', 'vulnerability', 'encryption', 'authentication', 'authorization',
    'load balancer', 'monitoring', 'logging', 'incident', 'troubleshoot', 'azure',
    'aws', 'gcp', 'kubernetes', 'docker', 'container', 'devops', 'ci/cd', 'api',
    'rest', 'json', 'xml', 'http', 'https', 'ftp', 'ssh', 'telnet', 'smtp',
    'pop3', 'imap', 'ldap', 'kerberos', 'oauth', 'saml', 'raid', 'san', 'nas'
]

# Query type classification patterns
QUERY_PATTERNS = {
    'step_by_step': ['how to', 'steps', 'procedure', 'configure', 'setup', 'install', 'deploy'],
    'definition': ['what is', 'define', 'explain', 'meaning', 'definition of'],
    'troubleshooting': ['troubleshoot', 'fix', 'error', 'problem', 'issue', 'not working', 'failed'],
    'comparison': ['compare', 'difference', 'vs', 'versus', 'better', 'which one']
}

# System prompts for different query types
SYSTEM_PROMPTS = {
    'base': """You are IT-Guru, a specialized AI assistant for IT infrastructure and cybersecurity.

Your role:
- Provide accurate, up-to-date information on networking, security, and system administration
- Explain complex concepts clearly, adapting to user expertise level
- Reference authoritative sources when possible
- Decline non-IT queries politely while suggesting your core competencies

Response guidelines:
- Start with direct answers, then provide additional context
- Use technical terminology appropriately with explanations
- Include practical examples and implementation steps
- Maintain professional, helpful tone throughout""",
    
    'definition': "\n\nFormat: Provide a clear definition followed by key characteristics and real-world applications.",
    'step_by_step': "\n\nFormat: Provide numbered steps with clear instructions and any prerequisites.",
    'troubleshooting': "\n\nFormat: Start with common causes, then provide systematic troubleshooting steps.",
    'comparison': "\n\nFormat: Create a structured comparison highlighting key differences and use cases.",
    'general': "\n\nFormat: Provide comprehensive information with practical examples."
}

# Polite decline message for non-IT queries
NON_IT_RESPONSE = """I'm specialized in IT infrastructure and cybersecurity topics. I'd be happy to help you with:

🔧 **Networking**: Firewalls, VPNs, DNS, routing, switching
🔒 **Security**: Cybersecurity practices, SSL/TLS, incident response  
💻 **Systems**: Active Directory, server administration, backups
☁️ **Cloud**: Cloud computing, load balancing, monitoring

Please ask me about any IT or cybersecurity topic!"""

# Styling configuration
CUSTOM_CSS = """
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #1f4e79 0%, #2d5aa0 100%);
        color: white;
        margin-bottom: 2rem;
        border-radius: 10px;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #2d5aa0;
    }
    .user-message {
        background-color: #f0f2f6;
        border-left-color: #ff6b6b;
    }
    .assistant-message {
        background-color: #e8f4fd;
        border-left-color: #2d5aa0;
    }
    .feedback-buttons {
        display: flex;
        gap: 10px;
        margin-top: 10px;
    }
    .stButton > button {
        border-radius: 20px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .sidebar-info {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.5rem 0;
    }
</style>
"""
