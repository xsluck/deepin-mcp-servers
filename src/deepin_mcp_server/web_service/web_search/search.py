from typing import List, Optional, Dict, Any
from .search_types import SearchResult, SearchConfig, SearchResponse
from .engines.google import GoogleSearchEngine
from .engines.duckduckgo import DuckDuckGoSearchEngine
from .engines.bing import BingSearchEngine
from .engines.baidu import BaiduSearchEngine
from .engines.sogou import SogouSearchEngine

class WebSearch:
    """Main search class that manages different search engines."""
    
    def __init__(self, config: SearchConfig):
        self.config = config
        self.engine = self._get_engine(config.provider)
    
    def _get_engine(self, provider: str):
        """Get the appropriate search engine based on provider."""
        engines = {
            "google": GoogleSearchEngine,
            "duckduckgo": DuckDuckGoSearchEngine,
            "bing": BingSearchEngine,
            "baidu": BaiduSearchEngine,
            "sogou": SogouSearchEngine
        }
        
        engine_class = engines.get(provider.lower())
        if not engine_class:
            raise ValueError(f"Unsupported search provider: {provider}")
            
        return engine_class()
    
    def search(self, query: str) -> SearchResponse:
        """Perform a search using the configured engine."""
        return self.engine.search(query, self.config.max_results)
    
    def set_provider(self, provider: str) -> None:
        """Change the search provider."""
        self.config.provider = provider
        self.engine = self._get_engine(provider)
    
    def set_max_results(self, max_results: int) -> None:
        """Change the maximum number of results."""
        self.config.max_results = max_results 
    
    def get_web_content(self, url: str) -> str:
        """Get the web content of a given URL."""
        return self.engine.get_web_content(url)