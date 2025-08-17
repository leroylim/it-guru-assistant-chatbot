"""
Security utilities for the IT-Guru chatbot.
Provides sanitization, URL validation, and prompt-injection heuristics.
"""
from __future__ import annotations
import re
import html
from urllib.parse import urlparse
from typing import List, Dict, Tuple, Set

# Default allowlist of trusted domains
DEFAULT_DOMAIN_ALLOWLIST: Set[str] = {
    "learn.microsoft.com",
    "microsoft.com",
    "docs.aws.amazon.com",
    "aws.amazon.com",
    "azure.microsoft.com",
    "cloud.google.com",
    "kubernetes.io",
    "iana.org",
    "developer.mozilla.org",
}


def sanitize_text(text: str) -> str:
    """Escape HTML to prevent injection in rendered content titles."""
    return html.escape(text or "")


def is_url_allowed(url: str, allowlist: Set[str] | None = None) -> bool:
    """URL filtering disabled: always allow."""
    return True


def build_sources_markdown(results: List[Dict]) -> str:
    """Build a Markdown list of sources from search results.
    Titles are escaped. URL filtering is disabled.
    """
    if not results:
        return ""
    lines = ["\n", "**📚 Sources:**"]
    for i, r in enumerate(results, 1):
        url = r.get("url", "")
        title = sanitize_text(r.get("title", "Untitled"))
        source = sanitize_text(r.get("source", ""))
        suffix = f" ({source})" if source else ""
        # Show hyperlink followed by raw URL for easy verification/copying
        lines.append(f"{i}. [{title}]({url}){suffix} — {url}")
    return "\n".join(lines)


# Simple prompt-injection heuristics
INJECTION_PATTERNS = [
    r"(?i)ignore (the )?(previous|above) (instructions|rules)",
    r"(?i)disregard (the )?(system|previous) (prompt|instructions)",
    r"(?i)reveal (the )?(system|hidden) (prompt|instructions)",
    r"(?i)print (environment|api|secret|token)",
    r"(?i)exfiltrat(e|ion)|leak (data|key|secret)",
    r"(?i)perform actions outside|execute code|run shell|launch process",
    r"(?i)send (all|your) data to",
]


def detect_prompt_injection(text: str) -> Tuple[bool, List[str]]:
    """Detect likely prompt-injection attempts using regex heuristics."""
    if not text:
        return False, []
    hits = []
    for pat in INJECTION_PATTERNS:
        if re.search(pat, text):
            hits.append(pat)
    return (len(hits) > 0), hits
