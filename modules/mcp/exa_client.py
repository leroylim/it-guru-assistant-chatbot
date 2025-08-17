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
        # Load domain categories and vendor map from JSON only; no hardcoded fallbacks
        try:
            json_path = os.path.join(os.path.dirname(__file__), 'exa_domains.json')
            with open(json_path, 'r') as f:
                data = json.load(f)
            self.domain_categories = data.get('domain_categories', {})
            self.vendor_map = data.get('vendor_map', {})
        except Exception as e:
            st.warning(f"Failed to load exa_domains.json: {e}. Proceeding with empty domain/vendor maps.")
            self.domain_categories = {}
            self.vendor_map = {}
    
    def _categorize_query(self, query: str) -> str:
        """Categorize query to select appropriate domains"""
        query_lower = query.lower()
        
        # SASE / SSE / Zero Trust Access
        if any(word in query_lower for word in [
            'sase', 'sse', 'zero trust', 'ztna', 'casb', 'swg', 'prisma access', 'zscaler', 'netskope'
        ]):
            return "sase_sse"

        # Backup and Disaster Recovery
        if any(word in query_lower for word in [
            'backup', 'backups', 'dr', 'disaster recovery', 'rpo', 'rto', 'snapshot', 'snapshots', 'veeam', 'rubrik', 'cohesity'
        ]):
            return "backup_dr"

        # Storage infrastructure (NAS/SAN/array)
        if any(word in query_lower for word in [
            'storage', 'nas', 'san', 'iscsi', 'nfs', 'smb', 'raid',
            'dell emc', 'powerscale', 'powerstore', 'isilon',
            'hpe nimble', 'hpe 3par', 'hpe alletra', 'nimble', '3par', 'alletra',
            'synology', 'qnap', 'netapp', 'pure storage', 'purestorage'
        ]):
            return "storage_infra"

        # Identity & Access Management
        if any(word in query_lower for word in [
            'iam', 'identity', 'saml', 'oauth', 'oidc', 'entra', 'azure ad', 'active directory', 'okta', 'auth0', 'duo', 'mfa', 'sso', 'single sign-on',
            'ping identity', 'onelogin'
        ]):
            return "identity_access"

        # Endpoint security / EDR / XDR
        if any(word in query_lower for word in [
            'edr', 'xdr', 'antivirus', 'endpoint', 'defender for endpoint', 'crowdstrike', 'sentinelone', 'cylance', 'trellix'
        ]):
            return "endpoint_security"

        # Email security / M365 security
        if any(word in query_lower for word in [
            'email security', 'phishing protection', 'mimecast', 'proofpoint', 'exchange online protection', 'eop', 'microsoft 365 defender', 'abnormal security'
        ]):
            return "email_security"

        # Code security / SCA / SAST / secrets
        if any(word in query_lower for word in [
            'sast', 'sca', 'snyk', 'veracode', 'gitguardian', 'supply chain security', 'dependency vulnerability', 'github advisories'
        ]):
            return "code_security"

        # Observability & monitoring
        if any(word in query_lower for word in [
            'observability', 'monitoring', 'apm', 'metrics', 'tracing', 'logs', 'datadog', 'new relic', 'grafana', 'prometheus', 'splunk', 'elastic'
        ]):
            return "observability_monitoring"

        # Networking & infrastructure vendors
        if any(word in query_lower for word in [
            'router', 'switch', 'bgp', 'ospf', 'sd-wan', 'firewall', 'vpn', 'cisco', 'juniper', 'aruba', 'mikrotik', 'f5', 'citrix', 'load balancer',
            'meraki', 'extreme', 'arista', 'ubiquiti', 'unifi', 'netgear', 'teltonika'
        ]):
            return "networking_infra"

        # Containers & Kubernetes / service mesh
        if any(word in query_lower for word in [
            'kubernetes', 'k8s', 'pod', 'cluster', 'ingress', 'docker', 'container', 'istio', 'envoy', 'helm', 'openshift'
        ]):
            return "containers_k8s"

        # Linux/Unix topics
        if any(word in query_lower for word in [
            'linux', 'ubuntu', 'debian', 'red hat', 'rhel', 'kernel', 'systemd', 'bash'
        ]):
            return "linux_unix"

        # Windows enterprise topics
        if any(word in query_lower for word in [
            'windows server', 'gpo', 'group policy', 'powershell', 'active directory', 'adcs', 'wsus'
        ]):
            return "windows_enterprise"

        # Data platforms / databases / caching
        if any(word in query_lower for word in [
            'postgres', 'postgresql', 'mysql', 'mariadb', 'mongodb', 'redis', 'clickhouse', 'database', 'rdbms'
        ]):
            return "data_platforms"

        # IaC and cloud provisioning
        if any(word in query_lower for word in [
            'terraform', 'pulumi', 'cloudformation', 'ansible', 'iac', 'infrastructure as code'
        ]):
            return "cloud_iac"

        # General cybersecurity
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
        base_domains = self.domain_categories.get("it_general", [])
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
                except Exception as e:
                    st.warning(f"Failed to load scope keywords JSON: {e}. Proceeding with empty keyword sets.")
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
            # Allow overriding max_results via secrets (prefer EXA_NUM_RESULTS, fallback to EXA_MAX_RESULTS)
            try:
                max_results = int(st.secrets.get("EXA_NUM_RESULTS", st.secrets.get("EXA_MAX_RESULTS", max_results)))
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
