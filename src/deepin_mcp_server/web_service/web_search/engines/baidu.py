from typing import List, Dict, Any, Optional
from ..base import BaseSearchEngine
from ..search_types import SearchResult, SearchResponse, SearchEngineConfig
import re
from urllib.parse import quote

class BaiduSearchEngine(BaseSearchEngine):
    """Baidu Search Engine implementation."""
    
    def __init__(self, config: Optional[SearchEngineConfig] = None):
        super().__init__(config or SearchEngineConfig(
            base_url="https://www.baidu.com/s",
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Content-Type": "text/html; charset=utf-8",
                "User-Agent": 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                "Referer": "https://www.baidu.com/",
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
            }
        ))
        self.host_url = "https://www.baidu.com"
    
    def search(self, query: str, max_results: int = 10) -> SearchResponse:
        """Perform a Baidu search."""
        params = {
            "wd": query,
            "ie": "utf-8",
            "tn": "baidu",
            "rn": str(max_results)
        }
        
        html = self._make_request(self.config.base_url, params)

        if isinstance(html, SearchResponse):
            return html
        
        soup = self._parse_html(html)
        results = []
        
        # Find search results in div content_left
        div_contents = soup.find("div", id="content_left")
        if not div_contents:
            return SearchResponse(
                results=[],
                error="No search results found"
            )
            
        for div in div_contents.children:
            if not hasattr(div, 'get'):
                continue
                
            class_list = div.get("class", [])
            if not class_list or "c-container" not in class_list:
                continue
                
            title = ""
            url = ""
            content = ""
            
            # 提取标题和URL
            if div.h3 and div.h3.a:
                title = self._extract_text(div.h3)
                url = div.h3.a.get("href", "")
            else:
                continue
                
            # 提取内容摘要
            abstract_div = div.find("div", class_="c-abstract")
            if abstract_div:
                content = self._extract_text(abstract_div)
            elif div.div:
                content = self._extract_text(div.div)
            else:
                # 尝试从div的文本中提取摘要
                all_text = div.text.strip()
                if title in all_text:
                    content = all_text.replace(title, "", 1).strip()
            
            # 如果URL是百度重定向链接，需要清洗
            if url.startswith("/"):
                url = self.host_url + url
            
            # 为有效结果创建SearchResult对象
            if title and url:
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
    
    def _extract_real_url(self, url: str) -> str:
        """如果是百度重定向链接，提取真实URL"""
        if "/s?word=" in url:
            try:
                match = re.search(r'url=([^&]+)', url)
                if match:
                    from urllib.parse import unquote
                    return unquote(match.group(1))
            except:
                pass
        return url 