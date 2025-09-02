import logging
import json
from .web_search.search import WebSearch
from .web_search.search_types import SearchConfig, SearchResponse
from .web_search.util import get_web_content

# Configure logging
logger = logging.getLogger(__name__)

def _web_search(query: str) -> str:
    if not query:
        return ""

    try:
        # 备用搜索引擎
        providers = ["baidu", "sogou", "bing"] # sogou google ...
        for provider in providers:
            logger.info(f"使用搜索引擎: {provider}")
            config = SearchConfig(
                provider=provider,
                max_results=10,
                timeout=10,
                proxy=None
            )
            searcher = WebSearch(config)
            response = searcher.search(query)
            if (len(response.results) > 0):
                break
        
        result_json = []
        for result in response.results:
            content, _ = get_web_content(result.url)
            result_json.append({
                "title": result.title,
                "url": result.url,
                "content": content
            })
        return json.dumps(result_json, ensure_ascii=False)
    except Exception as e:
        logger.error(f"搜索过程中发生异常: {e}", exc_info=True)
        return f"搜索失败: {str(e)}"

def _fetch_web_content(url: str) -> str:
    if not url:
        return ""

    try:
        content, _ = get_web_content(url)
        return content
    except Exception as e:
        logger.error(f"获取网页内容失败: {e}", exc_info=True)
        return f"获取网页内容失败: {str(e)}"