from typing import List, Dict, Any, Optional
from ..base import BaseSearchEngine
from ..search_types import SearchResult, SearchResponse, SearchEngineConfig
import re
from urllib.parse import quote
from ..util import get_web_content
from bs4 import BeautifulSoup
import requests

class SogouSearchEngine(BaseSearchEngine):
    """Sogou Search Engine implementation."""
    
    def __init__(self, config: Optional[SearchEngineConfig] = None):
        super().__init__(config or SearchEngineConfig(
            base_url="https://www.sogou.com/web",
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        ))
        self.host_url = "https://www.sogou.com"
    
    def search(self, query: str, max_results: int = 10) -> SearchResponse:
        """Perform a Baidu search."""
        params = {
            "query": query
        }
        
        html = self._make_request(self.config.base_url, params)

        if isinstance(html, SearchResponse):
            return html
        
        soup = self._parse_html(html)
        results = []
        
        for result in soup.select('.vrwrap, .rb'):
            title_elem = result.select_one("h3, .pt")
            link_elem = result.select_one("a[href]")

            content_elem = None
            for selector in [".str-pd, .ft, .str-text-info, .sp-text, .text-layout"]:
                content_elem = result.select_one(selector)
                if content_elem:
                    break
            
            if title_elem and link_elem and content_elem:
                title = title_elem.get_text(strip=True)
                url = link_elem['href']
                content = content_elem.get_text(strip=True)

                # 处理Sogou重定向
                if url.startswith('/link?url='):
                    response = requests.get(
                        self.host_url + url, 
                        headers=self.config.headers,
                        timeout=10,
                        proxies=None
                    )
                    refer_html = response.text

                    soup = BeautifulSoup(refer_html, 'html.parser')
                    refer_url = None
                    # 1. 检查 JavaScript 跳转 (window.location.replace)
                    script = soup.find('script')
                    if script and 'window.location.replace' in script.text:
                        start = script.text.find('("') + 2
                        end = script.text.find('")')
                        refer_url = script.text[start:end]
                    # 2. 如果 JavaScript 未生效，检查 <meta> 跳转
                    if not refer_url:
                        meta = soup.find('meta', attrs={'http-equiv': 'refresh'})
                        if meta:
                            content = meta.get('content', '')
                            if 'url=' in content.lower():
                                refer_url = content.split('url=')[1].strip("'\"")
                    
                    if refer_url:
                        url = refer_url
            
                # 为有效结果创建SearchResult对象
                if title and url and content:
                    results.append(self._create_result(title, url, content))
                
                # 达到最大结果数量时停止
                if len(results) >= max_results:
                    break
        
        # 如果没有找到任何结果
        if not results:
            return SearchResponse(
                results=[],
                metadata={"total_results": 0}
            )
        
        return SearchResponse(
            results=results,
            metadata={"total_results": len(results)}
        )