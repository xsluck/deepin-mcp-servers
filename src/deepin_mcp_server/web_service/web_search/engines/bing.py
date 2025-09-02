from typing import List, Dict, Any, Optional
from ..base import BaseSearchEngine
from ..search_types import SearchResult, SearchResponse, SearchEngineConfig

class BingSearchEngine(BaseSearchEngine):
    """Bing Search Engine implementation."""
    
    def __init__(self, config: Optional[SearchEngineConfig] = None):
        super().__init__(config or SearchEngineConfig(
            base_url="https://www.bing.com/search",
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            }
        ))
    
    def search(self, query: str, max_results: int = 10) -> SearchResponse:
        """Perform a Bing search."""
        params = {
            "q": query,
            "count": max_results
        }
        
        html = self._make_request(self.config.base_url, params)
        if isinstance(html, SearchResponse):
            return html
            
        soup = self._parse_html(html)
        results = []
        # Find search results
        for result in soup.select("li.b_algo"):
            title_elem = result.select_one("h2")
            link_elem = result.select_one("h2 a")
            content_elem = result.select_one("div.b_caption p")
            
            if title_elem and link_elem:
                title = self._extract_text(title_elem)
                url = link_elem.get("href", "")
                content = self._extract_text(content_elem)
                
                if not url.startswith("http"):
                    continue
                    
                results.append(self._create_result(title, url, content))
                
                if len(results) >= max_results:
                    break
        
        return SearchResponse(
            results=results,
            metadata={"total_results": len(results)}
        ) 