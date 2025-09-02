from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import requests
from bs4 import BeautifulSoup
from .search_types import SearchResult, SearchEngineConfig, SearchResponse
import markdownify
from readabilipy import simple_json
from readability import Document
import json

class BaseSearchEngine(ABC):
    """Base class for all search engines."""
    
    def __init__(self, config: SearchEngineConfig):
        self.config = config
        self.session = requests.Session()
        if config.headers:
            self.session.headers.update(config.headers)
    
    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> SearchResponse:
        """Perform a search query."""
    
        pass
    
    def _make_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Make an HTTP request with error handling."""
        try:
            response = self.session.get(
                url=url, 
                headers=self.config.headers,
                params=params,
                timeout=self.config.timeout,
                proxies=self.config.proxy
            )
            response.encoding = "utf-8"
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
    
    def _parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content."""
        return BeautifulSoup(html, 'html.parser')
    
    def _extract_text(self, element: Any) -> str:
        """Extract text from a BeautifulSoup element."""
        return element.get_text(strip=True) if element else ""
    
    def _clean_url(self, url: str) -> str:
        """Clean and normalize URLs."""
        return url.strip()
    
    def _create_result(self, title: str, url: str, content: str) -> SearchResult:
        """Create a SearchResult object."""
        return SearchResult(
            title=title.strip(),
            url=self._clean_url(url),
            content=content.strip()
        )
    
    def get_web_content(self, url: str) -> str:
        """Get the web content of a given URL."""
        from .util import get_web_content
        content, _ = get_web_content(url)
        return content