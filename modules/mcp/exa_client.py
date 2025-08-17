"""
Exa Real-time Search Client
"""
import aiohttp
import json
import os
import streamlit as st
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List


class ExaMCP:
    """Exa real-time search MCP integration with intelligent domain selection"""
    
    def __init__(self):
        # Defaults in case JSON cannot be read
        default_domain_categories = {
            "cybersecurity": [
                # News and analysis
                "bleepingcomputer.com", "krebsonsecurity.com", "securityweek.com",
                "threatpost.com", "darkreading.com", "infosecurity-magazine.com",
                "cybersecuritynews.com", "hackread.com", "thehackernews.com",
                "securityboulevard.com", "cyberscoop.com", "recordedfuture.com",
                # Official and frameworks
                "nist.gov", "cisa.gov", "sans.org", "owasp.org", "mitre.org",
                "attack.mitre.org",
                # Vendor researchers
                "talosintelligence.com", "unit42.paloaltonetworks.com",
                "blog.talosintelligence.com", "crowdstrike.com",
                "mandiant.com", "rapid7.com", "tenable.com", "qualys.com",
                # Advisories indices
                "github.com/advisories", "msrc.microsoft.com"
            ],
            "cloud_devops": [
                # Clouds
                "aws.amazon.com", "azure.microsoft.com", "cloud.google.com",
                # Security blogs
                "aws.amazon.com/blogs/security", "azure.microsoft.com/blog/topics/security",
                "cloud.google.com/blog/products/identity-security",
                # Platforms
                "cloudsecurityalliance.org", "devops.com", "containerjournal.com",
                "kubernetes.io", "docker.com", "redhat.com", "vmware.com",
                # Infra/docs
                "docs.nginx.com", "nginx.com", "istio.io", "envoyproxy.io",
                "developer.hashicorp.com", "helm.sh", "cncf.io"
            ],
            "it_general": [
                "techcrunch.com", "arstechnica.com", "zdnet.com", "computerworld.com",
                "infoworld.com", "techrepublic.com", "itpro.co.uk", "networkworld.com",
                "datacenterknowledge.com", "enterprisetech.com", "itbusinessedge.com"
            ],
            "programming": [
                "stackoverflow.com", "github.com", "dev.to", "medium.com",
                "hackernoon.com", "freecodecamp.org", "codinghorror.com"
            ],
            "business_tech": [
                "forbes.com", "businessinsider.com", "wired.com", "fastcompany.com",
                "venturebeat.com", "techcrunch.com", "recode.net"
            ],
            "research_academic": [
                "arxiv.org", "acm.org", "ieee.org", "springer.com", "nature.com",
                "sciencedirect.com", "researchgate.net"
            ]
        }
        default_vendor_map = {
            "cisco": ["advisories.cisco.com", "blogs.cisco.com", "talosintelligence.com"],
            "palo alto": ["paloaltonetworks.com", "unit42.paloaltonetworks.com", "docs.paloaltonetworks.com", "live.paloaltonetworks.com"],
            "fortinet": ["fortinet.com", "docs.fortinet.com"],
            "cloudflare": ["cloudflare.com", "blog.cloudflare.com", "developers.cloudflare.com", "docs.cloudflare.com"],
            "okta": ["okta.com", "developer.okta.com", "help.okta.com"],
            "auth0": ["auth0.com", "auth0.com/docs"],
            "github": ["github.com", "docs.github.com", "github.com/advisories"],
            "gitlab": ["gitlab.com", "docs.gitlab.com"],
            "hashicorp": ["developer.hashicorp.com"],
            "terraform": ["developer.hashicorp.com", "registry.terraform.io"],
            "vault": ["developer.hashicorp.com"],
            "consul": ["developer.hashicorp.com"],
            "nginx": ["docs.nginx.com", "nginx.com"],
            "istio": ["istio.io"],
            "envoy": ["envoyproxy.io"],
            "red hat": ["redhat.com", "access.redhat.com/security/cve"],
            "ubuntu": ["ubuntu.com/security"],
            "debian": ["security.debian.org"],
            "microsoft": ["learn.microsoft.com", "msrc.microsoft.com"],
            "apple": ["support.apple.com"],
            "project zero": ["security.googleblog.com"]
        }

        # Attempt to load from JSON file
        try:
            json_path = os.path.join(os.path.dirname(__file__), 'exa_domains.json')
            with open(json_path, 'r') as f:
                data = json.load(f)
            self.domain_categories = data.get('domain_categories', default_domain_categories)
            self.vendor_map = data.get('vendor_map', default_vendor_map)
        except Exception:
            self.domain_categories = default_domain_categories
            self.vendor_map = default_vendor_map
    
    def _categorize_query(self, query: str) -> str:
        """Categorize query to select appropriate domains"""
        query_lower = query.lower()
        
        # Security-related keywords
        if any(word in query_lower for word in ['security', 'vulnerability', 'cve', 'threat', 'malware', 'hack', 'breach', 'attack', 'exploit', 'phishing']):
            return "cybersecurity"
        
        # Cloud/DevOps keywords
        elif any(word in query_lower for word in ['aws', 'azure', 'gcp', 'cloud', 'docker', 'kubernetes', 'devops', 'container', 'serverless']):
            return "cloud_devops"
        
        # Programming keywords
        elif any(word in query_lower for word in ['python', 'javascript', 'java', 'code', 'programming', 'development', 'api', 'framework', 'library']):
            return "programming"
        
        # Business/strategy keywords
        elif any(word in query_lower for word in ['business', 'strategy', 'market', 'startup', 'investment', 'trends', 'future']):
            return "business_tech"
        
        # Research keywords
        elif any(word in query_lower for word in ['research', 'study', 'paper', 'academic', 'analysis', 'methodology']):
            return "research_academic"
        
        # Default to general IT
        else:
            return "it_general"
    
    def _get_search_domains(self, category: str) -> List[str]:
        """Get domains for search based on category"""
        # Always include core IT domains
        base_domains = self.domain_categories["it_general"]
        category_domains = self.domain_categories.get(category, [])
        
        # Combine and deduplicate
        return list(set(base_domains + category_domains))

    def _vendor_domains(self, query_lower: str) -> List[str]:
        """Add vendor-specific domains when keywords are present in the query."""
        hits: List[str] = []
        for key, domains in self.vendor_map.items():
            if key in query_lower:
                hits.extend(domains)
        return list(set(hits))
    
    async def _enhance_query_with_ai(self, query: str, category: str) -> str:
        """Use AI to generate optimal search keywords"""
        try:
            api_key = st.secrets.get("OPENROUTER_API_KEY")
            if not api_key:
                return self._enhance_query_fallback(query, category)
            
            enhancement_prompt = f"""
            You are a search optimization expert. Given a user query and category, generate the most effective search keywords to find relevant, current information.

            User Query: "{query}"
            Category: {category}
            
            Rules:
            1. Keep the original query intact
            2. Add 3-5 highly relevant keywords that will improve search results
            3. Focus on technical terms, industry jargon, and specific concepts
            4. Consider current trends and terminology
            5. Return only the enhanced query, no explanation
            
            Enhanced Query:"""
            
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": st.session_state.get("selected_model", st.secrets.get("OPENROUTER_MODEL")),
                        "messages": [{"role": "user", "content": enhancement_prompt}],
                        "max_tokens": 100,
                        "temperature": 0.3
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    enhanced = result['choices'][0]['message']['content'].strip()
                    return enhanced if enhanced else self._enhance_query_fallback(query, category)
                    
        except Exception:
            pass
        
        return self._enhance_query_fallback(query, category)
    
    def _enhance_query_fallback(self, query: str, category: str) -> str:
        """Fallback keyword enhancement for when AI is unavailable"""
        enhancements = {
            "cybersecurity": f"{query} cybersecurity security threat vulnerability attack",
            "cloud_devops": f"{query} cloud devops infrastructure deployment automation",
            "programming": f"{query} programming development code software framework",
            "business_tech": f"{query} technology business industry trends innovation",
            "research_academic": f"{query} research study analysis methodology findings",
            "it_general": f"{query} IT technology infrastructure systems network"
        }
        return enhancements.get(category, f"{query} technology")
    
    def _should_use_ai_enhancement(self, query: str) -> bool:
        """Determine if query needs AI enhancement or can use fast fallback"""
        # Use AI for complex, ambiguous, or novel queries
        complex_indicators = [
            len(query.split()) > 6,  # Long queries
            '?' in query,  # Questions
            any(word in query.lower() for word in ['best', 'compare', 'difference', 'how', 'why', 'when', 'latest', 'new', 'emerging'])
        ]
        return any(complex_indicators)
    
    async def search_content(self, query: str, max_results: int = 3) -> List[Dict]:
        """Search for real-time information using Exa API with intelligent domain selection"""
        try:
            # Scope guard: skip Exa calls for non-IT topics
            if bool(st.secrets.get("ENFORCE_IT_SCOPE", True)):
                ql = query.lower().strip()
                # Load scope keywords from JSON with safe defaults
                non_it_patterns = []
                it_career_whitelist = []
                it_anchors = []
                try:
                    json_path = os.path.join(os.path.dirname(__file__), 'scope_keywords.json')
                    with open(json_path, 'r') as f:
                        data = json.load(f)
                    non_it_patterns = data.get('non_it_patterns', [])
                    it_career_whitelist = data.get('it_career_whitelist', [])
                    it_anchors = data.get('it_anchors', [])
                except Exception:
                    non_it_patterns = [
                        'relationship', 'dating', 'marriage', 'breakup', 'love',
                        'diet', 'nutrition', 'weight loss', 'fitness', 'workout',
                        'mental health', 'therapy', 'depression', 'anxiety',
                        'finance', 'stock market', 'stock trading', 'cryptocurrency', 'crypto trading', 'crypto wallet', 'investment', 'tax', 'budget',
                        'politics', 'election', 'public policy', 'foreign policy', 'economic policy',
                        'religion', 'spiritual', 'astrology', 'horoscope',
                        'parenting', 'pregnancy', 'baby', 'children',
                        'travel', 'vacation', 'tourism', 'itinerary',
                        'sports', 'football', 'soccer', 'basketball',
                        'cooking', 'recipe', 'food', 'restaurant',
                        'celebrity', 'gossip', 'entertainment', 'movie', 'music'
                    ]
                    it_career_whitelist = [
                        'resume', 'cv', 'interview', 'career', 'study path', 'roadmap',
                        'certification', 'certifications', 'soc analyst', 'sre career',
                        'devops upskilling', 'job market', 'portfolio', 'linkedin'
                    ]
                    it_anchors = [
                        'firewall', 'vpn', 'router', 'switch', 'ips', 'ids', 'siem', 'xdr', 'edr', 'soar', 'endpoint',
                        'malware', 'cve', 'vulnerability', 'exploit', 'threat', 'tls', 'ssl', 'certificate', 'certificates', 'ssh',
                        'linux', 'windows', 'active directory', 'group policy', 'gpo', 'powershell',
                        'azure', 'aws', 'gcp', 'kubernetes', 'docker', 'terraform', 'ansible', 'devops', 'sre',
                        'fortinet', 'cisco', 'palo alto', 'okta', 'cloudflare', 'nginx', 'istio', 'gitlab', 'github', 's3', 'ec2', 'vpc'
                    ]
                allow_career = bool(st.secrets.get("ALLOW_IT_CAREER_TOPICS", True))

                def matches_non_it_term(text: str) -> bool:
                    for term in non_it_patterns:
                        if ' ' in term:
                            if term in text:
                                return True
                        else:
                            if re.search(r'\b' + re.escape(term) + r'\b', text):
                                return True
                    return False

                matches_non_it = matches_non_it_term(ql)
                matches_it_career = any(p in ql for p in it_career_whitelist)
                matches_it_anchor = any(a in ql for a in it_anchors)

                if matches_non_it and not matches_it_anchor and not (allow_career and matches_it_career):
                    return []

            exa_api_key = st.secrets.get("EXA_API_KEY")
            if not exa_api_key:
                return []
            # Allow overriding max_results via secrets
            try:
                max_results = int(st.secrets.get("EXA_MAX_RESULTS", max_results))
            except Exception:
                pass
            
            # Categorize query and get appropriate domains
            category = self._categorize_query(query)
            domains = self._get_search_domains(category)
            vendor_boost = self._vendor_domains(query.lower())
            if vendor_boost:
                domains = list(set(domains + vendor_boost))
            
            # Use AI enhancement for complex queries, fallback for simple ones
            if self._should_use_ai_enhancement(query):
                enhanced_query = await self._enhance_query_with_ai(query, category)
            else:
                enhanced_query = self._enhance_query_fallback(query, category)
            
            # Determine start date: prefer rolling window via EXA_START_DAYS, else static EXA_START_DATE
            start_date = st.secrets.get("EXA_START_DATE", "2024-01-01")
            try:
                days = int(st.secrets.get("EXA_START_DAYS", 0))
                if days > 0:
                    start_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
            except Exception:
                pass
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.exa.ai/search",
                    headers={
                        "Authorization": f"Bearer {exa_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "query": enhanced_query,
                        "num_results": max_results,
                        "include_domains": domains,
                        "start_crawl_date": start_date
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        for item in data.get('results', []):
                            results.append({
                                "title": item.get('title', 'No title'),
                                "excerpt": item.get('text', 'No excerpt available')[:200] + "...",
                                "url": item.get('url', ''),
                                "source": "Exa Search"
                            })
                        # If nothing found with domain filters, retry without restrictions
                        if not results:
                            async with session.post(
                                "https://api.exa.ai/search",
                                headers={
                                    "Authorization": f"Bearer {exa_api_key}",
                                    "Content-Type": "application/json"
                                },
                                json={
                                    "query": enhanced_query,
                                    "num_results": max_results,
                                    "start_crawl_date": start_date
                                }
                            ) as fallback_resp:
                                if fallback_resp.status == 200:
                                    data2 = await fallback_resp.json()
                                    for item in data2.get('results', []):
                                        results.append({
                                            "title": item.get('title', 'No title'),
                                            "excerpt": item.get('text', 'No excerpt available')[:200] + "...",
                                            "url": item.get('url', ''),
                                            "source": "Exa Search"
                                        })
                        return results
                    else:
                        st.error(f"Exa API error: {response.status}")
                        return []
        except Exception as e:
            st.error(f"Exa search error: {str(e)}")
            # Fallback links for common security topics
            if any(word in query.lower() for word in ['cve', 'vulnerability', 'security', 'exploit']):
                return [
                    {
                        "title": "NIST National Vulnerability Database",
                        "excerpt": "Search the NVD for the latest CVE information and vulnerability details.",
                        "url": "https://nvd.nist.gov/vuln/search",
                        "source": "NIST NVD"
                    }
                ]
            return []
