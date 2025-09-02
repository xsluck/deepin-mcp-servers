from typing import List, Dict, Any, Optional
from ..base import BaseSearchEngine
from ..search_types import SearchResult, SearchResponse, SearchEngineConfig

class DuckDuckGoSearchEngine(BaseSearchEngine):
    """DuckDuckGo Search Engine implementation."""
    
    def __init__(self, config: Optional[SearchEngineConfig] = None):
        super().__init__(config or SearchEngineConfig(
            base_url="https://html.duckduckgo.com/html/",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
        ))
    
    def search(self, query: str, max_results: int = 10) -> SearchResponse:
        """Perform a DuckDuckGo search."""
        params = {
            "q": query,
        }
        
        html = self._make_request(self.config.base_url, params)
        if isinstance(html, SearchResponse):
            return html
            
        soup = self._parse_html(html)
        results = []
        
        # Find search results
        for result in soup.select("div.result"):
            title_elem = result.select_one("h2")
            link_elem = result.select_one("a.result__a")
            content_elem = result.select_one("a.result__snippet")
            
            if title_elem and link_elem:
                title = self._extract_text(title_elem)
                url = link_elem.get("href", "")
                content = self._extract_text(content_elem)
                
                if url.startswith("/l/?uddg="):
                    url = url[8:].split("&")[0]
                    url = url.replace("%3A", ":").replace("%2F", "/")
                
                if not url.startswith("http"):
                    continue
                    
                results.append(self._create_result(title, url, content))
                
                if len(results) >= max_results:
                    break
        
        return SearchResponse(
            results=results,
            metadata={"total_results": len(results)}
        ) 