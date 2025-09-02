from dataclasses import dataclass
from typing import Optional, Dict, Any, List

@dataclass
class SearchResult:
    """Search result from a search engine."""
    title: str
    url: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class SearchConfig:
    """Configuration for the search engine."""
    provider: str
    max_results: int = 10
    timeout: int = 10
    proxy: Optional[str] = None

@dataclass
class SearchEngineConfig:
    """Configuration for specific search engines."""
    base_url: str
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, str]] = None
    timeout: Optional[int] = None
    proxy: Optional[str] = None

@dataclass
class SearchResponse:
    """Response from a search operation."""
    results: List[SearchResult]
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None 